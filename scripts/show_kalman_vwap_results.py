"""Quick script to display Kalman/VWAP backtest results."""
import pandas as pd

df = pd.read_csv('data/kalman_vwap_backtest_results.csv')
df_sorted = df.sort_values('expectancy_r', ascending=False)

print('=' * 90)
print('KALMAN FILTER & VWAP BACKTEST RESULTS - TOP 15 BY EXPECTANCY')
print('=' * 90)
print()
for _, row in df_sorted.head(15).iterrows():
    sig = '*** EDGE ***' if row['is_significant'] else ''
    print(f"{row['strategy']:8s} {row['symbol']:12s} {row['timeframe']:4s} ({row['params']}) | "
          f"Trades: {row['total_trades']:4.0f} | Win: {row['win_rate']*100:5.1f}% | "
          f"Exp: {row['expectancy_r']:+.3f}R | PF: {row['profit_factor']:.2f} | p={row['p_value']:.4f} {sig}")

print()
print('=' * 90)
print('STATISTICALLY SIGNIFICANT EDGES (p<0.05, positive expectancy)')
print('=' * 90)
sig_df = df[df['is_significant'] == True]
if len(sig_df) > 0:
    for _, row in sig_df.sort_values('expectancy_r', ascending=False).iterrows():
        print(f"{row['strategy']:8s} {row['symbol']:12s} {row['timeframe']:4s} ({row['params']}) | "
              f"Trades: {row['total_trades']:.0f} | Win: {row['win_rate']*100:.1f}% | "
              f"Exp: {row['expectancy_r']:+.3f}R | p={row['p_value']:.4f}")
else:
    print('No statistically significant edges found.')
