
import sqlite3

db_path = "titan_system/titan.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
try:
    cursor.execute("SELECT count(*) FROM market_universe")
    count = cursor.fetchone()[0]
    print(f"Market Universe Count: {count}")
    
    if count > 0:
        cursor.execute("SELECT symbol, category, volatility_score FROM market_universe ORDER BY volatility_score DESC LIMIT 5")
        print("\nTop 5 Volatile Assets:")
        for r in cursor.fetchall():
            print(r)
except Exception as e:
    print(e)
conn.close()
