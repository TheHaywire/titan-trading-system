"""
Deep Institutional Analysis: Asset Class Performance Patterns
Analyzes mining results by asset class to identify systematic edges.
"""

import pandas as pd
import numpy as np

# Load combined results
df = pd.read_csv('strategy_mining/results/ALL_BATCHES_COMBINED.csv')

print("=" * 100)
print("INSTITUTIONAL ASSET CLASS ANALYSIS")
print("=" * 100)

# Define asset classes (simplified classification)
def classify_asset(symbol):
    """Classify symbol into asset class."""
    symbol = symbol.upper()
    
    # Forex pairs
    forex_majors = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
    forex_minors = ['EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY', 'EURAUD', 'EURNZD']
    forex_exotics = ['USDTRY', 'USDZAR', 'USDMXN', 'USDRUB', 'USDBRL']
    
    # Indices
    indices = ['US100', 'US30', 'US500', 'GER40', 'UK100', 'JPN225', 'AUS200', 'FRA40', 'ESP35']
    
    # Commodities
    commodities = ['GOLD', 'XAUUSD', 'SILVER', 'XAGUSD', 'OIL', 'BRENT', 'NATGAS']
    
    # Crypto
    crypto = ['BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'BCHUSD']
    
    # Check each category
    for major in forex_majors:
        if major in symbol:
            return 'Forex Major'
    
    for minor in forex_minors:
        if minor in symbol:
            return 'Forex Minor'
    
    for exotic in forex_exotics:
        if exotic in symbol:
            return 'Forex Exotic'
    
    for idx in indices:
        if idx in symbol:
            return 'Index'
    
    for comm in commodities:
        if comm in symbol:
            return 'Commodity'
    
    for cry in crypto:
        if cry in symbol:
            return 'Crypto'
    
    # Check if it contains currency pairs
    if any(curr in symbol for curr in ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'NZD']):
        if len([c for c in ['USD', 'EUR', 'GBP', 'JPY'] if c in symbol]) >= 2:
            return 'Forex Other'
    
    # Default to Stock
    return 'Stock'

# Classify all symbols
df['asset_class'] = df['symbol'].apply(classify_asset)

print("\n" + "=" * 100)
print("ASSET CLASS DISTRIBUTION")
print("=" * 100)

for asset_class in df['asset_class'].value_counts().index:
    count = len(df[df['asset_class'] == asset_class])
    symbols_count = df[df['asset_class'] == asset_class]['symbol'].nunique()
    pct = count / len(df) * 100
    print(f"{asset_class:20s}: {count:5,} strategies ({pct:5.1f}%) - {symbols_count} symbols")

print("\n" + "=" * 100)
print("PERFORMANCE BY ASSET CLASS")
print("=" * 100)

for asset_class in df['asset_class'].value_counts().index:
    subset = df[df['asset_class'] == asset_class]
    
    avg_pf = subset['profit_factor'].mean()
    avg_wr = subset['win_rate'].mean()
    avg_sharpe = subset['sharpe_ratio'].mean()
    perfect_rob = (subset['oos_profitable_windows'] == 5).sum()
    
    print(f"\n{asset_class}:")
    print(f"  Average Profit Factor: {avg_pf:.2f}")
    print(f"  Average Win Rate: {avg_wr:.1%}")
    print(f"  Average Sharpe: {avg_sharpe:.2f}")
    print(f"  Perfect Robustness (5/5): {perfect_rob} strategies")

print("\n" + "=" * 100)
print("BEST STRATEGY TYPE PER ASSET CLASS")
print("=" * 100)

for asset_class in df['asset_class'].value_counts().index:
    subset = df[df['asset_class'] == asset_class]
    
    print(f"\n{asset_class}:")
    for strategy in subset['strategy'].value_counts().head(3).index:
        strat_subset = subset[subset['strategy'] == strategy]
        count = len(strat_subset)
        avg_pf = strat_subset['profit_factor'].mean()
        print(f"  {strategy:25s}: {count:4,} strategies (Avg PF: {avg_pf:.2f})")

print("\n" + "=" * 100)
print("BEST TIMEFRAME PER ASSET CLASS")
print("=" * 100)

