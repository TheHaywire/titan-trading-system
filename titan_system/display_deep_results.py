"""
Display Ultra Deep Analysis Results
"""
import pandas as pd
from pathlib import Path

# Load trades
df = pd.read_csv('trades_export_20251229.csv')
trades = df[df['Symbol'].notna() & (df['Symbol'] != '')].copy()
trades = trades[trades['P&L'] != 0].copy()
trades['DateTime'] = pd.to_datetime(trades['Date'] + ' ' + trades['Time'])
trades = trades.sort_values('DateTime').reset_index(drop=True)

print('='*80)
print('  TRADE SEQUENCE ANALYSIS')
print('='*80)

# What happens after wins vs losses
trades['PrevPnL'] = trades['P&L'].shift(1)
trades['PrevWin'] = trades['PrevPnL'] > 0

after_win = trades[trades['PrevWin'] == True]
after_loss = trades[trades['PrevWin'] == False]

print(f'\nAfter a WIN:')
if len(after_win) > 0:
    print(f'  Trades: {len(after_win)}')
    print(f'  Win Rate: {(after_win["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_win["P&L"].sum():,.0f}')

print(f'\nAfter a LOSS:')
if len(after_loss) > 0:
    print(f'  Trades: {len(after_loss)}')
    print(f'  Win Rate: {(after_loss["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_loss["P&L"].sum():,.0f}')

# After 2 wins in a row
trades['Prev2Win'] = (trades['PrevPnL'] > 0) & (trades['P&L'].shift(2) > 0)
after_2_wins = trades[trades['Prev2Win'] == True]

print(f'\nAfter 2 WINS in a row:')
if len(after_2_wins) > 0:
    print(f'  Trades: {len(after_2_wins)}')
    print(f'  Win Rate: {(after_2_wins["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_2_wins["P&L"].sum():,.0f}')

# After 2 losses in a row  
trades['Prev2Loss'] = (trades['PrevPnL'] < 0) & (trades['P&L'].shift(2) < 0)
after_2_losses = trades[trades['Prev2Loss'] == True]

print(f'\nAfter 2 LOSSES in a row:')
if len(after_2_losses) > 0:
    print(f'  Trades: {len(after_2_losses)}')
    print(f'  Win Rate: {(after_2_losses["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_2_losses["P&L"].sum():,.0f}')

# After big win (>$10K)
after_big_win = trades[trades['PrevPnL'] > 10000]
print(f'\nAfter a BIG WIN (>$10K):')
if len(after_big_win) > 0:
    print(f'  Trades: {len(after_big_win)}')
    print(f'  Win Rate: {(after_big_win["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_big_win["P&L"].sum():,.0f}')

# After big loss (<-$10K)
after_big_loss = trades[trades['PrevPnL'] < -10000]
print(f'\nAfter a BIG LOSS (<-$10K):')
if len(after_big_loss) > 0:
    print(f'  Trades: {len(after_big_loss)}')
    print(f'  Win Rate: {(after_big_loss["P&L"] > 0).mean()*100:.1f}%')
    print(f'  Net P&L: ${after_big_loss["P&L"].sum():,.0f}')

# Time between trades analysis
trades['TimeSincePrev'] = (trades['DateTime'] - trades['DateTime'].shift(1)).dt.total_seconds() / 60

print('\n' + '='*80)
print('  TIME BETWEEN TRADES ANALYSIS')
print('='*80)

for label, min_t, max_t in [('< 1 min', 0, 1), ('1-5 min', 1, 5), ('5-15 min', 5, 15), ('15-60 min', 15, 60), ('> 60 min', 60, 999999)]:
    subset = trades[(trades['TimeSincePrev'] >= min_t) & (trades['TimeSincePrev'] < max_t)]
    if len(subset) > 5:
        wr = (subset['P&L'] > 0).mean() * 100
        pnl = subset['P&L'].sum()
        print(f'{label:12}: {len(subset):>4} trades | WR: {wr:>5.1f}% | P&L: ${pnl:>12,.0f}')

print('\n' + '='*80)
print('  VOLUME/SIZE ANALYSIS')
print('='*80)

