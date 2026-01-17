import sqlite3
import json
import pandas as pd

def summarize_fleet():
    conn = sqlite3.connect('data/strategy_factory.db')
    query = """
    SELECT genome, status, bt_sharpe, bt_oos_sharpe, live_pnl, live_trades 
    FROM strategies 
    WHERE status IN ('paper', 'live', 'rejected')
    """
    df_raw = pd.read_sql_query(query, conn)
    conn.close()
    
    if df_raw.empty:
        print("No active or recently rejected strategies found.")
        return

    results = []
    for _, row in df_raw.iterrows():
        genome = json.loads(row['genome'])
        results.append({
            'Name': genome.get('name', 'N/A'),
            'Type': genome.get('type', 'N/A'),
            'Symbol': genome.get('symbol', 'N/A'),
            'TF': genome.get('timeframe', 'H1'),
            'Status': row['status'].upper(),
            'BT Sharpe': round(row['bt_sharpe'], 2) if row['bt_sharpe'] else 0,
            'OOS Sharpe': round(row['bt_oos_sharpe'], 2) if row['bt_oos_sharpe'] else 0,
            'Live PnL': round(row['live_pnl'], 2) if row['live_pnl'] else 0,
            'Trades': row['live_trades'] or 0
        })
    
    df = pd.DataFrame(results)
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    summarize_fleet()
