
import sys
import os
import MetaTrader5 as mt5
from datetime import datetime
import time
import pandas as pd

# Fix Windows console encoding for emojis
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

sys.path.append(os.getcwd())
from titan_system.core.execution import MT5Execution
from config.settings import settings
from titan_system.integrations.google_sheets import TitanSheets

def analyze_position(pos, current_price, atr):
    """Analyze if a position needs adjustment"""
    
    recommendations = []
    
    # 0. CRITICAL: Check if SL/TP are missing (user forgot to set them)
    if pos['sl'] == 0 or pos['tp'] == 0:
        # Calculate proper SL/TP based on ATR
        if pos['type'] == 0:  # Buy
            suggested_sl = pos['price_open'] - (atr * 1.5)
            suggested_tp = pos['price_open'] + (atr * 2.5)
        else:  # Sell
            suggested_sl = pos['price_open'] + (atr * 1.5)
            suggested_tp = pos['price_open'] - (atr * 2.5)
        
        recommendations.append({
            "action": "SET_SLTP",
            "reason": "⚠️ MISSING SL/TP - Auto-setting based on ATR",
            "sl": suggested_sl,
            "tp": suggested_tp
        })
        
        # Return immediately to set SL/TP first
        return {
            "pnl": 0,
            "pip_move": 0,
            "atr": atr,
            "recommendations": recommendations
        }
    
    # Calculate current P&L
    if pos['type'] == 0:  # Buy
        pnl = (current_price - pos['price_open']) * pos['volume'] * 100
        pip_move = current_price - pos['price_open']
    else:  # Sell
        pnl = (pos['price_open'] - current_price) * pos['volume'] * 100
        pip_move = pos['price_open'] - current_price
    
    # Distance to SL/TP
    sl_distance = abs(current_price - pos['sl']) if pos['sl'] > 0 else None
    tp_distance = abs(pos['tp'] - current_price) if pos['tp'] > 0 else None
    
    # Calculate Equity Percentage of this position (Risk Context)
    # Assuming standard contract size 100k, approx value
    notional = pos['volume'] * 100000 
    # Need equity passed in, or approx 10k base
    # For now, treat > 2.0 lots as "Whale" for this account size
    is_whale = pos['volume'] >= 2.0
    
    # 1. SNIPER PROTECT (Velocity Focus - New!)
    # Logic: If trade hits 0.5 ATR profit instantly (within 10 mins), lock it in.
    # This prevents the "instantly profitable, then destroyed" scenario.
    trade_start_time = pd.to_datetime(pos['time_update'], unit='s') if 'time_update' in pos else pd.to_datetime(pos['time'], unit='s')
    # fallback to current time if time is missing
    now = datetime.now()
    minutes_in_trade = (now.timestamp() - pos['time_update']) / 60 if 'time_update' in pos else 5 # assume 5 if unknown
    
    velocity = pip_move / max(minutes_in_trade, 1) # pips per minute
    
    # Sniper Trigger: Hits 0.5 ATR profit with high velocity OR 0.8 ATR generally
    if pnl > 0 and (pip_move > (atr * 0.8) or (pip_move > (atr * 0.4) and velocity > (atr * 0.1))):
        is_secured = False
        if pos['type'] == 0: # Buy
            if pos['sl'] >= pos['price_open']: is_secured = True
        else: # Sell
            if pos['sl'] <= pos['price_open'] and pos['sl'] > 0: is_secured = True
            
        if not is_secured:
            recommendations.append({
                "action": "MOVE_SL_BE", 
                "reason": f"🎯 SNIPER PROTECT: Velocity ({velocity:.5f}/min) too high to risk loss. Locking BE."
            })

    # 2. WHALE PROTECTION (Large Positions)
    # If it's a huge trade, DON'T partial close. LET IT RUN but TRAIL TIGHT.
    if is_whale and pnl > 0 and pip_move > (atr * 1.0):
        # Calculate Tight Trail (0.5 ATR)
        if pos['type'] == 0: # Buy
            new_sl = current_price - (atr * 0.5)
            if new_sl > pos['sl']: # Only move up
                recommendations.append({
                    "action": "TRAIL_SL", 
                    "reason": "🐋 WHALE PROTECT: Validating huge winner, trailing tight (0.5 ATR)",
                    "sl": new_sl
                })
        else: # Sell
            new_sl = current_price + (atr * 0.5)
            if pos['sl'] == 0 or new_sl < pos['sl']: # Only move down
                recommendations.append({
                    "action": "TRAIL_SL", 
                    "reason": "🐋 WHALE PROTECT: Validating huge winner, trailing tight (0.5 ATR)",
                    "sl": new_sl
                })

    # 3. Standard Account: Bank 50% Profit at 1.5 ATR (Only if NOT a Whale)
    elif not is_whale and pnl > 0 and pip_move > (atr * 1.5):
        # Prevent partials on tiny positions
        if pos['volume'] >= 0.02: 
            recommendations.append({
                "action": "TAKE_PARTIAL", 
                "reason": f"Hit 1.5 ATR target (+${pnl:.2f}), banking 50%",
                "volume": pos['volume']
            })

    # 4. Check if SL is too tight (might get stopped out on noise)
    if not is_whale and sl_distance and sl_distance < (atr * 0.8) and pnl < 0: 
        recommendations.append({"action": "WIDEN_SL", "reason": f"SL too tight ({sl_distance:.5f} < {atr*0.8:.5f} ATR)"})
    
    # 3. Check if trade is deep in loss
    if pnl < 0 and abs(pnl) > (pos['volume'] * 100 * atr):
        recommendations.append({"action": "CLOSE", "reason": f"Deep loss: ${pnl:.2f}"})
    
    # 4. Check if profit target is too far (let's not be greedy)
    if tp_distance and tp_distance > (atr * 4):
        recommendations.append({"action": "TIGHTEN_TP", "reason": "TP too far, lock in profits"})
    
    # 5. SCALING OPPORTUNITY: If trade is profitable AND trend still strong, ADD to position
    if pnl > 0 and pip_move > (atr * 1.0):  # Only if clearly winning
        # Fetch recent M5 candles to check if trend is still strong
        rates = mt5.copy_rates_from_pos(pos['symbol'], mt5.TIMEFRAME_M5, 0, 50)
        if rates is not None and len(rates) >= 30:
            df = pd.DataFrame(rates)
            # Calculate EMAs
            df['ema_fast'] = df['close'].ewm(span=9).mean()
            df['ema_slow'] = df['close'].ewm(span=21).mean()
            
            curr_fast = df['ema_fast'].iloc[-1]
            curr_slow = df['ema_slow'].iloc[-1]
            
            # Check if trend still supports our direction
            if pos['type'] == 0:  # We're long
                if curr_fast > curr_slow:  # Uptrend still strong
                    recommendations.append({
                        "action": "SCALE_UP",
                        "reason": f"Winning trade (+${pnl:.2f}) & trend still bullish - ADD MORE",
                        "add_volume": pos['volume'] * 0.5  # Add 50% of current position
                    })
            else:  # We're short
                if curr_fast < curr_slow:  # Downtrend still strong
                    recommendations.append({
                        "action": "SCALE_UP",
                        "reason": f"Winning trade (+${pnl:.2f}) & trend still bearish - ADD MORE",
                        "add_volume": pos['volume'] * 0.5
                    })
    
    return {
        "pnl": pnl,
        "pip_move": pip_move,
        "atr": atr,
        "recommendations": recommendations
    }

