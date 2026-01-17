"""
MT5 BACKTEST DATA FETCHER
==========================
Fetches historical OHLC data from MT5 and calculates technical indicators.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MT5DataFetcher:
    def __init__(self):
        self.connected = False
    
    def connect(self):
        if not mt5.initialize():
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False
        self.connected = True
        logger.info("MT5 connected for backtesting")
        return True
    
    def fetch_historical_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, days=180):
        """
        Fetch historical OHLC data.
        
        Args:
            symbol: MT5 symbol (e.g., "XAUUSD", "US100Cash")
            timeframe: MT5 timeframe constant
            days: Number of days to fetch
        
        Returns:
            DataFrame with OHLC + calculated indicators
        """
        if not self.connected:
            self.connect()
        
        # Calculate bars needed
        bars_per_day = {
            mt5.TIMEFRAME_H1: 24,
            mt5.TIMEFRAME_D1: 1,
            mt5.TIMEFRAME_M15: 96
        }
        count = days * bars_per_day.get(timeframe, 24)
        
        logger.info(f"Fetching {count} bars for {symbol}...")
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        
        if rates is None or len(rates) == 0:
            logger.error(f"No data for {symbol}")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        logger.info(f"Fetched {len(df)} bars from {df['time'].min()} to {df['time'].max()}")
        return df
    
    def calculate_indicators(self, df):
        """Calculate technical indicators (Finviz-style)."""
        
        # 1. RSI (14-period)
        df['RSI'] = self.calculate_rsi(df['close'], period=14)
        
        # 2. Relative Volume (Current Vol / 20-period Average Vol)
        df['Avg_Volume'] = df['tick_volume'].rolling(window=20).mean()
        df['Rel_Volume'] = df['tick_volume'] / df['Avg_Volume']
        
        # 3. ATR (Average True Range - 14 period)
        df['ATR'] = self.calculate_atr(df, period=14)
        
        # 4. Simple Moving Averages
        df['SMA_20'] = df['close'].rolling(window=20).mean()
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # 5. Price change %
        df['Change_Pct'] = df['close'].pct_change() * 100
        
        # 6. 52-bar High/Low (proxy for 52W on shorter timeframes)
        df['High_52'] = df['high'].rolling(window=52).max()
        df['Low_52'] = df['low'].rolling(window=52).min()
        df['Near_52W_High'] = (df['close'] >= df['High_52'] * 0.98).astype(int)
        
        return df
    
    def calculate_rsi(self, series, period=14):
        """Calculate Relative Strength Index."""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_atr(self, df, period=14):
        """Calculate Average True Range."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def save_to_csv(self, df, symbol, timeframe_name):
        """Save data to CSV for analysis."""
        filename = f"data/backtest_{symbol}_{timeframe_name}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"Saved to {filename}")
        return filename

if __name__ == "__main__":
    fetcher = MT5DataFetcher()
    fetcher.connect()
    
    # Get actual symbols from Market Watch
    all_symbols = mt5.symbols_get()
    if all_symbols:
        symbol_names = [s.name for s in all_symbols if s.visible]
        logger.info(f"Found {len(symbol_names)} symbols in Market Watch")
        
        # Filter for major symbols
        target_keywords = ["GOLD", "XAU", "SILVER", "XAG", "US100", "NAS", "EUR", "GBP"]
        symbols = [s for s in symbol_names if any(kw in s.upper() for kw in target_keywords)][:5]
        
        logger.info(f"Selected symbols for backtest: {symbols}")
    else:
        symbols = []
        logger.error("No symbols found in Market Watch")
    
    for symbol in symbols:
        df = fetcher.fetch_historical_data(symbol, mt5.TIMEFRAME_H1, days=180)
        if df is not None:
            print(f"\n{symbol} Data Sample:")
            print(df[['time', 'close', 'RSI', 'Rel_Volume', 'ATR']].tail(5))
            
            # Save to CSV
            fetcher.save_to_csv(df, symbol, "H1")
    
    mt5.shutdown()
