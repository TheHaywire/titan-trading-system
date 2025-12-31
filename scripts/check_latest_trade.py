
import sqlite3
import pandas as pd
from config.settings import settings

def check_trades():
    conn = sqlite3.connect(settings.db_path)
    cursor = conn.cursor()
    
    # Get last 5 trades
    cursor.execute("SELECT * FROM trades ORDER BY open_time DESC LIMIT 5")
    columns = [description[0] for description in cursor.description]
    rows = cursor.fetchall()
    
    print("\n🧾 LATEST LIVE TRADES")
    print("="*60)
    
    if not rows:
        print("No trades found.")
    else:
        df = pd.DataFrame(rows, columns=columns)
        for _, row in df.iterrows():
            print(f"🎫 TICKET: {row['ticket']}")
            print(f"   Symbol:   {row['symbol']}")
            print(f"   Type:     {row['type']}")
            print(f"   Volume:   {row['volume']}")
            print(f"   Price:    {row['open_price']}")
            print(f"   Strategy: {row['strategy_name']}")
            print(f"   Time:     {row['open_time']}")
            print("-" * 60)

    conn.close()

if __name__ == "__main__":
    check_trades()
