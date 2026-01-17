import pandas as pd

df = pd.read_csv('strategy_mining/results/ALL_BATCHES_COMBINED.csv')

print("=" * 100)
print("MINING ANALYSIS - 3 BATCHES COMPLETE")
print("=" * 100)

total = len(df)
symbols = df['symbol'].nunique()

print(f"\nTOTAL ROBUST STRATEGIES: {total:,}")
print(f"UNIQUE SYMBOLS ANALYZED: {symbols}")
print(f"Average Profit Factor: {df['profit_factor'].mean():.2f}")
print(f"Average Win Rate: {df['win_rate'].mean():.1%}")

perfect = (df['oos_profitable_windows'] == 5).sum()
high = (df['oos_profitable_windows'] == 4).sum()

print(f"\nPERFECT ROBUSTNESS (5/5 windows): {perfect:,}")
print(f"HIGH ROBUSTNESS (4/5 windows): {high:,}")

print("\n" + "=" * 100)
print("TOP 20 STRATEGIES")
print("=" * 100)

top20 = df.nlargest(20, 'profit_factor')
for idx, row in top20.iterrows():
    pf = row['profit_factor']
    wr = row['win_rate'] * 100
    oos = int(row['oos_profitable_windows'])
    print(f"{row['symbol']:20s} {row['timeframe']:5s} {row['strategy']:20s} PF:{pf:6.2f} WR:{wr:5.1f}% Robust:{oos}/5")

print("\n" + "=" * 100)
print("STRATEGY BREAKDOWN")
print("=" * 100)
for strat, count in df['strategy'].value_counts().items():
    pct = count / total * 100
    avg_pf = df[df['strategy']==strat]['profit_factor'].mean()
    print(f"{strat:25s}: {count:5,} ({pct:5.1f}%) - Avg PF: {avg_pf:.2f}")

print("\n✅ Full results saved to: ALL_BATCHES_COMBINED.csv")
