import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "data/titan.db"

def run_production_forensics():
    print("="*60)
    print("🚀 TITAN PRODUCTION FORENSIC AUDIT")
    print("="*60)
    
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Strategy Performance
    print("\n--- Strategy Alpha Performance ---")
    query = """
    SELECT strategy_name, COUNT(*) as trades, SUM(profit) as total_profit, 
           AVG(profit) as avg_profit,
           (SUM(CASE WHEN profit > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) as win_rate
    FROM trades 
    GROUP BY strategy_name
    ORDER BY total_profit DESC
    """
    df_strat = pd.read_sql_query(query, conn)
    print(df_strat)
    
    # 2. Symbol Performance
    print("\n--- Top Symbol Performance ---")
    query = """
    SELECT symbol, COUNT(*) as trades, SUM(profit) as total_profit
    FROM trades 
    GROUP BY symbol
    ORDER BY total_profit DESC
    LIMIT 10
    """
    df_sym = pd.read_sql_query(query, conn)
    print(df_sym)
    
    # 3. Recent Activity (Last 24h)
    print("\n--- Last 24h Activity ---")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    # Using open_time or just latest IDs if format varies
    try:
        query = f"SELECT symbol, type, profit, open_time FROM trades ORDER BY open_time DESC LIMIT 10"
        df_recent = pd.read_sql_query(query, conn)
        print(df_recent)
    except:
        print("Could not parse recent activity.")

    # 4. Drawdown Check
    print("\n--- System Health Check ---")
    try:
        query = "SELECT SUM(profit) FROM trades WHERE profit IS NOT NULL"
        total = conn.execute(query).fetchone()[0] or 0
        print(f"Cumulative Gross Profit: ${total:,.2f}")
    except:
        pass

    conn.close()

if __name__ == "__main__":
    run_production_forensics()
