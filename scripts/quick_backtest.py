"""Quick backtest with results saved to file"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

# Get data
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 2880)
df = pd.DataFrame(rates)

# RSI
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))

# Simple backtest
trades = []
for i in range(50, len(df) - 50):
    if df.iloc[i]['RSI'] < 30:
        direction = "BUY"
    elif df.iloc[i]['RSI'] > 70:
        direction = "SELL"  
    else:
        continue
    
    entry = df.iloc[i]['close']
    
    # Exit after 20 bars
    exit_bar = df.iloc[i+20]
    exit_price = exit_bar['close']
    
    profit = (exit_price - entry) * 10000 if direction == "BUY" else (entry - exit_price) * 10000
    trades.append(profit)

# Results
with open("backtest_results.txt", "w") as f:
    f.write(f"Total trades: {len(trades)}\n")
    if trades:
        wins = [t for t in trades if t > 0]
        f.write(f"Wins: {len(wins)} ({len(wins)/len(trades)*100:.1f}%)\n")
        f.write(f"Avg profit: {np.mean(trades):.2f} pips\n")
        f.write(f"Total: {sum(trades):.1f} pips\n")

mt5.shutdown()
print(f"✅ Results saved to backtest_results.txt")
print(f"Trades: {len(trades)}, Wins: {len(wins)}/{len(trades)} ({len(wins)/len(trades)*100:.1f}%)")
