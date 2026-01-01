import MetaTrader5 as mt5
from mt5_interface import MT5Interface
import json
import datetime

interface = MT5Interface()
interface.start()

# Get all data
account = mt5.account_info()
positions = mt5.positions_get()
from_date = datetime.datetime.now() - datetime.timedelta(days=7)
deals = mt5.history_deals_get(from_date, datetime.datetime.now())

# Create report dict
report = {
    "account": {
        "id": account.login,
        "server": account.server,
        "balance": account.balance,
        "equity": account.equity,
        "profit": account.profit,
        "margin": account.margin,
        "free_margin": account.margin_free,
        "margin_level": account.margin_level if account.margin > 0 else 0,
        "leverage": account.leverage
    },
    "positions": []
}

if positions:
    for pos in positions:
        report["positions"].append({
            "symbol": pos.symbol,
            "type": "BUY" if pos.type == 0 else "SELL",
            "volume": pos.volume,
            "entry": pos.price_open,
            "current": pos.price_current,
            "profit": pos.profit
        })

# Recent trades
if deals:
    closed = [d for d in deals if d.profit != 0 and d.entry == 1]
    if closed:
        wins = len([d for d in closed if d.profit > 0])
        report["last_7_days"] = {
            "total_trades": len(closed),
            "wins": wins,
            "losses": len(closed) - wins,
            "win_rate": round((wins/len(closed)*100), 1),
            "net_pnl": sum(d.profit for d in closed)
        }

# Save to file
with open("account_snapshot.json", "w") as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
interface.shutdown()
