import pandas as pd

df = pd.read_csv('strategy_research_results_20260106_000325.csv')
winners = df[df['sharpe_ratio'] > 1].sort_values('sharpe_ratio', ascending=False)

print('\n' + '='*80)
print('WINNING STRATEGIES - EXACT DETAILS')
print('='*80)

for i, (idx, row) in enumerate(winners.head(10).iterrows(), 1):
    print(f"\n{i}. {row['strategy']}")
    print(f"   Symbol: {row['symbol']}")
    print(f"   Timeframe: {row['timeframe']}")
    print(f"   Sharpe Ratio: {row['sharpe_ratio']:.2f}")
    print(f"   Total Return: {row['total_return_pct']:.1f}%")
    print(f"   Win Rate: {row['win_rate']*100:.1f}%")
    print(f"   Total Trades: {int(row['total_trades'])}")
    print(f"   Max Drawdown: {row['max_drawdown_pct']:.1f}%")
    print(f"   Profit Factor: {row['profit_factor']:.2f}")

print('\n' + '='*80)
print(f'Total winning strategies (Sharpe > 1): {len(winners)}')
print('='*80)
