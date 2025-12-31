"""
InstitutionalEngine Backtest
============================
Tests how the current InstitutionalEngine setup detection would have performed.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def main():
    print("=" * 60)
    print("BACKTESTING INSTITUTIONAL ENGINE")
    print("=" * 60)
    
    if not mt5.initialize():
        print(f"MT5 failed: {mt5.last_error()}")
        return
    
    from titan_system.smc.institutional_engine import InstitutionalEngine
    inst_engine = InstitutionalEngine()
    
    symbols = ["EURUSD", "GBPUSD", "GOLD", "USDJPY"]
    results = []
    
    for symbol in symbols:
        print(f"\n--- Testing {symbol} ---")
        
        # Get 500 H1 candles (about 3 weeks of data)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 500)
        if rates is None or len(rates) < 200:
            print(f"  Skipping - insufficient data")
            continue
        
        df_full = pd.DataFrame(rates)
        df_full['time'] = pd.to_datetime(df_full['time'], unit='s')
        
        signals_found = 0
        wins = 0
        losses = 0
        total_pips = 0
        
        # Walk through history, simulating what the engine would have seen
        for i in range(200, len(df_full) - 10):  # Need 200 bars lookback, 10 bars forward
            df_window = df_full.iloc[:i].copy().reset_index(drop=True)
            
            try:
                analysis = inst_engine.analyze_symbol(df_window, symbol)
                setups = analysis.get('setup', [])
                
                if setups:
                    setup = setups[0]
                    setup_name = setup.get('name', '')
                    entry_price = df_full.iloc[i]['open']  # Entry on next candle open
                    
                    # Determine direction
                    if 'BULLISH' in setup_name or 'LONG' in setup_name:
                        direction = 1  # Long
                    elif 'BEARISH' in setup_name or 'SHORT' in setup_name:
                        direction = -1  # Short
                    else:
                        continue
                    
                    signals_found += 1
                    
                    # Check outcome after 5 candles
                    exit_price = df_full.iloc[i + 5]['close']
                    
                    # Calculate P/L
                    if symbol == "GOLD":
                        pip_value = 0.1  # Gold uses 0.1
                    else:
                        pip_value = 0.0001  # Forex
                    
                    pips = (exit_price - entry_price) * direction / pip_value
                    
                    if pips > 0:
                        wins += 1
                    else:
                        losses += 1
                    
                    total_pips += pips
                    
            except Exception:
                continue
        
        if signals_found > 0:
            win_rate = wins / signals_found * 100
            avg_pips = total_pips / signals_found
            
            print(f"  Signals Found: {signals_found}")
            print(f"  Wins: {wins}, Losses: {losses}")
            print(f"  Win Rate: {win_rate:.1f}%")
            print(f"  Avg Pips: {avg_pips:.1f}")
            print(f"  Total Pips: {total_pips:.1f}")
            
            results.append({
                'symbol': symbol,
                'signals': signals_found,
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_pips': total_pips
            })
        else:
            print(f"  NO SIGNALS FOUND in last 500 H1 candles!")
            print(f"  This confirms the strategy is TOO SELECTIVE")
    
    # Summary
    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    
    if results:
        total_signals = sum(r['signals'] for r in results)
        total_wins = sum(r['wins'] for r in results)
        total_losses = sum(r['losses'] for r in results)
        total_pips = sum(r['total_pips'] for r in results)
        
        print(f"\nTotal Signals: {total_signals}")
        print(f"Total Wins: {total_wins}")
        print(f"Total Losses: {total_losses}")
        print(f"Overall Win Rate: {total_wins/(total_wins+total_losses)*100:.1f}%")
        print(f"Total Pips: {total_pips:.1f}")
    else:
        print("\nNO SIGNALS GENERATED ACROSS ALL SYMBOLS!")
        print("The InstitutionalEngine criteria are TOO STRICT.")
        print("\nRecommendation: Lower TSS threshold from 4 to 3")
        print("Or add a secondary, more frequent strategy.")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
