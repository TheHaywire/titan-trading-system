"""
Analyze your recent GOLD trades and what setup you captured
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone

mt5.initialize()

# Look at last 2 hours for your manual GOLD trades
now = datetime.now(timezone.utc)
from_date = now - timedelta(hours=2)

deals = mt5.history_deals_get(from_date, now)

print("YOUR GOLD TRADES (Last 2 hours)")
print("="*60)

gold_trades = []
for deal in deals:
    d = deal._asdict()
    if 'GOLD' in d['symbol'] or 'XAU' in d['symbol']:
        if d['type'] in [0, 1]:  # Buy/Sell
            entry_time = datetime.fromtimestamp(d['time'], tz=timezone.utc)
            gold_trades.append({
                'time': entry_time,
                'type': 'BUY' if d['type'] == 0 else 'SELL',
                'price': d['price'],
                'volume': d['volume'],
                'profit': d['profit'],
                'comment': d['comment']
            })

# Sort by time
gold_trades.sort(key=lambda x: x['time'], reverse=True)

for t in gold_trades:
    print(f"\n{t['type']} {t['volume']} lots @ {t['price']}")
    print(f"  Time: {t['time'].strftime('%H:%M:%S')} UTC ({(t['time'] + timedelta(hours=5, minutes=30)).strftime('%H:%M:%S')} IST)")
    print(f"  P/L: ${t['profit']:.2f}")
    print(f"  Comment: {t['comment']}")

# Now analyze what the market looked like at those entry points
print("\n" + "="*60)
print("TECHNICAL ANALYSIS AT YOUR ENTRY POINTS")
print("="*60)

# Get GOLD M1 and M5 data to see what you saw
gold_m5 = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M5, 0, 100)
gold_m1 = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M1, 0, 100)

if gold_m5 is not None:
    df = pd.DataFrame(gold_m5)
    df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
    
    # Calculate what you might have seen
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    # Recent price action
    recent = df.tail(20)
    
    print("\nCurrent GOLD Market State (M5):")
    print(f"  Price: {df.iloc[-1]['close']}")
    print(f"  EMA9: {df.iloc[-1]['EMA9']:.2f}")
    print(f"  EMA21: {df.iloc[-1]['EMA21']:.2f}")
    print(f"  RSI: {df.iloc[-1]['RSI']:.1f}")
    
    trend = "BULLISH" if df.iloc[-1]['EMA9'] > df.iloc[-1]['EMA21'] else "BEARISH"
    print(f"  Trend: {trend}")
    
    # Price range
    high_20 = recent['high'].max()
    low_20 = recent['low'].min()
    range_size = high_20 - low_20
    print(f"\n  Last 20 bars range: {low_20:.2f} - {high_20:.2f} (${range_size:.2f})")
    
    # What setup could have worked
    print("\n" + "="*60)
    print("WHAT SETUP DID YOU USE?")
    print("="*60)
    print("""
Based on your trades, you likely:
1. Saw a DIRECTION (trend or breakout)
2. Entered with SIZE (5-20 lots = conviction)
3. Exited quickly (30 mins to 2 hours)

CAN THE BOT DO THIS? YES, but needs:
- Faster timeframe (M1/M5 instead of M15)
- Larger position sizes
- Scalp-style exits (trail or quick TP)
- GOLD-focused instead of multi-symbol
""")

mt5.shutdown()
