"""Close all tiny 0.01 positions - keep properly sized ones"""
import MetaTrader5 as mt5
mt5.initialize()

positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    exit()

closed = 0
kept = 0

for pos in positions:
    if pos.volume <= 0.02:  # Close tiny positions
        close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        tick = mt5.symbol_info_tick(pos.symbol)
        price = tick.bid if pos.type == 0 else tick.ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 20,
            "magic": 999999,
            "comment": "Close tiny pos",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"Closed: {pos.symbol} {pos.volume} lots (P/L: ${pos.profit:.2f})")
            closed += 1
        else:
            print(f"Failed to close {pos.symbol}: {result.comment}")
    else:
        print(f"Keeping: {pos.symbol} {pos.volume} lots (P/L: ${pos.profit:.2f})")
        kept += 1

print(f"\nClosed: {closed}, Kept: {kept}")
mt5.shutdown()
