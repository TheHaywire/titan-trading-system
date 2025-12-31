"""
OPTIMIZED BACKTEST - Realistic Thresholds
==========================================
Based on actual market data distribution
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

def backtest_eurusd():
    """Backtest EURUSD with optimized parameters"""
    
    if not mt5.initialize():
        print("MT5 failed")
        return
    
    print("🚀 OPTIMIZED BACKTEST - 30 Days EURUSD")
    print("="*60)
    
    # Get 30 days of M15 data
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 2880)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate indicators
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
    
    df['MOM'] = df['close'].pct_change(5) * 100
    df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
    df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)
    
    # ATR
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # ADX
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    atr_adx = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr_adx)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr_adx)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['ADX'] = dx.rolling(14).mean()
    
    print(f"Data: {len(df)} bars")
    print(f"RSI range: {df['RSI'].min():.1f} - {df['RSI'].max():.1f}")
    print(f"ADX range: {df['ADX'].min():.1f} - {df['ADX'].max():.1f}")
    print()
    
    # Strategies to test
    strategies = {
        'Baseline (RSI<30/70)': lambda r: r['RSI'] < 30 or r['RSI'] > 70,
        '+ Volume Filter': lambda r: (r['RSI'] < 30 or r['RSI'] > 70) and r['VOL_RATIO'] > 0.8,
        '+ ADX Filter': lambda r: (r['RSI'] < 30 or r['RSI'] > 70) and r['VOL_RATIO'] > 0.8 and r['ADX'] > 20,
        '+ Momentum': lambda r: ((r['RSI'] < 30 and r['MOM'] > 0.3) or (r['RSI'] > 70 and r['MOM'] < -0.3)) and r['VOL_RATIO'] > 0.8 and r['ADX'] > 20,
    }
    
    for name, strategy_func in strategies.items():
        trades = []
        point = 0.0001
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            
            if not strategy_func(curr):
                continue
            
            # Determine direction
            if curr['RSI'] < 50:
                direction = "BUY"
                entry = curr['close']
                sl = entry - (curr['ATR'] * 2)
                tp = entry + (curr['ATR'] * 3)
            else:
                direction = "SELL"
                entry = curr['close']
                sl = entry + (curr['ATR'] * 2)
                tp = entry - (curr['ATR'] * 3)
            
            # Find exit
            for j in range(i+1, min(i+100, len(df))):
                bar = df.iloc[j]
                
                hit_sl = False
                hit_tp = False
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        hit_sl = True
                        exit_price = sl
                    elif bar['high'] >= tp:
                        hit_tp = True
                        exit_price = tp
                else:
                    if bar['high'] >= sl:
                        hit_sl = True
                        exit_price = sl
                    elif bar['low'] <= tp:
                        hit_tp = True
                        exit_price = tp
                
                if hit_sl or hit_tp:
                    profit_pips = (exit_price - entry) / point if direction == "BUY" else (entry - exit_price) / point
                    trades.append({
                        'profit': profit_pips,
                        'direction': direction,
                        'entry': entry,
                        'exit': exit_price,
                        'bars': j - i
                    })
                    break
        
        # Analyze
        if not trades:
            print(f"{name}: ❌ No trades")
            continue
        
        profits = [t['profit'] for t in trades]
        wins = [p for p in profits if p > 0]
        losses = [p for p in profits if p <= 0]
        
        win_rate = len(wins) / len(trades) * 100
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        total_pips = sum(profits)
        expectancy = np.mean(profits)
        
        print(f"\n{name}:")
        print(f"  Trades: {len(trades)}")
        print(f"  Win rate: {win_rate:.1f}%")
        print(f"  Avg win: {avg_win:.1f} pips")
        print(f"  Avg loss: {avg_loss:.1f} pips")
        print(f"  Total: {total_pips:.1f} pips")
        print(f"  Expectancy: {expectancy:.2f} pips/trade")
        
        if wins and losses:
            pf = abs(sum(wins) / sum(losses))
            print(f"  Profit Factor: {pf:.2f}")
    
    print("\n" + "="*60)
    mt5.shutdown()

if __name__ == "__main__":
    backtest_eurusd()
