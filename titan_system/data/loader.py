import MetaTrader5 as mt5
import pandas as pd
import polars as pl
import os
from datetime import datetime
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger("Titan.DataLoader")

class DataLoader:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
    def connect(self):
        if not mt5.initialize():
            logger.error(f"MT5 Initialize failed, error: {mt5.last_error()}")
            return False
        return True
        
    def find_symbol(self, symbol_name):
        """Attempts to find the correct broker specific symbol name"""
        # Common variations
        variations = [symbol_name, symbol_name.upper(), symbol_name.lower(), 
                     f"{symbol_name}m", f"{symbol_name}.m", f"{symbol_name}pro",
                     "GOLD" if symbol_name == "XAUUSD" else "XAUUSD"]
        
        info = mt5.symbols_get()
        if not info:
            logger.error("Failed to get symbols info")
            return None
            
        all_symbols = [s.name for s in info]
        
        for var in variations:
            if var in all_symbols:
                return var
                
        logger.warning(f"Could not find exact match for {symbol_name}. ")
        return None

    def fetch_history(self, symbol, timeframe, n_bars=10000):
        """Fetches history and returns a Polars DataFrame"""
        if not self.connect():
            return None
            
        real_symbol = self.find_symbol(symbol)
        if not real_symbol:
            logger.error(f"Symbol {symbol} not found in terminal.")
            return None
            
        # Ensure symbol is selected in Market Watch (CRITICAL)
        if not mt5.symbol_select(real_symbol, True):
             logger.warning(f"Failed to select {real_symbol} in Market Watch")

        logger.info(f"Fetching {n_bars} bars for {real_symbol}...")
        
        # Mt5 Copy Rates
        rates = mt5.copy_rates_from_pos(real_symbol, timeframe, 0, n_bars)
        
        # Fallback Logic: 100k -> 50k -> 10k -> 1000
        if rates is None:
             logger.warning(f"Fetch {n_bars} failed. Retrying with 50,000...")
             rates = mt5.copy_rates_from_pos(real_symbol, timeframe, 0, 50000)
             
        if rates is None:
             logger.warning(f"Fetch 50,000 failed. Retrying with 10,000...")
             rates = mt5.copy_rates_from_pos(real_symbol, timeframe, 0, 10000)
             
        if rates is None:
             logger.warning(f"Fetch 10,000 failed. Retrying with 1,000...")
             rates = mt5.copy_rates_from_pos(real_symbol, timeframe, 0, 1000)
        
        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch rates for {real_symbol}. Error: {mt5.last_error()}")
            return None
            
        # Convert to Pandas first (easier compatibility with Mt5 numpy struct)
        pdf = pd.DataFrame(rates)
        
        # Convert Time
        pdf['time'] = pd.to_datetime(pdf['time'], unit='s')
        
        # Convert to Polars for Speed
        df = pl.from_pandas(pdf)
        
        return df

    def save_data(self, df, filename):
        path = os.path.join(self.data_dir, filename)
        # Save as CSV for compatibility and ease of reading manually if needed
        # In full production we'd use parquet: df.write_parquet(path)
        df.write_csv(path)
        logger.info(f"💾 Saved {len(df)} rows to {path}")
        return path

if __name__ == "__main__":
    loader = DataLoader(data_dir=os.path.join(os.getcwd(), "titan_system", "data", "history"))
    
    # Test Fetch EURUSD
    df = loader.fetch_history("EURUSD", mt5.TIMEFRAME_M1, 50000)
    if df is not None:
        loader.save_data(df, "EURUSD_M1.csv")
        
    # Test Fetch GOLD
    df_gold = loader.fetch_history("XAUUSD", mt5.TIMEFRAME_M1, 50000)
    if df_gold is not None:
        loader.save_data(df_gold, "GOLD_M1.csv")
    
    mt5.shutdown()
