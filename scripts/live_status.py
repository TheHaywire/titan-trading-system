import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("MT5 initialization failed")
    exit()

print("=" * 60)
print(f"LIVE ACCOUNT STATUS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Account info
acc = mt5.account_info()
print(f"\n💰 ACCOUNT:")
print(f"Balance: ${acc.balance:,.2f}")
print(f"Equity: ${acc.equity:,.2f}")
print(f"Margin: ${acc.margin:,.2f}")
print(f"Free Margin: ${acc.margin_free:,.2f}")
print(f"P&L: ${acc.profit:,.2f}")

# Open positions
positions = mt5.positions_get()
print(f"\n📊 OPEN POSITIONS: {len(positions) if positions else 0}")

if positions:
    print("\nSymbol | Type | Size | Entry | Current | P&L | Magic")
    print("-" * 70)
    for pos in positions:
        direction = "BUY" if pos.type == 0 else "SELL"
        print(f"{pos.symbol:8} | {direction:4} | {pos.volume:5.2f} | {pos.price_open:8.2f} | {pos.price_current:8.2f} | ${pos.profit:8.2f} | {pos.magic}")

# Recent trades (last hour)
from datetime import timedelta
recent_time = datetime.now() - timedelta(hours=1)
deals = mt5.history_deals_get(recent_time, datetime.now())

if deals:
    print(f"\n⚡ RECENT ACTIVITY (Last hour): {len(deals)} deals")
    print("\nTime | Symbol | Type | Volume | Price | Profit")
    print("-" * 70)
    for deal in deals[-10:]:  # Last 10
        deal_time = datetime.fromtimestamp(deal.time)
        deal_type = "BUY" if deal.type == 0 else "SELL"
        print(f"{deal_time.strftime('%H:%M:%S')} | {deal.symbol:8} | {deal_type:4} | {deal.volume:5.2f} | {deal.price:8.2f} | ${deal.profit:8.2f}")
else:
    print(f"\n⚡ RECENT ACTIVITY: No trades in last hour")

# Check if bot is running (by checking for recent bot trades with magic 888888)
bot_deals = [d for d in deals if d.magic == 888888] if deals else []
if bot_deals:
    print(f"\n🤖 BOT STATUS: ACTIVE (detected {len(bot_deals)} bot trades)")
else:
    print(f"\n🤖 BOT STATUS: NOT DETECTED (no trades with magic 888888)")

mt5.shutdown()
