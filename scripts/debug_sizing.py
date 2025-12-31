"""Debug position sizing for all symbols"""
import MetaTrader5 as mt5
mt5.initialize()

account = mt5.account_info()
equity = account.equity
risk_amount = equity * 0.01  # 1%

print(f"Equity: ${equity:,.2f}")
print(f"Risk Amount (1%): ${risk_amount:,.2f}")
print()

symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "GOLD", "BTCUSD", "US500"]
sl_points = {
    "EURUSD": 500, "GBPUSD": 500, "USDJPY": 500, "AUDUSD": 500, "USDCAD": 500,
    "GOLD": 5000, "BTCUSD": 50000, "US500": 5000
}

for sym in symbols:
    info = mt5.symbol_info(sym)
    if not info:
        print(f"{sym}: Symbol not found")
        continue
    
    tick_value = info.trade_tick_value
    sl = sl_points.get(sym, 500)
    
    if tick_value > 0:
        lot = risk_amount / (sl * tick_value)
        lot = max(info.volume_min, min(info.volume_max, round(lot, 2)))
    else:
        lot = 0.01
    
    print(f"{sym}: tick_value={tick_value:.4f}, SL={sl}, LOT={lot:.2f}")

mt5.shutdown()
