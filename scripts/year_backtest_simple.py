"""One Year Backtest - Simple Results"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

# Get 1 year data
print("Loading 1 year EURUSD data...")
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 35040)
df = pd.DataFrame(rates)

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))

# Volume
df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)

# ADX
high, low, close = df['high'], df['low'], df['close']
tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
df['ATR'] = tr.rolling(14).mean()
plus_dm = high.diff()
minus_dm = -low.diff()
plus_dm[plus_dm < 0] = 0
minus_dm[minus_dm < 0] = 0
atr = tr.rolling(14).mean()
plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
df['ADX'] = dx.rolling(14).mean()

print(f"Data loaded: {len(df)} bars")

def backtest(df, name, filter_func):
    trades = []
    for i in range(100, len(df) - 100):
        curr = df.iloc[i]
        
        if not filter_func(curr):
            continue
            
        if curr['RSI'] < 30:
            direction = "BUY"
        elif curr['RSI'] > 70:
            direction = "SELL"
        else:
            continue
        
        entry = curr['close']
        sl_dist = curr['ATR'] * 2
        tp_dist = curr['ATR'] * 3
        
        if direction == "BUY":
            sl, tp = entry - sl_dist, entry + tp_dist
        else:
            sl, tp = entry + sl_dist, entry - tp_dist
        
        # Find exit
        for j in range(i+1, min(i+200, len(df))):
            bar = df.iloc[j]
            hit = False
            
            if direction == "BUY":
                if bar['low'] <= sl:
                    profit = (sl - entry) * 10000
                    hit = True
                elif bar['high'] >= tp:
                    profit = (tp - entry) * 10000
                    hit = True
            else:
                if bar['high'] >= sl:
                    profit = (entry - sl) * 10000
                    hit = True
                elif bar['low'] <= tp:
                    profit = (entry - tp) * 10000
                    hit = True
            
            if hit:
                trades.append(profit)
                break
    
    wins = [t for t in trades if t > 0]
    wr = len(wins) / len(trades) * 100 if trades else 0
    total = sum(trades) if trades else 0
    
    print(f"\n{name}:")
    print(f"  Trades: {len(trades)}")
    print(f"  Wins: {len(wins)} ({wr:.1f}%)")
    print(f"  Total: {total:.1f} pips")
    print(f"  Avg: {total/len(trades):.2f} pips/trade" if trades else "  Avg: 0")
    
    return {'trades': len(trades), 'wr': wr, 'total': total}

print("\n" + "="*50)
print("ONE YEAR BACKTEST RESULTS - EURUSD")
print("="*50)

r1 = backtest(df, "1. BASELINE (RSI only)", lambda c: True)
r2 = backtest(df, "2. + VPA (Vol>0.8)", lambda c: c['VOL_RATIO'] > 0.8)
r3 = backtest(df, "3. + VPA + ADX(>20)", lambda c: c['VOL_RATIO'] > 0.8 and c['ADX'] > 20)
r4 = backtest(df, "4. + VPA + ADX(>25)", lambda c: c['VOL_RATIO'] > 0.8 and c['ADX'] > 25)

print("\n" + "="*50)
print("IMPROVEMENT ANALYSIS:")
print("="*50)
if r1['wr'] > 0:
    print(f"VPA Impact: {r1['wr']:.1f}% → {r2['wr']:.1f}% ({r2['wr']-r1['wr']:+.1f}%)")
    print(f"VPA+ADX(20): {r1['wr']:.1f}% → {r3['wr']:.1f}% ({r3['wr']-r1['wr']:+.1f}%)")
    print(f"VPA+ADX(25): {r1['wr']:.1f}% → {r4['wr']:.1f}% ({r4['wr']-r1['wr']:+.1f}%)")

mt5.shutdown()
print("\n✅ Complete!\n")
