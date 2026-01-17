import MetaTrader5 as mt5
import pandas as pd

def test_data():
    if not mt5.initialize():
        print("Init failed")
        return
        
    symbol = "US500Cash" # Resolved root
    print(f"Testing {symbol}...")
    
    if not mt5.symbol_select(symbol, True):
        print(f"Failed to select {symbol}")
    else:
        # Check if visible
        info = mt5.symbol_info(symbol)
        print(f"Symbol Info: {info.select if info else 'None'}")
        
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
        if rates is None:
            print(f"Rates is NONE. Error: {mt5.last_error()}")
        else:
            print(f"Rates count: {len(rates)}")
            
    mt5.shutdown()

if __name__ == "__main__":
    test_data()