# Volume and PnL relationship
for symbol in ['GOLD', 'BTCUSD', 'SILVER']:
    sym = trades[trades['Symbol'] == symbol]
    if len(sym) > 10:
        print(f'\n{symbol}:')
        for label, min_v, max_v in [('Small', 0, 1), ('Medium', 1, 5), ('Large', 5, 10), ('XL', 10, 25), ('XXL', 25, 100)]:
            subset = sym[(sym['Quantity'] >= min_v) & (sym['Quantity'] < max_v)]
            if len(subset) > 0:
                wr = (subset['P&L'] > 0).mean() * 100
                pnl = subset['P&L'].sum()
                print(f'  {label:8} ({min_v}-{max_v} lots): {len(subset):>3} trades | WR: {wr:>5.1f}% | P&L: ${pnl:>12,.0f}')

print('\n' + '='*80)
print('  TRADE CLUSTERING (Sessions)')
print('='*80)

# Group trades into sessions (within 30 min of each other)
trades['NewSession'] = trades['TimeSincePrev'] > 30
trades['SessionId'] = trades['NewSession'].cumsum()

sessions = trades.groupby('SessionId').agg({
    'P&L': ['sum', 'count'],
    'DateTime': 'first'
})
sessions.columns = ['PnL', 'Trades', 'StartTime']
sessions['IsProfitable'] = sessions['PnL'] > 0

profitable = sessions[sessions['IsProfitable'] == True]
losing = sessions[sessions['IsProfitable'] == False]

print(f'\nTotal Sessions: {len(sessions)}')
print(f'Profitable Sessions: {len(profitable)} ({len(profitable)/len(sessions)*100:.1f}%)')
print(f'Losing Sessions: {len(losing)} ({len(losing)/len(sessions)*100:.1f}%)')

if len(profitable) > 0:
    print(f'\nProfitable Session Stats:')
    print(f'  Avg P&L: ${profitable["PnL"].mean():,.0f}')
    print(f'  Avg Trades: {profitable["Trades"].mean():.1f}')

if len(losing) > 0:
    print(f'\nLosing Session Stats:')
    print(f'  Avg P&L: ${losing["PnL"].mean():,.0f}')
    print(f'  Avg Trades: {losing["Trades"].mean():.1f}')

# Optimal session size
print(f'\nSession Size Analysis:')
for size in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
    subset = sessions[sessions['Trades'] == size]
    if len(subset) >= 3:
        win_pct = (subset['PnL'] > 0).mean() * 100
        avg_pnl = subset['PnL'].mean()
        print(f'  {size} trades/session: {len(subset)} sessions | Win%: {win_pct:.0f}% | Avg P&L: ${avg_pnl:,.0f}')

# Many trades in session (>10)
many = sessions[sessions['Trades'] > 10]
if len(many) > 0:
    print(f'  >10 trades/session: {len(many)} sessions | Win%: {(many["PnL"]>0).mean()*100:.0f}% | Avg P&L: ${many["PnL"].mean():,.0f}')

print('\n' + '='*80)
print('  DAY OF WEEK + HOUR HEAT MAP')
print('='*80)

trades['DayOfWeek'] = trades['DateTime'].dt.day_name()
trades['Hour'] = trades['DateTime'].dt.hour

# Best day/hour combos
day_hour = trades.groupby(['DayOfWeek', 'Hour']).agg({
    'P&L': ['sum', 'count']
})
day_hour.columns = ['PnL', 'Trades']
day_hour = day_hour[day_hour['Trades'] >= 5].sort_values('PnL', ascending=False)

print('\nBest Day/Hour Combos:')
for (day, hour), row in day_hour.head(5).iterrows():
    print(f'  {day} {hour}:00 UTC: {row["Trades"]:.0f} trades | P&L: ${row["PnL"]:,.0f}')

print('\nWorst Day/Hour Combos:')
for (day, hour), row in day_hour.tail(5).iterrows():
    print(f'  {day} {hour}:00 UTC: {row["Trades"]:.0f} trades | P&L: ${row["PnL"]:,.0f}')

print('\n' + '='*80)
print('  FINAL INSIGHTS')
print('='*80)
print('''
KEY FINDINGS:

1. SEQUENCE RULES:
   - What happens after consecutive losses?
   - What happens after big wins/losses?

2. TIMING RULES:
   - What's the optimal time between trades?
   - Which day/hour combos work best?

3. SESSION RULES:
   - What's the optimal session size?
   - When to stop trading in a session?

4. SIZE RULES:
   - What position size works best per symbol?
''')
