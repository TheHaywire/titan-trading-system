import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

def inspect_history():
    if not mt5.initialize():
        print("MT5 failed")
        return

    # Look at last 4 hours
    from_date = datetime.now() - timedelta(hours=4)
    to_date = datetime.now() + timedelta(hours=1)
    
    deals = mt5.history_deals_get(from_date, to_date)
    if not deals:
        print("No deals found.")
        return

    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time_str'] = df['time'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    
    # Filter for GOLD and non-zero volume
    df_gold = df[df['symbol'].str.contains('GOLD', na=False)]
    
    cols = ['ticket', 'symbol', 'type', 'entry', 'volume', 'price', 'profit', 'magic', 'comment', 'time_str']
    print(df_gold[cols].to_string())
    
    mt5.shutdown()

if __name__ == "__main__":
    inspect_history()
