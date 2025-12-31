
import MetaTrader5 as mt5
import sys
import os
# Fix import path for nested legacy location
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config.settings import settings

def cleanup_trades():
    if not mt5.initialize():
        print("❌ MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    symbol = "GOLD"
    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        print(f"No positions on {symbol}")
        return

    print(f"🔍 Analyzing {len(positions)} positions on {symbol}...")
    
    buys = [p for p in positions if p.type == 0]
    sells = [p for p in positions if p.type == 1]
    
    print(f"   🟢 BUYs: {len(buys)}")
    print(f"   🔴 SELLS: {len(sells)}")
    
    # Logic: If mixed, suggest closing the losers
    
    for pos in positions:
        print(f"   🗑️ Closing Position (Ticket: {pos.ticket}) | P/L: ${pos.profit:.2f}")
        
        # Try all filling modes
        modes = [mt5.ORDER_FILLING_FOK, mt5.ORDER_FILLING_IOC, mt5.ORDER_FILLING_RETURN]
        success = False
        
        for mode in modes:
            req = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": symbol,
                "volume": pos.volume,
                "type": 1 if pos.type == 0 else 0, # Opposite
                "price": mt5.symbol_info_tick(symbol).bid if pos.type == 0 else mt5.symbol_info_tick(symbol).ask,
                "dev": 20,
                "magic": pos.magic,
                "comment": f"Cleanup M{mode}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mode,
            }
            res = mt5.order_send(req)
            if res.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"     ✅ Closed (Mode {mode}).")
                success = True
                break
            else:
                print(f"     ⚠️ Mode {mode} Failed: {res.comment}")
        
        if not success:
            print("     ❌ ALL MODES FAILED.")

    print("\n✅ Cleanup Complete.")
    mt5.shutdown()

if __name__ == "__main__":
    cleanup_trades()
