import MetaTrader5 as mt5

if not mt5.initialize():
    print("Failed")
    exit()

print("CLOSING ALL POSITIONS IMMEDIATELY")

positions = mt5.positions_get()
for pos in positions:
    close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": pos.symbol,
        "volume": pos.volume,
        "type": close_type,
        "position": pos.ticket,
        "magic": 999999,
        "comment": "EMERGENCY_CLOSE",
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ Closed {pos.symbol} {pos.volume} lots")
    else:
        print(f"❌ Failed {pos.symbol}")

mt5.shutdown()
print("\nALL POSITIONS CLOSED")
