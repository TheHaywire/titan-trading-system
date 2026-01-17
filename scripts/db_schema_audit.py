import sqlite3

def audit_schema():
    conn = sqlite3.connect('data/titan.db')
    cursor = conn.cursor()
    
    tables = ['trades', 'ohlcv', 'trade_history', 'signal_decisions']
    for table in tables:
        print(f"\n--- {table} schema ---")
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            for col in cursor.fetchall():
                print(f"  {col[1]} ({col[2]})")
        except Exception as e:
            print(f"Error reading {table}: {e}")
            
    conn.close()

if __name__ == "__main__":
    audit_schema()
