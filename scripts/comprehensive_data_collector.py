"""
COMPREHENSIVE MT5 DATA COLLECTOR
==================================
Fetches historical data for multiple symbols and timeframes for institutional backtesting.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ComprehensiveDataCollector:
    def __init__(self):
        self.connected = False
        self.data_dir = Path("data/institutional")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def connect(self):
        if not mt5.initialize():
            logger.error(f"MT5 init failed: {mt5.last_error()}")
            return False
        self.connected = True
        logger.info("MT5 connected for data collection")
        return True
    
    def get_available_symbols(self, keywords):
        """Find available symbols matching keywords."""
        all_symbols = mt5.symbols_get()
        if not all_symbols:
            return []
        
        symbol_names = [s.name for s in all_symbols if s.visible]
        matches = []
        
        for keyword in keywords:
            for s in symbol_names:
                if keyword.upper() in s.upper() and s not in matches:
                    matches.append(s)
        
        return matches
    
    def fetch_multi_timeframe_data(self, symbol, days=365):
        """
        Fetch data for a symbol across multiple timeframes.
        Returns dict of {timeframe_name: DataFrame}
        """
        timeframes = {
            'M15': (mt5.TIMEFRAME_M15, 96),  # 96 bars per day
            'H1': (mt5.TIMEFRAME_H1, 24),
            'H4': (mt5.TIMEFRAME_H4, 6),
            'D1': (mt5.TIMEFRAME_D1, 1)
        }
        
        results = {}
        
        for tf_name, (tf_const, bars_per_day) in timeframes.items():
            count = days * bars_per_day
            logger.info(f"  {tf_name}: Fetching {count} bars...")
            
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, count)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"  {tf_name}: No data")
                continue
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate comprehensive indicators
            df = self.calculate_all_indicators(df)
            
            results[tf_name] = df
            logger.info(f"  {tf_name}: ✓ {len(df)} bars ({df['time'].min()} to {df['time'].max()})")
        
        return results
    
    def calculate_all_indicators(self, df):
        """Calculate ALL technical indicators needed for institutional testing."""
        
        # 1. RSI (14 period)
        df['RSI'] = self.calculate_rsi(df['close'], 14)
        
        # 2. Volume Indicators
        df['Avg_Volume'] = df['tick_volume'].rolling(20).mean()
        df['Rel_Volume'] = df['tick_volume'] / df['Avg_Volume']
        df['Volume_Surge'] = (df['Rel_Volume'] > 2.0).astype(int)
        
        # 3. ATR (Volatility)
        df['ATR'] = self.calculate_atr(df, 14)
        df['ATR_Pct'] = (df['ATR'] / df['close']) * 100
        
        # 4. Moving Averages
        for period in [20, 50, 200]:
            df[f'SMA_{period}'] = df['close'].rolling(period).mean()
            df[f'Distance_SMA_{period}'] = ((df['close'] - df[f'SMA_{period}']) / df[f'SMA_{period}']) * 100
        
        # 5. Golden/Death Cross
        df['Golden_Cross'] = ((df['SMA_50'] > df['SMA_200']) & 
                              (df['SMA_50'].shift(1) <= df['SMA_200'].shift(1))).astype(int)
        df['Death_Cross'] = ((df['SMA_50'] < df['SMA_200']) & 
                             (df['SMA_50'].shift(1) >= df['SMA_200'].shift(1))).astype(int)
        
        # 6. Bollinger Bands
        sma_20 = df['close'].rolling(20).mean()
        std_20 = df['close'].rolling(20).std()
        df['BB_Upper'] = sma_20 + (2 * std_20)
        df['BB_Lower'] = sma_20 - (2 * std_20)
        df['BB_Width'] = ((df['BB_Upper'] - df['BB_Lower']) / sma_20) * 100
        
        # 7. ADX (Trend Strength)
        df['ADX'] = self.calculate_adx(df, 14)
        
        # 8. High/Low Tracking
        for period in [20, 52]:
            df[f'High_{period}'] = df['high'].rolling(period).max()
            df[f'Low_{period}'] = df['low'].rolling(period).min()
            df[f'Near_High_{period}'] = (df['close'] >= df[f'High_{period}'] * 0.98).astype(int)
            df[f'Near_Low_{period}'] = (df['close'] <= df[f'Low_{period}'] * 1.02).astype(int)
        
        # 9. Price Change
        df['Change_Pct'] = df['close'].pct_change() * 100
        df['Change_3bar'] = ((df['close'] - df['close'].shift(3)) / df['close'].shift(3)) * 100
        
        # 10. Trend Classification
        df['Trend'] = 'Neutral'
        df.loc[df['close'] > df['SMA_200'], 'Trend'] = 'Uptrend'
        df.loc[df['close'] < df['SMA_200'], 'Trend'] = 'Downtrend'
        
        return df
    
    def calculate_rsi(self, series, period=14):
        """RSI calculation."""
        delta = series.diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = -delta.where(delta < 0, 0).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def calculate_atr(self, df, period=14):
        """ATR calculation."""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    def calculate_adx(self, df, period=14):
        """ADX calculation (simplified)."""
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = self.calculate_atr(df, 1) * period  # Approximate
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / tr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / tr)
        
        dx = (np.abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
        adx = dx.rolling(period).mean()
        
        return adx
    
    def save_dataset(self, symbol, timeframe, df):
        """Save dataset to CSV."""
        filename = self.data_dir / f"{symbol}_{timeframe}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"  Saved: {filename} ({len(df)} rows)")
        return filename

if __name__ == "__main__":
    collector = ComprehensiveDataCollector()
    
    if not collector.connect():
        exit(1)
    
    # Define target symbols
    symbol_keywords = ["GOLD", "XAU", "SILVER", "XAG", "US100", "NAS", "US30"]
    
    logger.info("Searching for available symbols...")
    available = collector.get_available_symbols(symbol_keywords)
    logger.info(f"Found {len(available)} matching symbols: {available}")
    
    # Select top 5
    target_symbols = available[:5]
    
    if not target_symbols:
        logger.error("No symbols found! Check MT5 Market Watch.")
        mt5.shutdown()
        exit(1)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Starting comprehensive data collection for {len(target_symbols)} symbols")
    logger.info(f"{'='*60}\n")
    
    for symbol in target_symbols:
        logger.info(f"\n[{symbol}] Collecting multi-timeframe data...")
        
        data = collector.fetch_multi_timeframe_data(symbol, days=365)
        
        for tf_name, df in data.items():
            collector.save_dataset(symbol, tf_name, df)
    
    mt5.shutdown()
    logger.info(f"\n{'='*60}")
    logger.info("✅ Data collection complete!")
    logger.info(f"Files saved to: {collector.data_dir.absolute()}")
    logger.info(f"{'='*60}")
