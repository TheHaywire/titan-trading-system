
import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings

def view_positions():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    positions = mt5.positions_get()
    
    if not positions:
        print("No Open Positions.")
    else:
        print(f"\n{'Symbol':<10} {'Type':<6} {'Vol':<6} {'Open Price':<12} {'Current':<12} {'Profit':<10}")
        print("-" * 60)
        for pos in positions:
            type_str = "BUY" if pos.type == 0 else "SELL"
            print(f"{pos.symbol:<10} {type_str:<6} {pos.volume:<6} {pos.price_open:<12.5f} {pos.price_current:<12.5f} {pos.profit:<10.2f}")
    
    mt5.shutdown()

if __name__ == "__main__":
    view_positions()
