import sqlite3
import pandas as pd
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

def inspect_db():
    db_path = settings.db_path
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return

    print(f"🔍 Inspecting Database: {db_path}")
    conn = sqlite3.connect(db_path)
    
    # 1. Check Trades
    print("\n📊 Recent Trades:")
    try:
        trades = pd.read_sql_query("SELECT * FROM trades ORDER BY open_time DESC LIMIT 10", conn)
        if trades.empty:
            print("   No trades found.")
        else:
            print(trades.to_string(index=False))
            
            # Summary Stats
            print("\n📈 Performance Summary:")
            all_trades = pd.read_sql_query("SELECT profit, type FROM trades", conn)
            total_pnl = all_trades['profit'].sum()
            win_rate = len(all_trades[all_trades['profit'] > 0]) / len(all_trades) * 100 if len(all_trades) > 0 else 0
            print(f"   Total PnL: ${total_pnl:.2f}")
            print(f"   Win Rate: {win_rate:.1f}%")
            print(f"   Total Trades: {len(all_trades)}")
            
    except Exception as e:
        print(f"   Error reading trades: {e}")

    # 2. Check Logs
    print("\n📝 Recent System Logs (Errors/Warnings):")
    try:
        logs = pd.read_sql_query("SELECT timestamp, level, component, message FROM logs WHERE level IN ('ERROR', 'CRITICAL', 'WARNING') ORDER BY id DESC LIMIT 10", conn)
        if logs.empty:
            print("   No critical logs found.")
        else:
            print(logs.to_string(index=False))
    except Exception as e:
        print(f"   Error reading logs: {e}")

    conn.close()

if __name__ == "__main__":
    inspect_db()
