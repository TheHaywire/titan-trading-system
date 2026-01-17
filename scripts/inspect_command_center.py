import sqlite3
import os

db_path = "data/command_center.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("--- SYMBOLS ---")
    cursor.execute("SELECT ticker, is_active, source FROM symbols LIMIT 10")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
        
    print("\n--- FINVIZ DATA ---")
    cursor.execute("SELECT symbol_id, price, change_pct FROM finviz_data LIMIT 10")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
        
    print("\n--- NEWS ---")
    cursor.execute("SELECT symbol_id, headline FROM news LIMIT 10")
    rows = cursor.fetchall()
    for r in rows:
        print(r)
        
    conn.close()
else:
    print(f"Database {db_path} not found.")
