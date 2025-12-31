"""Quick status check"""
import MetaTrader5 as mt5
mt5.initialize()

positions = mt5.positions_get()
account = mt5.account_info()

print(f"Equity: ${account.equity:,.2f}")
print(f"Balance: ${account.balance:,.2f}")
print(f"Profit: ${account.profit:,.2f}")
print(f"Open Positions: {len(positions) if positions else 0}")

if positions:
    print()
    total_profit = 0
    for p in positions:
        emoji = "+" if p.profit > 0 else "-"
        direction = "BUY" if p.type == 0 else "SELL"
        print(f"{emoji} {p.symbol}: {direction} {p.volume} lots | P/L: ${p.profit:.2f}")
        total_profit += p.profit
    print(f"\nTotal Open P/L: ${total_profit:.2f}")

mt5.shutdown()
