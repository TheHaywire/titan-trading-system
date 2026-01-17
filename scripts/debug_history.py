import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import json

def debug_history():
    if not mt5.initialize():
        print("MT5 Initialize failed")
        return

    acc = mt5.account_info()
    print(f"--- ACCOUNT INFO ---")
    print(f"Login: {acc.login}")
    print(f"Server: {acc.server}")
    print(f"Name: {acc.name}")
    print(f"Balance: {acc.balance}")
    print(f"Currency: {acc.currency}")
    print("-" * 20)

    # Get history for last 7 days
    from_date = datetime.now() - timedelta(days=7)
    deals = mt5.history_deals_get(from_date, datetime.now())
    
    if not deals:
        print("No history found for last 7 days.")
        mt5.shutdown()
        return

    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Deal Type Mapping
    # 0: DEAL_TYPE_BUY
    # 1: DEAL_TYPE_SELL
    # 2: DEAL_TYPE_BALANCE
    # 3: DEAL_TYPE_CREDIT
    # 4: DEAL_TYPE_CHARGE
    # 5: DEAL_TYPE_CORRECTION
    # 6: DEAL_TYPE_BONUS
    # 7: DEAL_TYPE_COMMISSION
    # ...
    
    print(f"\n--- DEAL SUMMARY (7 Days) ---")
    print(f"Total Deals: {len(df)}")
    
    type_counts = df['type'].value_counts().to_dict()
    print(f"Types Count: {type_counts}")
    
    magic_counts = df['magic'].value_counts().to_dict()
    print(f"Magic Numbers Count: {magic_counts}")
    
    # Analyze "Trades" only (0 and 1)
    trades_df = df[df['type'].isin([0, 1])]
    print(f"Actual Trades: {len(trades_df)}")
    
    # Filter for closing trades (entry == 1)
    exit_df = trades_df[trades_df['entry'] == 1]
    print(f"Closing Trades: {len(exit_df)}")
    
    print("\n--- LATEST 10 CLOSING TRADES ---")
    cols = ['time', 'symbol', 'type', 'magic', 'volume', 'price', 'profit', 'comment']
    # Limit comment length for readability
    exit_df_disp = exit_df[cols].tail(10).copy()
    exit_df_disp['comment'] = exit_df_disp['comment'].apply(lambda x: str(x)[:20] + "..." if len(str(x)) > 20 else str(x))
    print(exit_df_disp.to_string(index=False))

    mt5.shutdown()

if __name__ == "__main__":
    debug_history()
