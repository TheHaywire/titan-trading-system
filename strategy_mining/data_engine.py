"""
Mass Parallel Data Engine for MT5
Fetches OHLCV data for multiple symbols and timeframes concurrently.
Constructs a memory-efficient MultiIndex Pandas DataFrame.
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import concurrent.futures
from typing import List, Dict, Optional, Tuple
import logging
from datetime import datetime
import time

# Import configuration
import strategy_mining.mining_config as config

# Setup logging
logger = logging.getLogger(__name__)

class DataEngine:
    def __init__(self):
        self.initialized = False
        self.connect()

    def connect(self):
        """Initialize connection to MT5."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed, error code: {mt5.last_error()}")
            return False
        
        self.initialized = True
        logger.info("MT5 initialized successfully.")
        return True

    def get_market_watch_symbols(self) -> List[str]:
        """Fetch all symbols currently available in the Market Watch."""
        if not self.initialized and not self.connect():
            return []
            
        symbols = mt5.symbols_get()
        if symbols is None:
            logger.error("No symbols found in MT5.")
            return []
            
        # Filter for symbols visible in Market Watch
        mw_symbols = [s.name for s in symbols if s.visible]
        logger.info(f"Discovered {len(mw_symbols)} symbols in Market Watch.")
        return mw_symbols

    def fetch_bars(self, symbol: str, timeframe_str: str, n_bars: int = config.LOOKBACK_BARS) -> Optional[pd.DataFrame]:
        """Fetch bars for a single symbol and timeframe."""
        if not self.initialized and not self.connect():
            return None
            
        tf = config.get_mt5_timeframe(timeframe_str)
        # print(f"Fetching {symbol} {timeframe_str}...") # Debugging
        
        bars = mt5.copy_rates_from_pos(symbol, tf, 0, n_bars)
        
        if bars is None or len(bars) == 0:
            logger.warning(f"Failed to fetch data for {symbol} ({timeframe_str}).")
            return None
            
        df = pd.DataFrame(bars)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Add Index identifiers
        df['symbol'] = symbol
        df['timeframe'] = timeframe_str
        
        # Select and rename columns
        df = df[['time', 'symbol', 'timeframe', 'open', 'high', 'low', 'close', 'tick_volume']]
        df.rename(columns={'tick_volume': 'volume'}, inplace=True)
        
        return df

    def parallel_fetch_all(self, symbols: List[str], timeframes: List[str]) -> pd.DataFrame:
        """Fetch all data in parallel using ThreadPoolExecutor."""
        tasks = []
        for symbol in symbols:
            for tf in timeframes:
                tasks.append((symbol, tf))
        
        logger.info(f"Starting parallel fetch for {len(tasks)} combinations...")
        
        results = []
        completed = 0
        total = len(tasks)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            future_to_task = {executor.submit(self.fetch_bars, s, tf): (s, tf) for s, tf in tasks}
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                completed += 1
                
                if completed % 25 == 0:
                    logger.info(f"Progress: {completed}/{total} ({completed/total*100:.1f}%) - Last: {task[0]} {task[1]}")
                
                try:
                    data = future.result()
                    if data is not None:
                        results.append(data)
                except Exception as exc:
                    logger.error(f"Task {task} generated an exception: {exc}")
        
        if not results:
            logger.error("No data fetched in parallel process.")
            return pd.DataFrame()
            
        # Combine all dataframes
        combined_df = pd.concat(results, ignore_index=True)
        
        # Set MultiIndex: Symbol, Timeframe, Time
        # This makes it memory efficient and easy to slice
        combined_df.set_index(['symbol', 'timeframe', 'time'], inplace=True)
        combined_df.sort_index(inplace=True)
        
        logger.info(f"Data engine ready. Total rows: {len(combined_df)}")
        return combined_df

    def close(self):
        """Shutdown MT5 connection."""
        mt5.shutdown()
        self.initialized = False
        logger.info("MT5 connection closed.")

# Usage Example:
# engine = DataEngine()
# symbols = engine.get_market_watch_symbols()
# df = engine.parallel_fetch_all(symbols, ['M15', 'H1', 'H4'])