def fix_position(pos, recommendation, execution):
    """Execute the recommended fix"""
    
    symbol = pos['symbol']
    ticket = pos['ticket']
    
    # Get symbol info for filling mode
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"   ❌ Cannot get symbol info for {symbol}")
        return False
    
    # Determine filling mode
    filling_modes = symbol_info.filling_mode
    if filling_modes & 2:  # IOC
        filling_mode = mt5.ORDER_FILLING_IOC
    elif filling_modes & 1:  # FOK
        filling_mode = mt5.ORDER_FILLING_FOK
    else:
        filling_mode = mt5.ORDER_FILLING_RETURN
    
    try:
        if recommendation['action'] == "CLOSE":
            # Close the position
            order_type = mt5.ORDER_TYPE_SELL if pos['type'] == 0 else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(symbol)
            price = tick.bid if pos['type'] == 0 else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos['volume'],
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Auto-Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,  # Use detected filling mode
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   ✅ CLOSED position {ticket}")
                return True
            else:
                print(f"   ❌ Failed to close: {result.comment if result else 'No result'}")
                return False
        
        elif recommendation['action'] == "MOVE_SL_BE":
            # Modify SL to breakeven
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": pos['price_open'],
                "tp": pos['tp'],
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   ✅ Moved SL to breakeven for {ticket}")
                return True
            else:
                print(f"   ❌ Failed to modify SL: {result.comment if result else 'No result'}")
                return False
        
        elif recommendation['action'] == "SET_SLTP":
            # Set missing SL/TP
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": recommendation.get('sl', pos['sl']),
                "tp": recommendation.get('tp', pos['tp']),
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   ✅ Set SL/TP for {ticket}")
                return True
            else:
                print(f"   ❌ Failed to set SL/TP: {result.comment if result else 'No result'}")
                return False
        
        elif recommendation['action'] == "SCALE_UP":
            # Add to winning position
            add_volume = recommendation.get('add_volume', 0.01)
            
            # Normalize volume to meet symbol requirements
            add_volume = max(symbol_info.volume_min, add_volume)
            add_volume = round(add_volume / symbol_info.volume_step) * symbol_info.volume_step
            add_volume = round(add_volume, 2)
            
            # Same direction as existing position
            order_type = mt5.ORDER_TYPE_BUY if pos['type'] == 0 else mt5.ORDER_TYPE_SELL
            tick = mt5.symbol_info_tick(symbol)
            price = tick.ask if pos['type'] == 0 else tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": add_volume,
                "type": order_type,
                "price": price,
                "sl": pos['sl'],  # Use same SL as original
                "tp": pos['tp'],  # Use same TP
                "deviation": 20,
                "magic": 234000,
                "comment": "Scale-Up",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   ✅ SCALED UP: Added {add_volume} lots to position")
                return True
            else:
                print(f"   ❌ Failed to scale: {result.comment if result else 'No result'}")
                return False
                
        elif recommendation['action'] == "TAKE_PARTIAL":
            # Close 50% of position
            current_vol = recommendation.get('volume', 0.01)
            close_vol = current_vol * 0.5
            
            # Normalize
            close_vol = max(symbol_info.volume_min, close_vol)
            close_vol = round(close_vol / symbol_info.volume_step) * symbol_info.volume_step
            close_vol = round(close_vol, 2)
            
            if close_vol == 0: return False
            
            # Execution
            order_type = mt5.ORDER_TYPE_SELL if pos['type'] == 0 else mt5.ORDER_TYPE_BUY
            tick = mt5.symbol_info_tick(symbol)
            price = tick.bid if pos['type'] == 0 else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": close_vol,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": 234000,
                "comment": "Partial Close (1.5 ATR)",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": filling_mode,
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   💰 PARTIAL TAKE: Closed {close_vol} lots (Banked Profit)")
                return True
            else:
                print(f"   ❌ Failed to partial close: {result.comment if result else 'No result'}")
                return False
                
        elif recommendation['action'] == "TRAIL_SL":
            # Trail SL (Whale or Normal)
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": symbol,
                "position": ticket,
                "sl": recommendation['sl'],
                "tp": pos['tp'], # Keep TP same
            }
            
            result = mt5.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"   🛡️  TRAILED SL to {recommendation['sl']:.5f}")
                return True
            else:
                print(f"   ❌ Failed to trail: {result.comment if result else 'No result'}")
                return False
                
    except Exception as e:
        print(f"   ⚠️ Error executing fix: {e}")
        return False

