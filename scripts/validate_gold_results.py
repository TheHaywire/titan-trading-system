"""
CRITICAL VALIDATION OF GOLD RESULTS
====================================
Applies professional statistical standards.
"""

import pandas as pd
import numpy as np
from scipy import stats

# Load results
df = pd.read_csv('gold_strategy_results_20260106_015703.csv')

print("="*80)
print("CRITICAL VALIDATION - PROFESSIONAL STANDARDS")
print("="*80)
print()

# Filter significant
sig = df[(df['p_value'] < 0.05) & (df['total_trades'] >= 10)]

print(f"Results passing p<0.05 and trades>=10: {len(sig)}")
print()

# Apply PROFESSIONAL standards
MINIMUM_TRADES = 30  # Industry standard
MINIMUM_SHARPE = 1.5  # Conservative threshold
MINIMUM_WIN_RATE = 0.40  # At least 40%
MAX_DRAWDOWN_LIMIT = 20  # Max 20% DD

print("APPLYING PROFESSIONAL FILTERS:")
print(f"1. Minimum trades: {MINIMUM_TRADES}")
print(f"2. Minimum Sharpe: {MINIMUM_SHARPE}")
print(f"3. Minimum win rate: {MINIMUM_WIN_RATE*100}%")
print(f"4. Max drawdown: {MAX_DRAWDOWN_LIMIT}%")
print()

# Apply filters
professional = sig[
    (sig['total_trades'] >= MINIMUM_TRADES) &
    (sig['sharpe_ratio'] >= MINIMUM_SHARPE) &
    (sig['win_rate'] >= MINIMUM_WIN_RATE) &
    (sig['max_drawdown_pct'] <= MAX_DRAWDOWN_LIMIT)
]

print(f"Results passing PROFESSIONAL standards: {len(professional)}")
print()

if len(professional) > 0:
    print("QUALIFIED STRATEGIES:")
    print("-"*80)
    for i, row in professional.iterrows():
        print(f"\n{row['strategy']} ({row['timeframe']})")
        print(f"  Sharpe: {row['sharpe_ratio']:.2f}")
        print(f"  Win Rate: {row['win_rate']*100:.1f}%")
        print(f"  Trades: {int(row['total_trades'])}")
        print(f"  Return: {row['total_return_pct']:+.1f}%")
        print(f"  Max DD: {row['max_drawdown_pct']:.1f}%")
else:
    print("❌ NO STRATEGIES MEET PROFESSIONAL STANDARDS!")
    print()
    print("ANALYSIS OF FAILURES:")
    print("-"*80)
    
    # Why did they fail?
    not_enough_trades = sig[sig['total_trades'] < MINIMUM_TRADES]
    print(f"\n1. Insufficient trades (< {MINIMUM_TRADES}): {len(not_enough_trades)} strategies")
    if len(not_enough_trades) > 0:
        print("   Top by Sharpe (but too few trades):")
        for i, row in not_enough_trades.nlargest(5, 'sharpe_ratio').iterrows():
            print(f"   - {row['strategy']} ({row['timeframe']}): {int(row['total_trades'])} trades, Sharpe {row['sharpe_ratio']:.2f}")
    
    low_sharpe = sig[
        (sig['total_trades'] >= MINIMUM_TRADES) & 
        (sig['sharpe_ratio'] < MINIMUM_SHARPE)
    ]
    print(f"\n2. Low Sharpe (< {MINIMUM_SHARPE}): {len(low_sharpe)} strategies")
    
    high_dd = sig[
        (sig['total_trades'] >= MINIMUM_TRADES) &
        (sig['max_drawdown_pct'] > MAX_DRAWDOWN_LIMIT)
    ]
    print(f"\n3. High drawdown (> {MAX_DRAWDOWN_LIMIT}%): {len(high_dd)} strategies")

print()
print("="*80)
print("RECOMMENDATIONS:")
print("="*80)

if len(professional) == 0:
    print("""
❌ FINDING: No strategies meet professional standards on GOLD (6-month data)

POSSIBLE REASONS:
1. 6 months is insufficient for H4 strategies (need 1-2 years)
2. GOLD requires parameter optimization
3. GOLD may need more sophisticated strategies
4. Sample size too small for reliable statistics

NEXT STEPS:
1. Extend backtest period to 12-24 months
2. Lower trade frequency requirement (accept 20+ trades)
3. Test with optimized parameters
4. Consider walk-forward analysis
5. Add more aggressive strategies for GOLD's volatility

⚠️  DO NOT TRADE the "winners" - insufficient sample size!
    """)
else:
    print(f"✅ {len(professional)} strategies are VALIDATED and safe to trade")

print("="*80)
