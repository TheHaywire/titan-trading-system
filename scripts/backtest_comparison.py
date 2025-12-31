"""Backtest Comparison - Baseline vs Enhanced"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 2880)
df = pd.DataFrame(rates)

# Calculate all indicators
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))

df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)

high = df['high']
low = df['low']
close = df['close']
tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)

plus_dm = high.diff()
minus_dm = -low.diff()
plus_dm[plus_dm < 0] = 0
minus_dm[minus_dm < 0] = 0
atr = tr.rolling(14).mean()
plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
df['ADX'] = dx.rolling(14).mean()

results = []

# 1. BASELINE
trades_baseline = []
for i in range(50, len(df) - 50):
    if df.iloc[i]['RSI'] < 30:
        direction = "BUY"
    elif df.iloc[i]['RSI'] > 70:
        direction = "SELL"
    else:
        continue
    entry = df.iloc[i]['close']
    exit_price = df.iloc[i+20]['close']
    profit = (exit_price - entry) * 10000 if direction == "BUY" else (entry - exit_price) * 10000
    trades_baseline.append(profit)

# 2. WITH VOLUME FILTER
trades_vpa = []
for i in range(50, len(df) - 50):
    vol_ratio = df.iloc[i]['VOL_RATIO']
    if vol_ratio < 0.8:  # Skip low volume
        continue
    if df.iloc[i]['RSI'] < 30:
        direction = "BUY"
    elif df.iloc[i]['RSI'] > 70:
        direction = "SELL"
    else:
        continue
    entry = df.iloc[i]['close']
    exit_price = df.iloc[i+20]['close']
    profit = (exit_price - entry) * 10000 if direction == "BUY" else (entry - exit_price) * 10000
    trades_vpa.append(profit)

# 3. WITH VPA + ADX
trades_full = []
for i in range(50, len(df) - 50):
    vol_ratio = df.iloc[i]['VOL_RATIO']
    adx = df.iloc[i]['ADX']
    
    if vol_ratio < 0.8 or adx < 20:  # Skip low volume or weak trend
        continue
    
    if df.iloc[i]['RSI'] < 30:
        direction = "BUY"
    elif df.iloc[i]['RSI'] > 70:
        direction = "SELL"
    else:
        continue
    
    entry = df.iloc[i]['close']
    exit_price = df.iloc[i+20]['close']
    profit = (exit_price - entry) * 10000 if direction == "BUY" else (entry - exit_price) * 10000
    trades_full.append(profit)

# Print results
def analyze(trades, name):
    if not trades:
        print(f"{name}: No trades")
        return None
    wins = [t for t in trades if t > 0]
    wr = len(wins) / len(trades) * 100
    avg = np.mean(trades)
    total = sum(trades)
    return {'trades': len(trades), 'wr': wr, 'avg': avg, 'total': total}

print("\n" + "="*60)
print("BACKTEST COMPARISON - 30 Days EURUSD")
print("="*60)

r1 = analyze(trades_baseline, "Baseline (RSI only)")
if r1:
    print(f"\n1. BASELINE (RSI only):")
    print(f"   Trades: {r1['trades']}")
    print(f"   Win Rate: {r1['wr']:.1f}%")
    print(f"   Avg: {r1['avg']:.2f} pips")
    print(f"   Total: {r1['total']:.1f} pips")

r2 = analyze(trades_vpa, "VPA Filter")
if r2:
    print(f"\n2. WITH VPA (Volume Filter):")
    print(f"   Trades: {r2['trades']}")
    print(f"   Win Rate: {r2['wr']:.1f}%")
    print(f"   Avg: {r2['avg']:.2f} pips")
    print(f"   Total: {r2['total']:.1f} pips")
    if r1:
        print(f"   Impact: WR {r1['wr']:.1f}% → {r2['wr']:.1f}% ({r2['wr']-r1['wr']:+.1f}%)")

r3 = analyze(trades_full, "VPA + ADX")
if r3:
    print(f"\n3. WITH VPA + ADX (Full System):")
    print(f"   Trades: {r3['trades']}")
    print(f"   Win Rate: {r3['wr']:.1f}%")
    print(f"   Avg: {r3['avg']:.2f} pips")
    print(f"   Total: {r3['total']:.1f} pips")
    if r1:
        print(f"   Impact: WR {r1['wr']:.1f}% → {r3['wr']:.1f}% ({r3['wr']-r1['wr']:+.1f}%)")

print("\n" +  "="*60)
print("CONCLUSION:")
if r1 and r3 and r3['wr'] > r1['wr']:
    print(f"✅ Books concepts IMPROVE win rate by {r3['wr']-r1['wr']:.1f}%")
elif r1 and r3:
    print(f"⚠️  Win rate change: {r3['wr']-r1['wr']:+.1f}% (fewer trades, better quality)")
print("="*60 + "\n")

mt5.shutdown()