def calculate_exposure(positions, account_equity):
    """Calculates exposure per currency."""
    exposure = {}
    
    for pos in positions:
        symbol = pos['symbol']
        # Simplified Logic for Dashboard Display
        base_currency = symbol[:3]
        if "XAU" in symbol or "GOLD" in symbol: base_currency = "GLD"
        if "BTC" in symbol: base_currency = "BTC"
        if "ETH" in symbol: base_currency = "ETH"
        if "US30" in symbol or "NAS" in symbol or "SPX" in symbol: base_currency = "USD"
        
        volume = pos['volume']
        
        # Add to Net Exposure
        if base_currency not in exposure: exposure[base_currency] = 0.0
        exposure[base_currency] += volume
        
    # Format for Sheet
    result = {}
    for curr, vol in exposure.items():
        # Approx Value (Standard Lot = 100k units, very rough)
        notional = vol * 100000 
        pct_equity = (notional / account_equity) * 100 if account_equity > 0 else 0
        
        status = "OK"
        if pct_equity > 500: status = "HIGH LEVERAGE"
        if pct_equity > 1000: status = "CRITICAL"
        
        result[curr] = {
            "volume": vol,
            "value": notional,
            "equity_pct": pct_equity,
            "status": status
        }
        
    return result

def monitor_trades():
    """Main monitoring loop"""
    
    execution = MT5Execution(settings)
    sheets = TitanSheets()
    
    if not execution.connect():
        print("❌ Failed to connect to MT5")
        return
    
    print("👁️  TRADE MONITOR ACTIVE")
    print("Watching all positions and providing real-time analysis...\n")
    
    while True:
        try:
            positions = execution.get_positions()
            account = execution.get_account_info()
            equity = account.get('equity', 10000)
            
            # --- DASHBOARD UPDATES ---
            if sheets.enabled:
                # 1. Update Exposure Tab
                exposure_data = calculate_exposure(positions, equity)
                sheets.update_exposure(exposure_data)
                
                # 2. Update Dashboard Tab (Alive Status)
                sheets.update_dashboard({
                    "running": True, 
                    "equity": equity,
                    "balance": account.get('balance', 0),
                    "profit_today": account.get('profit', 0)
                })
            # -------------------------
            
            if not positions:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No open positions")
            else:
                print(f"\n{'='*80}")
                print(f"📊 PORTFOLIO SNAPSHOT - {datetime.now().strftime('%H:%M:%S')}")
                print(f"{'='*80}")
                
                for pos in positions:
                    symbol = pos['symbol']
                    
                    # Get current market data
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        continue
                    
                    current_price = tick.bid if pos['type'] == 0 else tick.ask
                    
                    # Calculate ATR
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 20)
                    if rates is not None and len(rates) >= 14:
                        df = pd.DataFrame(rates)
                        atr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
                    else:
                        atr = 0.001
                    
                    # Analyze
                    analysis = analyze_position(pos, current_price, atr)
                    
                    # Determine if it's a bot trade or user trade
                    is_bot_trade = 'Scalp' in pos.get('comment', '') or pos.get('magic', 0) == 234000
                    trader = "🤖 BOT" if is_bot_trade else "👤 YOU"
                    
                    # Print summary
                    type_str = "BUY" if pos['type'] == 0 else "SELL"
                    print(f"\n{trader} | {symbol} {type_str} | Vol: {pos['volume']}")
                    print(f"   Entry: {pos['price_open']:.5f} | Current: {current_price:.5f}")
                    print(f"   P&L: ${analysis['pnl']:.2f} | Pips: {analysis['pip_move']:.5f}")
                    
                    if analysis['recommendations']:
                        print(f"   ⚠️  TAKING ACTION:")
                        for rec in analysis['recommendations']:
                            print(f"      - {rec['action']}: {rec['reason']}")
                            # AUTO-EXECUTE THE FIX
                            success = fix_position(pos, rec, execution)
                            if success:
                                print(f"      ✅ Fix applied successfully")
                            else:
                                print(f"      ❌ Fix failed - manual intervention needed")
                    else:
                        print(f"   ✅ Trade looks good")
                
                print(f"{'='*80}\n")
            
            # Check every 30 seconds
            time.sleep(30)
            
        except KeyboardInterrupt:
            print("\n👁️  Monitor stopped")
            break
        except Exception as e:
            print(f"⚠️  Monitor error: {e}")
            time.sleep(30)

if __name__ == "__main__":
    monitor_trades()