for asset_class in df['asset_class'].value_counts().index:
    subset = df[df['asset_class'] == asset_class]
    
    print(f"\n{asset_class}:")
    for tf in subset['timeframe'].value_counts().head(3).index:
        tf_subset = subset[subset['timeframe'] == tf]
        count = len(tf_subset)
        avg_pf = tf_subset['profit_factor'].mean()
        print(f"  {tf:5s}: {count:4,} strategies (Avg PF: {avg_pf:.2f})")

print("\n" + "=" * 100)
print("TOP 5 PERFORMERS PER MAJOR ASSET CLASS")
print("=" * 100)

major_classes = ['Forex Major', 'Forex Exotic', 'Stock', 'Index', 'Commodity', 'Crypto']

for asset_class in major_classes:
    subset = df[df['asset_class'] == asset_class]
    if len(subset) == 0:
        continue
    
    print(f"\n{asset_class}:")
    print("-" * 100)
    
    top5 = subset.nlargest(5, 'profit_factor')
    for idx, row in top5.iterrows():
        print(f"  {row['symbol']:20s} {row['timeframe']:5s} {row['strategy']:20s} "
              f"PF:{row['profit_factor']:6.2f} WR:{row['win_rate']*100:5.1f}% "
              f"Robust:{int(row['oos_profitable_windows'])}/5")

print("\n" + "=" * 100)
print("KEY INSIGHTS & PATTERNS")
print("=" * 100)

# Insight 1: Which asset class has highest avg PF?
best_class = df.groupby('asset_class')['profit_factor'].mean().idxmax()
best_pf = df.groupby('asset_class')['profit_factor'].mean().max()
print(f"\n1. BEST ASSET CLASS: {best_class} (Avg PF: {best_pf:.2f})")

# Insight 2: Which strategy type dominates?
best_strategy = df.groupby('strategy')['profit_factor'].mean().idxmax()
best_strat_pf = df.groupby('strategy')['profit_factor'].mean().max()
print(f"2. BEST STRATEGY TYPE: {best_strategy} (Avg PF: {best_strat_pf:.2f})")

# Insight 3: Which timeframe is most profitable?
best_tf = df.groupby('timeframe')['profit_factor'].mean().idxmax()
best_tf_pf = df.groupby('timeframe')['profit_factor'].mean().max()
print(f"3. BEST TIMEFRAME: {best_tf} (Avg PF: {best_tf_pf:.2f})")

# Insight 4: Mean Reversion vs Trend Following by asset class
print("\n4. MEAN REVERSION VS TREND FOLLOWING:")
for asset_class in ['Forex Major', 'Stock', 'Index']:
    subset = df[df['asset_class'] == asset_class]
    if len(subset) == 0:
        continue
    
    mr = subset[subset['strategy'] == 'MeanReversion']
    tf_strat = subset[subset['strategy'] == 'TrendFollowing']
    
    if len(mr) > 0 and len(tf_strat) > 0:
        mr_pf = mr['profit_factor'].mean()
        tf_pf = tf_strat['profit_factor'].mean()
        winner = "Mean Reversion" if mr_pf > tf_pf else "Trend Following"
        print(f"   {asset_class:20s}: {winner} wins (MR:{mr_pf:.2f} vs TF:{tf_pf:.2f})")

print("\n" + "=" * 100)
print("PORTFOLIO RECOMMENDATIONS")
print("=" * 100)

print("\nDIVERSIFIED PORTFOLIO BLUEPRINT:")
print("\nBased on the analysis, here's an optimal 10-strategy portfolio:")

portfolio_blueprint = []
for asset_class in ['Forex Exotic', 'Forex Major', 'Stock', 'Index', 'Commodity']:
    subset = df[df['asset_class'] == asset_class]
    if len(subset) > 0:
        top = subset.nlargest(2, 'profit_factor').head(2)
        for idx, row in top.iterrows():
            portfolio_blueprint.append({
                'Asset Class': asset_class,
                'Symbol': row['symbol'],
                'Timeframe': row['timeframe'],
                'Strategy': row['strategy'],
                'PF': row['profit_factor'],
                'WR': row['win_rate']
            })

for i, strat in enumerate(portfolio_blueprint[:10], 1):
    print(f"\n{i:2d}. [{strat['Asset Class']:15s}] {strat['Symbol']:15s} {strat['Timeframe']:5s} "
          f"{strat['Strategy']:20s} PF:{strat['PF']:6.2f} WR:{strat['WR']*100:5.1f}%")

print("\n✅ Analysis complete!")
