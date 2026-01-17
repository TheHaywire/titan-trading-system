import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

if not mt5.initialize():
    print("Failed")
    exit()

print("="*90)
print("🔍 FINDING YOUR WINNING PATTERN ($100k → $1.5M)")
print("="*90)

# Get last 7 days of history
start = datetime.now() - timedelta(days=7)
deals = mt5.history_deals_get(start, datetime.now())

if not deals:
    print("No deals found")
    exit()

# Convert to DataFrame
df = pd.DataFrame([{
    'time': datetime.fromtimestamp(d.time),
    'symbol': d.symbol,
    'type': 'BUY' if d.type == 0 else 'SELL',
    'volume': d.volume,
    'price': d.price,
    'profit': d.profit,
    'comment': d.comment
} for d in deals])

# Filter out deposits/withdrawals
df = df[df['profit'] != 0]

# Sort by time
df = df.sort_values('time')

# Calculate cumulative profit
df['cumulative'] = df['profit'].cumsum()

# Find the big winners
big_winners = df[df['profit'] > 10000].sort_values('profit', ascending=False)

print(f"\n💰 BIG WINNERS (>$10k):")
print("-"*90)
for _, trade in big_winners.head(20).iterrows():
    print(f"{trade['time'].strftime('%m/%d %H:%M')} | {trade['symbol']:<10} | {trade['type']:<4} | {trade['volume']:>6.2f} lots | ${trade['profit']:>10,.0f}")

# Analyze by symbol
symbol_profit = df.groupby('symbol')['profit'].agg(['sum', 'count', 'mean']).sort_values('sum', ascending=False)

print(f"\n📊 PROFIT BY SYMBOL:")
print("-"*90)
print(f"{'Symbol':<12} {'Total Profit':<15} {'Trade Count':<12} {'Avg/Trade'}")
print("-"*90)
for symbol, row in symbol_profit.head(10).iterrows():
    print(f"{symbol:<12} ${row['sum']:>13,.0f} {int(row['count']):>11} ${row['mean']:>10,.0f}")

# Find the pattern
print(f"\n🎯 PATTERN ANALYSIS:")
print("-"*90)

# What time of day?
df['hour'] = df['time'].dt.hour
hourly = df.groupby('hour')['profit'].sum().sort_values(ascending=False)
print(f"\nBest Hours (UTC):")
for hour, profit in hourly.head(5).items():
    if profit > 0:
        print(f"  {hour:02d}:00 - ${profit:,.0f}")

# What direction?
direction = df.groupby('type')['profit'].sum()
print(f"\nBest Direction:")
for dir, profit in direction.items():
    print(f"  {dir}: ${profit:,.0f}")

# Win rate
wins = len(df[df['profit'] > 0])
total = len(df)
print(f"\nWin Rate: {wins}/{total} = {wins/total*100:.1f}%")

# Average win vs loss
avg_win = df[df['profit'] > 0]['profit'].mean()
avg_loss = abs(df[df['profit'] < 0]['profit'].mean())
print(f"Avg Win: ${avg_win:,.0f}")
print(f"Avg Loss: ${avg_loss:,.0f}")
print(f"Win/Loss Ratio: {avg_win/avg_loss:.2f}:1")

mt5.shutdown()
