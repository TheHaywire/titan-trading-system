import MetaTrader5 as mt5
import sqlite3
from datetime import datetime

# Initialize MT5
if not mt5.initialize():
    print("Failed to initialize MT5")
    exit()

# Get all positions
positions = mt5.positions_get()
print(f"=== MT5 ACTIVE POSITIONS ===")
print(f"Total: {len(positions)}")

factory_positions = [p for p in positions if 999000 <= p.magic <= 999999]
print(f"\nFactory Bot Positions: {len(factory_positions)}")
for p in factory_positions:
    print(f"  {p.symbol}: ${p.profit:.2f} | Magic: {p.magic} | Type: {'BUY' if p.type == 0 else 'SELL'}")

# Get closed deals from last 24 hours
from_date = datetime(2026, 1, 14, 0, 0, 0)
to_date = datetime.now()
deals = mt5.history_deals_get(from_date, to_date)

print(f"\n=== MT5 CLOSED DEALS (Last 24h) ===")
print(f"Total: {len(deals) if deals else 0}")

factory_deals = [d for d in deals if 999000 <= d.magic <= 999999] if deals else []
print(f"Factory Bot Deals: {len(factory_deals)}")
for d in factory_deals[:10]:  # Show last 10
    print(f"  {d.symbol}: ${d.profit:.2f} | Magic: {d.magic} | Time: {datetime.fromtimestamp(d.time)}")

# Check database sync
print(f"\n=== DATABASE SYNC STATUS ===")
conn = sqlite3.connect('data/strategy_factory.db')
c = conn.cursor()
c.execute("SELECT id, live_pnl, live_trades, magic_number FROM strategies WHERE status='paper'")
rows = c.fetchall()
for row in rows:
    print(f"  {row[0][:8]}: PnL=${row[1] or 0:.2f}, Trades={row[2] or 0}, Magic={row[3]}")

mt5.shutdown()

print("\n=== DIAGNOSIS ===")
if len(factory_positions) == 0 and len(factory_deals) == 0:
    print("⚠️  ISSUE: Bots are NOT placing trades in MT5")
    print("   Check bot logs for errors")
elif len(factory_deals) > 0 and all(r[2] == 0 for r in rows):
    print("⚠️  ISSUE: Trades exist in MT5 but NOT syncing to database")
    print("   Fleet Orchestrator's monitor_trades() is not running")
else:
    print("✅ System is working correctly")

conn.close()
