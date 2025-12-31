
import sqlite3

db_path = "titan_system/titan.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 60)
print("TITAN SYSTEM - OPTIMIZATION RESULTS")
print("=" * 60)

# Get strategy assignments
cursor.execute("""
    SELECT symbol, active_strategy, backtest_score, volatility_score
    FROM market_universe 
    WHERE active_strategy IS NOT NULL
    ORDER BY backtest_score DESC
    LIMIT 20
""")

results = cursor.fetchall()

print(f"\n{'Symbol':<12} {'Strategy':<18} {'Backtest P/L':<15} {'Vol Score':<10}")
print("-" * 60)

for symbol, strategy, score, vol in results:
    print(f"{symbol:<12} {strategy:<18} {score:>10.2f}%    {vol:>8.2f}")

print("=" * 60)

# Summary stats
cursor.execute("SELECT active_strategy, COUNT(*) FROM market_universe WHERE active_strategy IS NOT NULL GROUP BY active_strategy")
summary = cursor.fetchall()

print("\nStrategy Distribution:")
for strat, count in summary:
    print(f"  {strat}: {count} symbols")

conn.close()
