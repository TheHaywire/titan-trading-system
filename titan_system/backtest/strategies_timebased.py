"""
TIME-BASED STRATEGIES
=====================
Strategies based on specific trading sessions and time patterns.
"""

import pandas as pd
import numpy as np
from datetime import time
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class LondonOpen_Breakout(BaseStrategy):
    """London Open breakout (08:00 GMT)"""
    
    def __init__(self):
        super().__init__("London Open Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Identify London open (08:00 GMT)
        df['hour'] = pd.to_datetime(df['time']).dt.hour
        df['is_london_open'] = (df['hour'] >= 8) & (df['hour'] < 9)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        
        # Only trade during London session
        if not curr.get('is_london_open', False):
            return None
        
        # Get pre-London range (previous 2 hours)
        recent = df.tail(10)
        pre_range_high = recent['high'].max()
        pre_range_low = recent['low'].min()
        
        # Breakout above
        if curr['close'] > pre_range_high:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': pre_range_high - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Breakout below
        if curr['close'] < pre_range_low:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': pre_range_low + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class NewYorkOpen_Breakout(BaseStrategy):
    """New York Open breakout (13:30 GMT)"""
    
    def __init__(self):
        super().__init__("NY Open Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['hour'] = pd.to_datetime(df['time']).dt.hour
        df['is_ny_open'] = (df['hour'] >= 13) & (df['hour'] < 15)
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        
        if not curr.get('is_ny_open', False):
            return None
        
        recent = df.tail(10)
        pre_high = recent['high'].max()
        pre_low = recent['low'].min()
        
        if curr['close'] > pre_high:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': pre_high - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        if curr['close'] < pre_low:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': pre_low + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class AsianSession_Range(BaseStrategy):
    """Asian session range trading (00:00-08:00 GMT)"""
    
    def __init__(self):
        super().__init__("Asian Range")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['hour'] = pd.to_datetime(df['time']).dt.hour
        df['is_asian'] = (df['hour'] >= 0) & (df['hour'] < 8)
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        
        # Only trade during Asian session
        if not curr.get('is_asian', False):
            return None
        
        # Range trading within Asian bounds
        asian_data = df[df['is_asian']].tail(20)
        if len(asian_data) < 5:
            return None
        
        asian_high = asian_data['high'].max()
        asian_low = asian_data['low'].min()
        asian_mid = (asian_high + asian_low) / 2
        
        # Buy at bottom of range
        if curr['close'] <= asian_low + ((asian_high - asian_low) * 0.2):
            return {
                'direction': 'BUY',
                'stop_loss': asian_low,
                'take_profit': asian_mid
            }
        
        # Sell at top of range
        if curr['close'] >= asian_high - ((asian_high - asian_low) * 0.2):
            return {
                'direction': 'SELL',
                'stop_loss': asian_high,
                'take_profit': asian_mid
            }
        
        return None
