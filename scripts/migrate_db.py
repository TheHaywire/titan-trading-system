
import sqlite3

db_path = "titan_system/titan.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Migrating Database...")

# Add active_strategy
try:
    cursor.execute("ALTER TABLE market_universe ADD COLUMN active_strategy TEXT")
    print("✅ Added active_strategy column")
except Exception as e:
    print(f"⚠️ active_strategy: {e}")

# Add backtest_score
try:
    cursor.execute("ALTER TABLE market_universe ADD COLUMN backtest_score REAL")
    print("✅ Added backtest_score column")
except Exception as e:
    print(f"⚠️ backtest_score: {e}")

conn.commit()
conn.close()
print("Migration Complete.")
