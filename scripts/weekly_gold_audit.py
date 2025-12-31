"""
Weekly Institutional Strategy Audit
Simulates precise PnL for the last 7 days of GOLD trading using the DOP logic.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from titan_system.smc.momentum_engine import MomentumEngine
from config.settings import settings

def run_weekly_audit():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    symbol = "GOLD"
    # Get last 7 days of M15 data (~672 bars)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 1500) 
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate RSI
    mom = MomentumEngine()
    df['rsi'] = mom.calculate_rsi(df['close'], 14)
    
    # Simple Liquidity Logic: Rolling 24h High/Low
    df['pdh'] = df['high'].rolling(96).max().shift(1) # Previous 96 bars (24h) High
    df['pdl'] = df['low'].rolling(96).min().shift(1)  # Previous 96 bars (24h) Low
    
    with open("weekly_audit.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        log("\n" + "="*80)
        log(f"📅 WEEKLY INSTITUTIONAL AUDIT: {symbol} (Last 7 Days)")
        log("Strategy: Liquidity Sweeps (LSR) + Momentum Fades")
        log("Size: 0.10 Lots | SL: 50 pts ($50) | TP: 100 pts ($100)")
        log("="*80)
        log(f"{'DATE':<12} {'TIME':<10} {'TYPE':<6} {'STATUS':<50} {'RESULT':<10}")
        log("-" * 100)
        
        equity = 10000.0
        wins = 0
        losses = 0
        
        active_trade = None
        
        for i in range(100, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # 1. MANAGE ACTIVE TRADE
            if active_trade:
                # Check SL/TP
                sl = active_trade['sl']
                tp = active_trade['tp']
                
                if active_trade['type'] == 'BUY':
                    if row['low'] <= sl:
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   ❌ STOP LOSS HIT at {sl:.2f}                               -$50")
                        equity -= 50
                        losses += 1
                        active_trade = None
                    elif row['high'] >= tp:
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   ✅ TAKE PROFIT HIT at {tp:.2f}                              +$100")
                        equity += 100
                        wins += 1
                        active_trade = None
                else: # SELL
                    if row['high'] >= sl:
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   ❌ STOP LOSS HIT at {sl:.2f}                               -$50")
                        equity -= 50
                        losses += 1
                        active_trade = None
                    elif row['low'] <= tp:
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   ✅ TAKE PROFIT HIT at {tp:.2f}                              +$100")
                        equity += 100
                        wins += 1
                        active_trade = None
                continue # Don't take new trade if one is active (Simple logic)
                
            # 2. CHECK FOR ENTRIES
            # LONG: Sweep PDL (Low < PDL) but Close back above PDL
            if row['low'] < row['pdl'] and row['close'] > row['pdl']:
                 reason = f"SWEEP PDL ({row['pdl']:.2f})"
                 log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      BUY    ⚡ {reason:<45} Entry: {row['close']:.2f}")
                 active_trade = {
                     'type': 'BUY', 'entry': row['close'], 
                     'sl': row['close'] - 5.0, # 500 pips (5.0 points)
                     'tp': row['close'] + 10.0 # 1000 pips (10.0 points)
                 }
                 
            # SHORT: Sweep PDH (High > PDH) but Close back below PDH
            elif row['high'] > row['pdh'] and row['close'] < row['pdh']:
                 reason = f"SWEEP PDH ({row['pdh']:.2f})"
                 log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      SELL   ⚡ {reason:<45} Entry: {row['close']:.2f}")
                 active_trade = {
                     'type': 'SELL', 'entry': row['close'], 
                     'sl': row['close'] + 5.0,
                     'tp': row['close'] - 10.0
                 }
                 
        log("="*100)
        log(f"🏆 FINAL RESULT:")
        log(f"   Trades: {wins+losses}")
        log(f"   Wins:   {wins} ({wins/(wins+losses)*100:.1f}%)" if (wins+losses) > 0 else "   Wins: 0")
        log(f"   Losses: {losses}")
        log(f"   Net PnL: ${equity - 10000:.2f}")
        log(f"   Final Equity: ${equity:.2f}")
        log("="*100)
    
    mt5.shutdown()

if __name__ == "__main__":
    run_weekly_audit()
