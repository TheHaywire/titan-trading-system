import sqlite3
import pandas as pd
import os

DB_PATH = "data/titan.db"

def audit_live_state():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    
    # Check tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    print(f"=== DATABASE TABLES ===\n{tables}")

    print("\n=== LATEST TRADES (Last 5) ===")
    try:
        trades = pd.read_sql_query("SELECT symbol, type, volume, open_price, profit, comment, strategy_name FROM trades ORDER BY open_time DESC LIMIT 5", conn)
        print(trades)
    except Exception as e:
        print(f"No trades found or error: {e}")

    if 'signal_decisions' in tables:
        print("\n=== LATEST SIGNAL DECISIONS (Last 10) ===")
        try:
            decisions = pd.read_sql_query("SELECT timestamp, symbol, decision, reason, score, strategy FROM signal_decisions ORDER BY id DESC LIMIT 10", conn)
            print(decisions)
        except Exception as e:
            print(f"Error reading decisions: {e}")
    else:
        print("\n⚠️  CRITICAL: 'signal_decisions' table NOT FOUND. Bots need a restart to apply schema updates.")
        
    conn.close()

if __name__ == "__main__":
    audit_live_state()
