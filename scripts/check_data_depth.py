import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

def check_data_depth():
    print("📊 CHECKING MT5 DATA DEPTH...")
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    symbol = "GOLD"
    if not mt5.symbol_select(symbol, True):
        print(f"{symbol} not found")
        return

    # 1. Deep History Scope (2020-2026)
    start_deep = datetime(2020, 1, 1)
    end_deep = datetime(2026, 1, 1)

    # 2. Scalping Scope (Jun 2025 - Jan 2026)
    start_scalp = datetime(2025, 6, 1)
    end_scalp = datetime(2026, 1, 1)

    timeframes = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }

    print(f"\n{'TF':<5} | {'Deep History (2020-2026)':<25} | {'Scalping (Jun 25-Jan 26)':<25}")
    print("-" * 60)

    for name, tf in timeframes.items():
        # Count Deep
        rates_deep = mt5.copy_rates_range(symbol, tf, start_deep, end_deep)
        count_deep = len(rates_deep) if rates_deep is not None else 0
        
        # Count Scalp
        rates_scalp = mt5.copy_rates_range(symbol, tf, start_scalp, end_scalp)
        count_scalp = len(rates_scalp) if rates_scalp is not None else 0

        print(f"{name:<5} | {count_deep:<25,} | {count_scalp:<25,}")

    mt5.shutdown()

if __name__ == "__main__":
    check_data_depth()
