import MetaTrader5 as mt5
import pandas as pd
import time

def close_all_positions():
    print("Connecting to MT5...")
    if not mt5.initialize():
        print(f"Failed to connect: {mt5.last_error()}")
        return

    print("Fetching open positions...")
    positions = mt5.positions_get()
    
    if not positions:
        print("No open positions found.")
        return

    print(f"Found {len(positions)} open positions. Closing them now...")
    
    count = 0
    for pos in positions:
        tick = mt5.symbol_info_tick(pos.symbol)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": pos.ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
            "price": tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close All Script",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Failed to close #{pos.ticket}: {result.comment}")
        else:
            print(f"Closed #{pos.ticket} ({pos.symbol})")
            count += 1
            
        time.sleep(0.1) # Small delay to be gentle

    print(f"Done. Closed {count}/{len(positions)} positions.")
    mt5.shutdown()

if __name__ == "__main__":
    close_all_positions()
