import sqlite3
import os

DB_PATH = "data/titan.db"

def init_production_ledger():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print(f"Initializing Decision Ledger in {DB_PATH}...")
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS signal_decisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        symbol TEXT NOT NULL,
        decision TEXT NOT NULL, -- 'EXECUTED', 'REJECTED', 'SKIPPED', 'ADAPTIVE_EXIT'
        reason TEXT,
        score REAL,
        strategy TEXT,
        metadata TEXT -- JSON blob for extra info
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Signal Decisions table created/confirmed.")

if __name__ == "__main__":
    init_production_ledger()
