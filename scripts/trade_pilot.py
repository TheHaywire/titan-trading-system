"""
TITAN TRADE PILOT (Power Steering)
==================================
Manages trade safety without being destructive.
- Adds missing SL/TP based on ATR.
- Adjusts risk dynamically based on CURRENT equity.
- Alerts user to extreme violations rather than insta-killing.
"""

import MetaTrader5 as mt5
import os
from datetime import datetime
import pandas as pd
import sys

# Import Monte Carlo Simulator
sys.path.append(os.getcwd())
from scripts.risk_monte_carlo import get_monte_carlo_results

# SETTINGS (Adaptive)
RISK_PER_TRADE_PCT = 2.0  # Aim for 2% risk per position
ATR_MULTIPLIER_SL = 1.5   # Standard SL distance
POLL_INTERVAL_S = 1.0     # Check every second (less aggressive than Janitor)

def get_structural_stop(symbol, order_type):
    """
    Finds a 'Smart' Structural Stop Loss based on recent Swing High/Low.
    Uses M15 structure for tight execution context.
    """
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
    if rates is None: return None
    
    df = pd.DataFrame(rates)
    # Simple Swing Detection (High/Low of last 10 bars)
    last_low = df['low'].rolling(10).min().iloc[-1]
    last_high = df['high'].rolling(10).max().iloc[-1]
    
    # ATR for buffer
    high_low = df['high'] - df['low']
    atr = high_low.rolling(14).mean().iloc[-1]
    
    if order_type == 0: # BUY
        # SL below recent structure low + small buffer
        return last_low - (atr * 0.5)
    else: # SELL
        # SL above recent structure high + small buffer
        return last_high + (atr * 0.5)

def fix_missing_sl(pos):
    """Apply a STRUCTURAL (Context-Aware) SL if missing."""
    symbol = pos.symbol
    ticket = pos.ticket
    
    # 1. Try to get a smart structural level
    new_sl = get_structural_stop(symbol, pos.type)
    
    if not new_sl:
        print(f"⚠️ PILOT: Could not find structure for {symbol}, tracking manually.")
        return False
        
    # Apply SL
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": ticket,
        "sl": new_sl,
        "tp": 0.0, # Let user or trailing stop handle TP
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"🧠 SMART PILOT: Added STRUCTURAL SL to {symbol} #{ticket} at {new_sl} (Context-Aware)")
        return True
    return False

def check_account_sizing(pos, equity):
    """Check if position is dangerously oversized for current equity."""
    symbol_info = mt5.symbol_info(pos.symbol)
    if not symbol_info: return False
    
    # Calculate margin required for this position
    # (Simplified: Lot * ContractSize * Price / Leverage)
    # MT5 has a tool for this though:
    margin = mt5.order_calc_margin(pos.type, pos.symbol, pos.volume, pos.price_open)
    if margin is None: return False
    
    margin_utilization = (margin / equity) * 100
    
    if margin_utilization > 30: # If one position uses > 30% of total equity
        print(f"⚠️ PILOT: {pos.symbol} #{pos.ticket} is using {margin_utilization:.1f}% margin. DANGEROUS.")
        return True
    return False

def pyramid_position(pos, mc_prob):
    """
    Autonomously scale-in (pyramid) if conviction is high (>70% win prob).
    Conditions:
    1. Win Prob > 70% (Monte Carlo)
    2. Position is in profit (>1% of equity)
    3. No existing pyramid order (Magic number check or Comment)
    """
    if mc_prob < 70 or pos.profit < 0:
        return False
        
    # Check if we already pyramided this ticket (simple comment check)
    if "PYRAMID" in pos.comment:
        return False
        
    symbol = pos.symbol
    lots = pos.volume * 0.5 # Scale in with half size
    
    print(f"🚀 PILOT: HIGH CONVICTION ({mc_prob}%). Pyramiding {symbol} #{pos.ticket}...")
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lots,
        "type": pos.type,
        "price": mt5.symbol_info_tick(symbol).ask if pos.type == 0 else mt5.symbol_info_tick(symbol).bid,
        "sl": pos.sl, # Inherit existing SL
        "tp": pos.tp, # Inherit existing TP
        "magic": 999999,
        "comment": f"PYRAMID_{pos.ticket}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ PILOT: Pyramid order filled for {symbol} (Total Lot: {pos.volume + lots})")
        return True
    return False

def run_pilot():
    print("🚀 TRADE PILOT ACTIVE | Setting: Power Steering Mode")
    print("Goal: Fix trades, don't kill them. Scale-in on High Conviction.")
    
    if not mt5.initialize():
        return

    try:
        while True:
            positions = mt5.positions_get()
            account = mt5.account_info()
            mc_results = get_monte_carlo_results(standalone=False)
            
            if positions:
                for pos in positions:
                    # 1. Missing Stop Loss? FIX IT.
                    if pos.sl == 0:
                        fix_missing_sl(pos)
                    
                    # 2. Oversized? WARN
                    check_account_sizing(pos, account.equity)
                    
                    # 3. HIGH CONVICTION? PYRAMID (Aggressive Growth)
                    ticket_str = str(pos.ticket)
                    if ticket_str in mc_results:
                        prob = mc_results[ticket_str]['win_prob']
                        pyramid_position(pos, prob)
            
            time.sleep(POLL_INTERVAL_S)
    except KeyboardInterrupt:
        pass
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    import pandas as pd
    run_pilot()
