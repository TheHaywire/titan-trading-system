
import sqlite3

db_path = "titan_system/titan.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT category, COUNT(*) FROM market_universe GROUP BY category")
rows = cursor.fetchall()

print("--- Category Distribution ---")
for cat, count in rows:
    print(f"{cat}: {count}")

conn.close()
