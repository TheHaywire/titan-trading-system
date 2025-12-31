import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import config
from mt5_interface import MT5Interface

def download_data(symbol, timeframe, num_candles=10000, filename=None):
    """
    Downloads historical data and saves to CSV.
    """
    mt5_interface = MT5Interface()
    if not mt5_interface.start():
        print("Failed to connect to MT5")
        return

    print(f"Downloading {num_candles} candles for {symbol}...")
    df = mt5_interface.get_closes(symbol, timeframe, num_candles)
    
    if df is not None:
        if filename is None:
            filename = f"{symbol}_{timeframe}_data.csv"
        
        df.to_csv(filename, index=False)
        print(f"Data saved to {filename}")
        print(df.head())
        print(df.tail())
    else:
        print("No data received")

    mt5_interface.shutdown()

if __name__ == "__main__":
    # Example usage: Download 10,000 H1 candles for EURUSD
    download_data("EURUSD", mt5.TIMEFRAME_H1, num_candles=10000)
