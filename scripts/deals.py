"""Detailed breakdown of recent trades"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta, timezone

mt5.initialize()

now = datetime.now(timezone.utc)
from_date = now - timedelta(hours=24)

deals = mt5.history_deals_get(from_date, now)

if not deals:
    print("No deals")
    mt5.shutdown()
    exit()

print("ALL DEALS (Last 24h)")
print("="*60)

# Group by position
positions = {}
for deal in deals:
    d = deal._asdict()
    if d['type'] in [0, 1]:  # Buy/Sell only
        pos_id = d['position_id']
        if pos_id not in positions:
            positions[pos_id] = []
        positions[pos_id].append(d)

for pos_id, deals_list in sorted(positions.items(), key=lambda x: x[1][0]['time'], reverse=True):
    if len(deals_list) < 1:
        continue
    
    entry = deals_list[0]
    total_profit = sum(d['profit'] for d in deals_list)
    symbol = entry['symbol']
    direction = "BUY" if entry['type'] == 0 else "SELL"
    volume = entry['volume']
    entry_time = datetime.fromtimestamp(entry['time'], tz=timezone.utc)
    
    emoji = "WIN" if total_profit > 0 else "LOSS"
    
    if len(deals_list) > 1:
        exit_deal = deals_list[-1]
        exit_time = datetime.fromtimestamp(exit_deal['time'], tz=timezone.utc)
        duration = exit_time - entry_time
        status = "CLOSED"
    else:
        duration = "OPEN"
        status = "OPEN"
    
    print(f"\n[{emoji}] {symbol} {direction} {volume} lots")
    print(f"   Entry: {entry['price']:.5f} at {entry_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   P/L: ${total_profit:.2f} | Status: {status}")
    print(f"   Duration: {duration}")
    print(f"   Comment: {entry['comment']}")

mt5.shutdown()
