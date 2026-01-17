import pandas as pd

df = pd.read_csv('strategy_mining/results/batch_1_results.csv')

print("=" * 80)
print("BATCH 1 MINING RESULTS - COMPREHENSIVE ANALYSIS")
print("=" * 80)

print(f"\nTotal Robust Strategies Found: {len(df)}")
print(f"Unique Symbols Analyzed: {df['symbol'].nunique()}")
print(f"\nSymbol List:\n{', '.join(sorted(df['symbol'].unique()))}")

print("\n" + "=" * 80)
print("STRATEGY TYPE BREAKDOWN:")
print("=" * 80)
print(df['strategy'].value_counts())

print("\n" + "=" * 80)
print("TIMEFRAME DISTRIBUTION:")
print("=" * 80)
print(df['timeframe'].value_counts())

print("\n" + "=" * 80)
print("TOP 15 BEST STRATEGIES (BY PROFIT FACTOR):")
print("=" * 80)
top15 = df.nlargest(15, 'profit_factor')[['symbol', 'timeframe', 'strategy', 'params', 'profit_factor', 'win_rate', 'sharpe_ratio', 'oos_profitable_windows']]
print(top15.to_string(index=False))

print("\n" + "=" * 80)
print("HIGHEST WIN RATE STRATEGIES:")
print("=" * 80)
top_wr = df.nlargest(10, 'win_rate')[['symbol', 'timeframe', 'strategy', 'win_rate', 'profit_factor', 'num_trades']]
print(top_wr.to_string(index=False))

print("\n" + "=" * 80)
print("STATISTICS:")
print("=" * 80)
print(f"Average Profit Factor: {df['profit_factor'].mean():.2f}")
print(f"Average Win Rate: {df['win_rate'].mean():.1%}")
print(f"Average Sharpe Ratio: {df['sharpe_ratio'].mean():.2f}")
print(f"Strategies with 5/5 OOS Windows: {(df['oos_profitable_windows'] == 5).sum()}")
print(f"Strategies with 4/5 OOS Windows: {(df['oos_profitable_windows'] == 4).sum()}")
