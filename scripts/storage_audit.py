import MetaTrader5 as mt5
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
from rich.console import Console

console = Console()

def audit_storage():
    if not mt5.initialize():
        return
    
    # MT5 History (Last 5 Days)
    from_date = datetime.now() - timedelta(days=5)
    history_deals = mt5.history_deals_get(from_date, datetime.now())
    mt5.shutdown()
    
    if history_deals:
        mt5_df = pd.DataFrame(list(history_deals), columns=history_deals[0]._asdict().keys())
        mt5_df = mt5_df[mt5_df['entry'] != 0] # Exclude entries
        mt5_count = len(mt5_df)
    else:
        mt5_count = 0
        
    # SQLite History
    try:
        conn = sqlite3.connect('data/titan.db')
        # Check both tables
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trades'")
        has_trades_table = cursor.fetchone() is not None
        
        if has_trades_table:
            db_df = pd.read_sql_query('SELECT * FROM trades', conn)
            db_count = len(db_df)
            last_db_trade = db_df.iloc[-1]['open_time'] if not db_df.empty else "Empty"
        else:
            db_df = pd.read_sql_query('SELECT * FROM trade_history', conn)
            db_count = len(db_df)
            last_db_trade = db_df.iloc[-1]['entry_time'] if not db_df.empty else "Empty"
            
        conn.close()
    except Exception as e:
        db_count = -1
        last_db_trade = str(e)

    # CSV History
    try:
        csv_df = pd.read_csv('data/trade_history_full.csv')
        csv_count = len(csv_df)
        last_csv_trade = csv_df.iloc[-1]['Entry Time'] if not csv_df.empty else "N/A"
    except Exception as e:
        csv_count = -1
        last_csv_trade = str(e)

    console.print(f"[bold cyan]STORAGE AUDIT[/bold cyan]")
    console.print(f"MT5 History (5d): {mt5_count} trades")
    console.print(f"SQLite (titan.db): {db_count} total trades logged")
    console.print(f"CSV (trade_history_full): {csv_count} total trades logged")
    console.print(f"\nLast Logged in DB: {last_db_trade}")
    console.print(f"Last Logged in CSV: {last_csv_trade}")

if __name__ == "__main__":
    audit_storage()
