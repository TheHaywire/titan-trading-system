
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def test_mt5_connection():
    print("Testing MT5 Connection...")
    if not mt5.initialize():
        print(f"initialize() failed, error code = {mt5.last_error()}")
        return False
    
    print(f"MT5 Initialized. Version: {mt5.version()}")
    
    # Test Data Fetching
    symbol = "XAUUSD" # Try GOLD first
    print(f"Attempting to fetch data for {symbol}...")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
    
    if rates is None:
        print(f"Failed to fetch data for {symbol}. Error: {mt5.last_error()}")
        # Try a fallback symbol if gold fails (maybe symbol name is different)
        symbol = "EURUSD"
        print(f"Retrying with {symbol}...")
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 100)
        
    if rates is not None and len(rates) > 0:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        print(f"SUCCESS! Fetched {len(df)} rows.")
        print(df.head())
        mt5.shutdown()
        return True
    else:
        print("FAILED to fetch any data.")
        mt5.shutdown()
        return False

if __name__ == "__main__":
    test_mt5_connection()
