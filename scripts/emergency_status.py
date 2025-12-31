import MetaTrader5 as mt5
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Emergency")

if not mt5.initialize():
    logger.error("MT5 Init Failed")
    exit()

if settings.mt5_login:
    mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

# Get account info
account = mt5.account_info()
positions = mt5.positions_get()

print("\n" + "="*60)
print("🚨 EMERGENCY ACCOUNT STATUS")
print("="*60)
print(f"Balance: ${account.balance:.2f}")
print(f"Equity: ${account.equity:.2f}")
print(f"Margin: ${account.margin:.2f}")
print(f"Free Margin: ${account.margin_free:.2f}")
print(f"Margin Level: {account.margin_level:.2f}%")
print(f"\nOpen Positions: {len(positions)}")
print("="*60)

print("\n📊 POSITION BREAKDOWN:")
for pos in positions[:20]:  # Show first 20
    pnl = pos.profit
    color = "🟢" if pnl > 0 else "🔴"
    trade_type = "BUY" if pos.type == 0 else "SELL"
    print(f"{color} {pos.symbol:<10} {trade_type:<5} Vol:{pos.volume:.2f} P/L:${pnl:>8.2f}")

if len(positions) > 20:
    print(f"\n... and {len(positions) - 20} more positions")

print("\n" + "="*60)
total_pnl = sum(p.profit for p in positions)
print(f"Total Floating P/L: ${total_pnl:.2f}")
print("="*60)

mt5.shutdown()
