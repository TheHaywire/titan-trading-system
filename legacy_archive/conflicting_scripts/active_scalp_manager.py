"""
Active Scalp Manager for GOLD
Monitors M15 extremes and manages active scalp positions.
"""
import MetaTrader5 as mt5
import pandas as pd
import time
from titan_system.smc.vwap_engine import VWAPEngine
from titan_system.smc.momentum_engine import MomentumEngine
from config.settings import settings

SYMBOL = "GOLD"
MAGIC_NUMBER = 999001  # Special Magic for Manual Scalps
LOT_SIZE = 0.01  # Keep it small for recovery
SL_POINTS = 5.0
TP_POINTS = 10.0

def execute_scalp(direction):
    """Execute Market Order"""
    price = mt5.symbol_info_tick(SYMBOL).ask if direction == "BUY" else mt5.symbol_info_tick(SYMBOL).bid
    order_type = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
    
    sl = price - SL_POINTS if direction == "BUY" else price + SL_POINTS
    tp = price + TP_POINTS if direction == "BUY" else price - TP_POINTS
    
    req = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": MAGIC_NUMBER,
        "comment": "M15 Scalp Bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    res = mt5.order_send(req)
    if res.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"🚀 SCALP EXECUTED: {direction} @ {price}")
        return True
    else:
        print(f"❌ EXECUTION FAILED: {res.comment}")
        return False

def manage_trades():
    """Trail SL and Monitor Exit"""
    positions = mt5.positions_get(symbol=SYMBOL)
    if not positions:
        return False
        
    for pos in positions:
        if pos.magic == MAGIC_NUMBER:
            profit_points = 0
            current_price = mt5.symbol_info_tick(SYMBOL).bid if pos.type == 0 else mt5.symbol_info_tick(SYMBOL).ask
            
            if pos.type == 0: # BUY
                profit_points = current_price - pos.price_open
            else: # SELL
                profit_points = pos.price_open - current_price
            
            # Print status
            print(f"   Pos {pos.ticket}: P/L Points = {profit_points:.2f}")
            
            # Trail SL to Breakeven after 3 points profit
            if profit_points >= 3.0:
                # Check if SL is already at BE
                is_be = abs(pos.sl - pos.price_open) < 0.1
                if not is_be:
                    print("   🛡️ Moving SL to Breakeven...")
                    req = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": pos.price_open, # Move to Entry
                        "tp": pos.tp
                    }
                    mt5.order_send(req)
                    
    return True

def scalp_loop():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    print(f"⚔️ ACTIVE SCALP MANAGER ONLINE | {SYMBOL}")
    print("   Monitoring M15 RSI > 78 for SHORT SCALP...")
    
    while True:
        try:
            # Check Active Positions
            has_active = manage_trades()
            
            if not has_active:
                # Scan for Entry
                rates = mt5.copy_rates_from_pos(SYMBOL, mt5.TIMEFRAME_M15, 0, 100)
                df = pd.DataFrame(rates)
                
                # Logic
                vwap_eng = VWAPEngine()
                vwap_res = vwap_eng.analyze(df)
                
                mom_eng = MomentumEngine()
                mom_res = mom_eng.analyze(df)
                
                rsi = mom_res['rsi']
                price = df['close'].iloc[-1]
                dist = price - vwap_res['vwap']
                
                print(f"   Scanning... Price: {price:.2f} | RSI: {rsi:.1f} | Dist: {dist:.2f}")
                
                # ENTRY TRIGGER
                # STRICT SCALP: RSI > 78 AND Extension > 8 points
                if rsi > 78 and dist > 8.0:
                     print("!!! SIGNAL DETECTED: SHORT !!!")
                     execute_scalp("SELL")
                     
                elif rsi < 22 and dist < -8.0:
                     print("!!! SIGNAL DETECTED: LONG !!!")
                     execute_scalp("BUY")
            
            time.sleep(10) # 10s Loop
            
        except KeyboardInterrupt:
            print("\n🛑 Scalp Manager Stopped")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    scalp_loop()
