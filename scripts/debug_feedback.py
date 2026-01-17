import sqlite3
import os

db_path = 'data/alpha_feedback.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit()

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("--- RECENT NON-REJECTED DECISIONS ---")
cursor.execute("SELECT symbol, decision, reasoning FROM ai_decisions WHERE decision != 'NO' ORDER BY timestamp DESC LIMIT 10")
rows = cursor.fetchall()
if not rows:
    print("No 'YES' decisions found.")
for row in rows:
    print(row)

print("\n--- RECENT REJECTIONS (NON-ALPHA) ---")
cursor.execute("SELECT symbol, decision, reasoning FROM ai_decisions WHERE decision = 'NO' AND reasoning NOT LIKE 'Low Alpha%' ORDER BY timestamp DESC LIMIT 10")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()
