"""
Analyze Recent Closed Trades
============================
Look at trades from the last few hours and analyze what worked
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone

mt5.initialize()

# Get trades from last 12 hours
now = datetime.now(timezone.utc)
from_date = now - timedelta(hours=12)

# Get deal history
deals = mt5.history_deals_get(from_date, now)

if not deals or len(deals) == 0:
    print("No deals found in last 12 hours")
    mt5.shutdown()
    exit()

print("="*70)
print(f"YOUR RECENT TRADES (Last 12 hours)")
print("="*70)

# Convert to dataframe
df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())

# Filter only trade entries and exits (not balance operations)
df = df[df['type'].isin([0, 1])]  # 0=buy, 1=sell

# Group by position to get complete trades
positions = {}
for _, deal in df.iterrows():
    pos_id = deal['position_id']
    if pos_id not in positions:
        positions[pos_id] = {'deals': [], 'symbol': deal['symbol']}
    positions[pos_id]['deals'].append(deal)

# Analyze closed positions
closed_trades = []
for pos_id, data in positions.items():
    if len(data['deals']) >= 2:  # Entry and exit
        entry = data['deals'][0]
        exit_deal = data['deals'][-1]
        
        profit = sum(d['profit'] for d in data['deals'])
        volume = entry['volume']
        
        entry_time = datetime.fromtimestamp(entry['time'], tz=timezone.utc)
        exit_time = datetime.fromtimestamp(exit_deal['time'], tz=timezone.utc)
        duration = exit_time - entry_time
        
        closed_trades.append({
            'symbol': data['symbol'],
            'type': 'BUY' if entry['type'] == 0 else 'SELL',
            'volume': volume,
            'entry_price': entry['price'],
            'exit_price': exit_deal['price'],
            'profit': profit,
            'entry_time': entry_time,
            'duration': duration,
            'pips': abs(exit_deal['price'] - entry['price']) / mt5.symbol_info(data['symbol']).point if mt5.symbol_info(data['symbol']) else 0
        })

# Sort by time
closed_trades.sort(key=lambda x: x['entry_time'], reverse=True)

# Print recent trades
winners = 0
losers = 0
total_profit = 0
quick_trades = []

print(f"\nFound {len(closed_trades)} closed trades\n")

for trade in closed_trades[:20]:  # Last 20 trades
    emoji = "+" if trade['profit'] > 0 else "-"
    duration_str = str(trade['duration']).split('.')[0]  # Remove microseconds
    
    print(f"{emoji} {trade['symbol']} {trade['type']} {trade['volume']} lots")
    print(f"   Entry: {trade['entry_price']:.5f} at {trade['entry_time'].strftime('%H:%M')}")
    print(f"   Exit:  {trade['exit_price']:.5f} | Duration: {duration_str}")
    print(f"   P/L: ${trade['profit']:.2f} | Pips: {trade['pips']:.1f}")
    print()
    
    if trade['profit'] > 0:
        winners += 1
    else:
        losers += 1
    total_profit += trade['profit']
    
    # Quick scalps (under 30 minutes)
    if trade['duration'].total_seconds() < 1800:
        quick_trades.append(trade)

# Summary
print("="*70)
print("SUMMARY")
print("="*70)
print(f"Total Trades: {len(closed_trades)}")
print(f"Winners: {winners} | Losers: {losers}")
print(f"Win Rate: {winners/(winners+losers)*100:.1f}%" if (winners+losers) > 0 else "N/A")
print(f"Total P/L: ${total_profit:.2f}")

if quick_trades:
    print(f"\nQUICK SCALPS (under 30 mins): {len(quick_trades)}")
    quick_profit = sum(t['profit'] for t in quick_trades)
    print(f"Quick Trade P/L: ${quick_profit:.2f}")
    
    print("\nPATTERNS IN YOUR WINNING QUICK TRADES:")
    winning_quick = [t for t in quick_trades if t['profit'] > 0]
    if winning_quick:
        # Analyze patterns
        symbols = {}
        for t in winning_quick:
            if t['symbol'] not in symbols:
                symbols[t['symbol']] = {'count': 0, 'profit': 0}
            symbols[t['symbol']]['count'] += 1
            symbols[t['symbol']]['profit'] += t['profit']
        
        print("\nBest Symbols for Scalping:")
        for sym, data in sorted(symbols.items(), key=lambda x: x[1]['profit'], reverse=True):
            print(f"  {sym}: {data['count']} trades, ${data['profit']:.2f}")

mt5.shutdown()
