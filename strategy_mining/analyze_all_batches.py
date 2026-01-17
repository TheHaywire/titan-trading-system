import pandas as pd
import glob

print("=" * 100)
print("COMPREHENSIVE MINING ANALYSIS - ALL BATCHES")
print("=" * 100)

# Load all batch results
batch_files = glob.glob('strategy_mining/results/batch_*.csv')
batch_files.sort()

all_batches = []
for file in batch_files:
    batch_num = file.split('_')[1].split('.')[0]
    df = pd.read_csv(file)
    all_batches.append(df)
    print(f"\nBatch {batch_num}: {len(df)} strategies, {df['symbol'].nunique()} symbols")

# Combine all batches
combined = pd.concat(all_batches, ignore_index=True)

print("\n" + "=" * 100)
print("OVERALL STATISTICS")
print("=" * 100)
print(f"Total Robust Strategies Found: {len(combined):,}")
print(f"Unique Symbols Analyzed: {combined['symbol'].nunique()}")
print(f"Average Profit Factor: {combined['profit_factor'].mean():.2f}")
print(f"Average Win Rate: {combined['win_rate'].mean():.1%}")
print(f"Average Sharpe Ratio: {combined['sharpe_ratio'].mean():.2f}")
print(f"Strategies with 5/5 OOS Windows: {(combined['oos_profitable_windows'] == 5).sum():,}")
print(f"Strategies with 4/5 OOS Windows: {(combined['oos_profitable_windows'] == 4).sum():,}")

print("\n" + "=" * 100)
print("TOP 20 STRATEGIES BY PROFIT FACTOR")
print("=" * 100)
top20 = combined.nlargest(20, 'profit_factor')[['symbol', 'timeframe', 'strategy', 'params', 'profit_factor', 'win_rate', 'sharpe_ratio', 'oos_profitable_windows']]
print(top20.to_string(index=False))

print("\n" + "=" * 100)
print("STRATEGY TYPE BREAKDOWN")
print("=" * 100)
print(combined['strategy'].value_counts())

print("\n" + "=" * 100)
print("TIMEFRAME DISTRIBUTION")
print("=" * 100)
print(combined['timeframe'].value_counts())

print("\n" + "=" * 100)
print("TOP 10 SYMBOLS BY STRATEGY COUNT")
print("=" * 100)
symbol_counts = combined['symbol'].value_counts().head(10)
for symbol, count in symbol_counts.items():
    avg_pf = combined[combined['symbol']==symbol]['profit_factor'].mean()
    print(f"{symbol}: {count} strategies (Avg PF: {avg_pf:.2f})")

print("\n" + "=" * 100)
print("PERFECT ROBUSTNESS (5/5 OOS Windows)")
print("=" * 100)
perfect = combined[combined['oos_profitable_windows'] == 5].nlargest(15, 'profit_factor')
print(perfect[['symbol', 'timeframe', 'strategy', 'profit_factor', 'win_rate']].to_string(index=False))

# Save combined results
combined.to_csv('strategy_mining/results/ALL_BATCHES_COMBINED.csv', index=False)
print("\n" + "=" * 100)
print(f"✅ COMBINED RESULTS SAVED: ALL_BATCHES_COMBINED.csv ({len(combined):,} strategies)")
print("=" * 100)
