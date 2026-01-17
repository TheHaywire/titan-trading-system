import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def audit_positions():
    if not mt5.initialize():
        print("MT5 failed")
        return

    positions = mt5.positions_get()
    if not positions:
        print("No open positions.")
        return

    df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
    
    # Add human readable time
    df['time_str'] = df['time'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
    
    # Select key columns
    cols = ['ticket', 'symbol', 'type', 'volume', 'price_open', 'price_current', 'sl', 'tp', 'profit', 'magic', 'comment', 'time_str']
    print(df[cols].to_string())
    
    mt5.shutdown()

if __name__ == "__main__":
    audit_positions()
