import sqlite3
import pandas as pd

def debug():
    db_path = 'data/titan.db'
    print(f"Inspecting {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    for t in tables:
        try:
            df = pd.read_sql_query(f"SELECT count(*) as count FROM {t}", conn)
            print(f"  Table '{t}': {df.iloc[0]['count']} rows")
            if t == 'trades':
                sample = pd.read_sql_query(f"SELECT * FROM {t} LIMIT 1", conn)
                print(f"    Sample: {sample.to_dict('records')}")
        except Exception as e:
            print(f"  Table '{t}': Error {e}")
            
    conn.close()

if __name__ == "__main__":
    debug()
