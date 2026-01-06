import pandas as pd

df = pd.read_csv('gold_strategy_results_20260106_015703.csv')

# Professional standards
MIN_TRADES = 30
MIN_SHARPE = 1.5
MIN_WIN = 0.40
MAX_DD = 20

print("="*70)
print("CRITICAL VALIDATION - PROFESSIONAL STANDARDS")
print("="*70)
print()

sig = df[(df['p_value'] < 0.05) & (df['total_trades'] >= 10)]
print(f"Results with p<0.05 and 10+ trades: {len(sig)}")

# Apply professional filter
prof = sig[(sig['total_trades'] >= MIN_TRADES) & 
           (sig['sharpe_ratio'] >= MIN_SHARPE) &
           (sig['win_rate'] >= MIN_WIN) &
           (sig['max_drawdown_pct'] <= MAX_DD)]

print(f"Meeting ALL professional standards (30+ trades): {len(prof)}")
print()

if len(prof) == 0:
    print("❌ NO STRATEGIES MEET PROFESSIONAL STANDARDS")
    print()
    print("REASON: Too few trades (< 30)")
    print()
    
    # Show what failed
    high_sharpe_low_trades = sig[(sig['sharpe_ratio'] > 1) & (sig['total_trades'] < MIN_TRADES)].sort_values('sharpe_ratio', ascending=False)
    
    print(f"High Sharpe BUT too few trades: {len(high_sharpe_low_trades)}")
    print()
    print("Top 5 (unreliable due to small sample):")
    for i, row in high_sharpe_low_trades.head(5).iterrows():
        print(f"  {row['strategy']:30s} {row['timeframe']:4s} | Sharpe:{row['sharpe_ratio']:6.2f} | Trades:{int(row['total_trades']):3d} ❌ TOO FEW")
else:
    print("✅ VALIDATED STRATEGIES:")
    for i, row in prof.iterrows():
        print(f"  {row['strategy']} ({row['timeframe']})")
        print(f"    Sharpe: {row['sharpe_ratio']:.2f} | Trades: {int(row['total_trades'])} | Win: {row['win_rate']*100:.1f}%")

print()
print("="*70)
print("VERDICT:")
print("="*70)
if len(prof) == 0:
    print("⚠️  6 MONTHS DATA IS INSUFFICIENT FOR H4 STRATEGIES")
    print("⚠️  NEED 12-24 MONTHS OR MORE ACTIVE STRATEGIES")
print("="*70)
