"""
BREAKOUT STRATEGIES
===================
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class HighLow_Breakout(BaseStrategy):
    """High/Low breakout of previous N bars"""
    
    def __init__(self, period=20):
        super().__init__(f"High/Low Breakout {period}")
        self.period = period
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df[f'high_{self.period}'] = df['high'].shift(1).rolling(self.period).max()
        df[f'low_{self.period}'] = df['low'].shift(1).rolling(self.period).min()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < self.period + 1:
            return None
        
        curr = df.iloc[-1]
        high_key = f'high_{self.period}'
        low_key = f'low_{self.period}'
        
        # Breakout above
        if curr['close'] > curr[high_key]:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr[high_key] - (atr * 1),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Breakout below
        if curr['close'] < curr[low_key]:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr[low_key] + (atr * 1),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class ATR_Breakout(BaseStrategy):
    """ATR-based volatility breakout"""
    
    def __init__(self):
        super().__init__("ATR Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['atr_avg'] = df['atr'].rolling(20).mean()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # ATR expansion with bullish bar
        if curr['atr'] > curr['atr_avg'] * 1.5 and curr['close'] > prev['close']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 1.5),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # ATR expansion with bearish bar
        if curr['atr'] > curr['atr_avg'] * 1.5 and curr['close'] < prev['close']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 1.5),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class BB_Squeeze_Breakout(BaseStrategy):
    """Bollinger Band squeeze breakout"""
    
    def __init__(self):
        super().__init__("BB Squeeze Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        df['bb_width_avg'] = df['bb_width'].rolling(20).mean()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Squeeze detected (low volatility)
        if prev['bb_width'] < prev['bb_width_avg'] * 0.7:
            # Breakout above upper band
            if curr['close'] > curr['bb_upper']:
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['bb_mid'],
                    'take_profit': curr['close'] + (atr * 4)
                }
            
            # Breakout below lower band
            if curr['close'] < curr['bb_lower']:
                atr = curr['atr']
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['bb_mid'],
                    'take_profit': curr['close'] - (atr * 4)
                }
        
        return None


class Volume_Breakout(BaseStrategy):
    """Volume-confirmed breakout"""
    
    def __init__(self):
        super().__init__("Volume Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['vol_avg'] = df['tick_volume'].rolling(20).mean()
        df['high_20'] = df['high'].shift(1).rolling(20).max()
        df['low_20'] = df['low'].shift(1).rolling(20).min()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 21:
            return None
        
        curr = df.iloc[-1]
        
        # High volume breakout above
        if curr['close'] > curr['high_20'] and curr['tick_volume'] > curr['vol_avg'] * 1.5:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['high_20'] - (atr * 1),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # High volume breakout below
        if curr['close'] < curr['low_20'] and curr['tick_volume'] > curr['vol_avg'] * 1.5:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['low_20'] + (atr * 1),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class Opening_Range_Breakout(BaseStrategy):
    """First hour range breakout"""
    
    def __init__(self):
        super().__init__("Opening Range Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        # Assuming M5 data - first 12 bars = 1 hour
        df['or_high'] = df['high'].shift(12).rolling(12).max()
        df['or_low'] = df['low'].shift(12).rolling(12).min()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        
        # Breakout above opening range
        if curr['close'] > curr['or_high']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['or_high'] - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Breakout below opening range
        if curr['close'] < curr['or_low']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['or_low'] + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None
