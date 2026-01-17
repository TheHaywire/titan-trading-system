import MetaTrader5 as mt5

def rescue_gold():
    if not mt5.initialize():
        print("MT5 failed")
        return

    positions = mt5.positions_get(symbol="GOLD")
    if not positions:
        print("No GOLD positions found.")
        return

    for p in positions:
        # Check if it's a SHORT (type 1) and has the rogue magic or comment
        # Or just close all SHORTS on GOLD to be safe
        if p.type == mt5.ORDER_TYPE_SELL:
            print(f"🚨 Closing Rogue GOLD Short: {p.ticket} | Volume: {p.volume} | P&L: {p.profit}")
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": p.symbol,
                "volume": p.volume,
                "type": mt5.ORDER_TYPE_BUY,
                "position": p.ticket,
                "price": mt5.symbol_info_tick(p.symbol).ask,
                "deviation": 50,
                "magic": p.magic,
                "comment": "RESCUE_LIQUIDATION",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ Closed {p.ticket}")
            else:
                print(f"❌ Failed to close {p.ticket}: {result.comment}")

    mt5.shutdown()

if __name__ == "__main__":
    rescue_gold()
