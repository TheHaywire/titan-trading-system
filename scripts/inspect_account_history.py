
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

if not mt5.initialize():
    print("Init failed")
    quit()

# Get history for last 24 hours
from_date = datetime.now() - timedelta(hours=24)
history = mt5.history_deals_get(from_date, datetime.now())

if history:
    df = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Filter for User's Manual Trades (usually different Magic number or no expert ID)
    # Print recent profitable trades
    print("\n🔍 RECENT TRADING ACTIVITY (Use vs Bot)")
    print("=" * 60)
    print(f"{'TIME':<20} {'SYMBOL':<10} {'TYPE':<5} {'VOL':<5} {'PROFIT':<8} {'COMMENT'}")
    print("-" * 60)
    
    total_profit = 0.0
    for deal in history:
        # Deal Types: 0=Buy, 1=Sell
        type_str = "BUY" if deal.type == 0 else "SELL" if deal.type == 1 else str(deal.type)
        if deal.profit != 0:
            print(f"{datetime.fromtimestamp(deal.time)} {deal.symbol:<10} {type_str:<5} {deal.volume:<5} {deal.profit:<8.2f} {deal.comment}")
            total_profit += deal.profit
            
    print("=" * 60)
    print(f"💰 TOTAL PROFIT/LOSS (Last 24h): ${total_profit:.2f}")

else:
    print("No history found")

mt5.shutdown()
