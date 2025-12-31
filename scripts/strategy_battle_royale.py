"""
Strategy Battle Royale
Tests 3 distinct logic models on historical GOLD data to find the highest performing edge.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from titan_system.smc.vwap_engine import VWAPEngine
from config.settings import settings

def run_battle_royale():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    symbol = "GOLD"
    # Get 2 weeks of M15 data (~2000 bars)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 2000) 
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate Indicators
    df['pdh'] = df['high'].rolling(96).max().shift(1)
    df['pdl'] = df['low'].rolling(96).min().shift(1)
    
    vwap_eng = VWAPEngine()
    vwap_res = vwap_eng.analyze(df) # Adds 'vwap' column
    
    # PnL Trackers
    pnl_A = 0.0 # Liquidator
    pnl_B = 0.0 # Trend Surfer
    pnl_C = 0.0 # VWAP Mean Revert
    
    trades_A = 0
    trades_B = 0
    trades_C = 0
    
    active_A = None
    active_B = None
    active_C = None
    
    with open("battle_results.txt", "w", encoding="utf-8") as f:
        def log(msg):
            print(msg)
            f.write(msg + "\n")
            
        log("\n" + "="*80)
        log(f"🥊 STRATEGY BATTLE ROYALE: GOLD (Last 14 Days)")
        log("="*80)
        
        for i in range(100, len(df)):
            row = df.iloc[i]
            prev = df.iloc[i-1]
            
            # --- STRATEGY A: LIQUIDITY SWEEPS (Fade the Break) ---
            if active_A:
                if active_A['type'] == 'BUY':
                    if row['low'] <= active_A['sl']: pnl_A -= 50; active_A = None
                    elif row['high'] >= active_A['tp']: pnl_A += 100; active_A = None
                else:
                    if row['high'] >= active_A['sl']: pnl_A -= 50; active_A = None
                    elif row['low'] <= active_A['tp']: pnl_A += 100; active_A = None
            
            if not active_A:
                # Buy Sweep of Low
                if prev['low'] < row['pdl'] and row['close'] > row['pdl']:
                    active_A = {'type': 'BUY', 'sl': row['close']-5.0, 'tp': row['close']+10.0}
                    trades_A += 1
                # Sell Sweep of High
                elif prev['high'] > row['pdh'] and row['close'] < row['pdh']:
                    active_A = {'type': 'SELL', 'sl': row['close']+5.0, 'tp': row['close']-10.0}
                    trades_A += 1

            # --- STRATEGY B: TREND SURFER (Follow the Break) ---
            if active_B:
                # Trailing Stop Logic (Simplified)
                current_price = row['close']
                if active_B['type'] == 'BUY':
                    if row['low'] <= active_B['sl']: 
                        pnl_B += (active_B['sl'] - active_B['entry']) * 10
                        active_B = None
                    else:
                        new_sl = row['high'] - 5.0
                        if new_sl > active_B['sl']: active_B['sl'] = new_sl
                else:
                     if row['high'] >= active_B['sl']: 
                        pnl_B += (active_B['entry'] - active_B['sl']) * 10
                        active_B = None
                     else:
                        new_sl = row['low'] + 5.0
                        if new_sl < active_B['sl']: active_B['sl'] = new_sl
            
            if not active_B:
                # Buy BREAKOUT of High (Close > PDH)
                if row['close'] > row['pdh']:
                    # Filter: Don't buy if we are miles above it
                    if (row['close'] - row['pdh']) < 5.0:
                        active_B = {'type': 'BUY', 'entry': row['close'], 'sl': row['close']-5.0}
                        trades_B += 1
                # Sell BREAKDOWN of Low (Close < PDL)
                elif row['close'] < row['pdl']:
                    if (row['pdl'] - row['close']) < 5.0:
                        active_B = {'type': 'SELL', 'entry': row['close'], 'sl': row['close']+5.0}
                        trades_B += 1
                        
            # --- STRATEGY C: VWAP MEAN REVERSION (Rubber Band) ---
            if active_C:
                if active_C['type'] == 'BUY':
                    # Exit at VWAP
                    if row['high'] >= row['vwap']:
                         profit = (row['vwap'] - active_C['entry']) * 10
                         pnl_C += profit
                         active_C = None
                    elif row['low'] <= active_C['sl']:
                         pnl_C -= 50; active_C = None
                else:
                     if row['low'] <= row['vwap']:
                         profit = (active_C['entry'] - row['vwap']) * 10
                         pnl_C += profit
                         active_C = None
                     elif row['high'] >= active_C['sl']:
                         pnl_C -= 50; active_C = None
                         
            if not active_C:
                dist = row['close'] - row['vwap']
                # If Price is 20 points BELOW VWAP -> Buy
                if dist < -20.0:
                    active_C = {'type': 'BUY', 'entry': row['close'], 'sl': row['close']-5.0}
                    trades_C += 1
                # If Price is 20 points ABOVE VWAP -> Sell
                elif dist > 20.0:
                    active_C = {'type': 'SELL', 'entry': row['close'], 'sl': row['close']+5.0}
                    trades_C += 1

        log(f"📊 RESULTS (Ascending Order of Profit):")
        
        results = [
            ("A: Liquidator (Fade)", pnl_A, trades_A),
            ("B: Trend Surfer (Follow)", pnl_B, trades_B),
            ("C: VWAP Revert (Mean)", pnl_C, trades_C)
        ]
        results.sort(key=lambda x: x[1])
        
        for name, pnl, trades in results:
            log(f"   {name:<25} | PnL: ${pnl:+.2f} | Trades: {trades}")
            
        log("="*80)
    
    mt5.shutdown()

if __name__ == "__main__":
    run_battle_royale()
