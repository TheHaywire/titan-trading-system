"""
Weekly Audit: THE RUNNER EDITION
Simulates the same trades but with a Trailing Stop to capture massive trends.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config.settings import settings

def run_audit_runner():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 1500) 
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Simple Liquidity Logic
    df['pdh'] = df['high'].rolling(96).max().shift(1)
    df['pdl'] = df['low'].rolling(96).min().shift(1)
    
    with open("weekly_runner_audit.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")

        log("\n" + "="*80)
        log(f"🚀 WEEKLY AUDIT: THE 'RUNNER' STRATEGY (Trailing Stop)")
        log("Goal: Don't take $100. Take $1,000.")
        log("Logic: Entry same. Exit = Trail SL by 5.0 points.")
        log("="*80)
        log(f"{'DATE':<12} {'TIME':<10} {'TYPE':<6} {'STATUS':<50} {'RESULT':<10} {'EQUITY':<10}")
        log("-" * 110)
        
        equity = 10000.0
        active_trade = None
        
        wins = 0
        losses = 0
        big_wins = 0
        
        for i in range(100, len(df)):
            row = df.iloc[i]
            
            # 1. MANAGE ACTIVE TRADE (Trailing Logic)
            if active_trade:
                sl = active_trade['sl']
                current_profit = 0
                
                if active_trade['type'] == 'BUY':
                    # Calc floating profit
                    current_profit_pts = row['high'] - active_trade['entry']
                    
                    # Check Stop Loss
                    if row['low'] <= sl:
                        loss_amt = (sl - active_trade['entry']) * 10 # $10 per point (0.10 lot)
                        equity += loss_amt
                        
                        outcome = "❌ STOP OUT" if loss_amt < 0 else "🛡️ TRAILING STOP HIT"
                        icon = "❌" if loss_amt < 0 else "💰"
                        if loss_amt > 200: 
                            icon = "🚀"
                            big_wins += 1
                        elif loss_amt > 0:
                            wins += 1
                        else:
                            losses += 1
                            
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   {icon} {outcome} at {sl:.2f} ({loss_amt:+.0f} USD)             ${loss_amt:+.0f}       ${equity:.0f}")
                        active_trade = None
                    
                    # Trail Stop logic: If price moves up, drag SL up behind it (Distance 5.0)
                    else:
                        new_sl = row['high'] - 5.0 
                        if new_sl > sl:
                            active_trade['sl'] = new_sl
                            
                else: # SELL
                    # Check Stop Loss
                    if row['high'] >= sl:
                        loss_amt = (active_trade['entry'] - sl) * 10
                        equity += loss_amt
                        
                        outcome = "❌ STOP OUT" if loss_amt < 0 else "🛡️ TRAILING STOP HIT"
                        icon = "❌" if loss_amt < 0 else "💰"
                        if loss_amt > 200: 
                            icon = "🚀"
                            big_wins += 1
                        elif loss_amt > 0:
                            wins += 1
                        else:
                            losses += 1
                            
                        log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      EXIT   {icon} {outcome} at {sl:.2f} ({loss_amt:+.0f} USD)             ${loss_amt:+.0f}       ${equity:.0f}")
                        active_trade = None
                    
                    # Trail Stop logic
                    else:
                        new_sl = row['low'] + 5.0
                        if new_sl < sl:
                            active_trade['sl'] = new_sl
                            
                continue 
            
            # 2. ENTRIES (Same as before)
            if row['low'] < row['pdl'] and row['close'] > row['pdl']:
                 log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      BUY    ⚡ SWEEP PDL. Entry: {row['close']:.2f}")
                 active_trade = {
                     'type': 'BUY', 'entry': row['close'], 
                     'sl': row['close'] - 5.0
                 }
            elif row['high'] > row['pdh'] and row['close'] < row['pdh']:
                 log(f"{row['time'].date()}   {row['time'].strftime('%H:%M')}      SELL   ⚡ SWEEP PDH. Entry: {row['close']:.2f}")
                 active_trade = {
                     'type': 'SELL', 'entry': row['close'], 
                     'sl': row['close'] + 5.0
                 }
                 
        log("="*110)
        log(f"🏆 RUNNER RESULT:")
        log(f"   Net PnL: ${equity - 10000:.2f}")
        log(f"   Big Runners (>$200): {big_wins}")
        log("="*110)
    
    mt5.shutdown()

if __name__ == "__main__":
    run_audit_runner()
