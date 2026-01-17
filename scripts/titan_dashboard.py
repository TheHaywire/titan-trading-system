"""
TITAN TERMINAL DASHBOARD
========================
Real-time "Command Center" for the terminal.
Displays: Account Health, Active Positions, and Live Scanner Results.
Refreshes every 2 seconds.
"""

import os
import time
import sys
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Import internal modules (assuming in path)
sys.path.append(os.getcwd())
# We will pull scanner logic directly here or via the orchestrator/signal producer modules if needed
# For dashboard speed, we might want light-weight polling

WATCHLIST = ["ETHUSD", "SILVER", "GOLD", "US100Cash", "BTCUSD"]

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_account_status():
    acct = mt5.account_info()
    if not acct: return None
    return {
        "fw_equity": acct.equity,
        "balance": acct.balance,
        "margin": acct.margin,
        "free_margin": acct.margin_free,
        "margin_level": acct.margin_level,
        "profit": acct.profit
    }

def get_positions():
    positions = mt5.positions_get()
    if not positions: return []
    return positions

# Import Pattern Engine
from pattern_recognition_engine import PatternEngine

pattern_engine = PatternEngine()

def get_market_pulse(symbol):
    # Quick scan for pattern/structure
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if rates is None: return "N/A", "N/A", "N/A", "N/A"
    
    df = pd.DataFrame(rates)
    
    # 1. Trend
    sma20 = df['close'].rolling(20).mean().iloc[-1]
    sma50 = df['close'].rolling(50).mean().iloc[-1]
    trend = "BULLISH 🟢" if sma20 > sma50 else "BEARISH 🔴"
    
    # 2. RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_val = rsi.iloc[-1]
    rsi_stat = f"{rsi_val:.1f}"
    if rsi_val > 70: rsi_stat += " (OB)"
    if rsi_val < 30: rsi_stat += " (OS)"
    
    # 3. Patterns (FinViz Style)
    patterns = pattern_engine.analyze(df)
    pattern_str = patterns[0] if patterns else "None"
    
    # 4. Quant Win Rate (Simulated based on Trend+RSI)
    # Simple probability model
    win_rate = 50
    if "BULLISH" in trend: win_rate += 5
    if "BEARISH" in trend: win_rate += 5
    if rsi_val < 30 and "BULLISH" in trend: win_rate += 15 # Pullback
    if rsi_val > 70 and "BEARISH" in trend: win_rate += 15 # Pullback
    if "Channel" in pattern_str: win_rate += 10
    
    return trend, rsi_stat, pattern_str, f"{win_rate}%"

def print_dashboard():
    while True:
        if not mt5.initialize():
            print("MT5 Connection Failed. Retrying...")
            time.sleep(5)
            continue
            
        clear_screen()
        status = get_account_status()
        
        # 1. HEADER
        print("="*100)
        print(f" TITAN SYSTEM v2.0 | COMMAND CENTER | {datetime.now().strftime('%H:%M:%S')}")
        print("="*100)
        if status:
            print(f" 💰 EQUITY:      ${status['fw_equity']:,.2f}   (PnL Today: ${status['profit']:,.2f})")
            print(f" 🛡️ MARGIN:      {status['margin_level']:.2f}%     (Used: ${status['margin']:,.2f})")
            print(f" 🎮 MODE:        PILOT ACTIVE (Power Steering)")
            
            # EQUITY SIMULATOR (Quant Feature)
            # Assuming 2 open trades, 2% risk each, 4% reward
            risk_amt = status['fw_equity'] * 0.02
            reward_amt = risk_amt * 2
            print(f" 🔮 PREDICTION:  If TP hit -> ${status['fw_equity'] + reward_amt:,.2f} | If SL hit -> ${status['fw_equity'] - risk_amt:,.2f}")
            
        else:
            print(" ⚠️ ACCOUNT INFO UNAVAILABLE")
        print("-" * 100)
        
        # 2. ACTIVE POSITIONS
        print(f" ✈️  ACTIVE FLIGHT DECK (Positions)")
        print(f" {'TICKET':<12} | {'SYMBOL':<10} | {'TYPE':<4} | {'VOL':<5} | {'OPEN':<10} | {'CURR':<10} | {'PNL':<10}")
        print("-" * 100)
        
        positions = get_positions()
        if positions:
            for p in positions:
                type_str = "BUY" if p.type == 0 else "SELL"
                pnl = p.profit
                pnl_str = f"${pnl:,.2f}"
                print(f" {p.ticket:<12} | {p.symbol:<10} | {type_str:<4} | {p.volume:<5} | {p.price_open:<10.2f} | {p.price_current:<10.2f} | {pnl_str:<10}")
        else:
            print(" No Active Trades.")
            
        print("-" * 100)
        
        # 3. ALPHA SCANNER
        print(f" 📡 ALPHA RADAR (Hand-Picked Watchlist)")
        print(f" {'SYMBOL':<12} | {'H1 TREND':<15} | {'RSI':<10} | {'PATTERN (FinViz)':<20} | {'WIN RATE':<10} | {'EDGE VERDICT'}")
        print("-" * 100)
        
        for sym in WATCHLIST:
            trend, rsi, pat, wr = get_market_pulse(sym)
            
            # Simple Edge Logic for display
            edge = "WAIT"
            if int(wr.replace("%", "")) > 65: edge = "🚀 FIRE"
            elif int(wr.replace("%", "")) > 60: edge = "👀 WATCH"
            
            print(f" {sym:<12} | {trend:<15} | {rsi:<10} | {pat:<20} | {wr:<10} | {edge}")
            
        print("="*80)
        print(" [CTRL+C] to Exit Dashboard")
        
        # Refresh Rate
        time.sleep(2)

if __name__ == "__main__":
    try:
        print_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard Closed.")
        mt5.shutdown()
