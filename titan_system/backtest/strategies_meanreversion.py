"""
MEAN REVERSION STRATEGIES
==========================
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class BB_Reversal(BaseStrategy):
    """Bollinger Band mean reversion"""
    
    def __init__(self):
        super().__init__("BB Reversal")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        
        # Buy when price touches lower band
        if curr['close'] <= curr['bb_lower'] and curr['rsi'] < 40:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 1.5),
                'take_profit': curr['bb_mid']  # Target middle band
            }
        
        # Sell when price touches upper band
        if curr['close'] >= curr['bb_upper'] and curr['rsi'] > 60:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 1.5),
                'take_profit': curr['bb_mid']
            }
        
        return None


class RSI_Extreme_Reversal(BaseStrategy):
    """RSI oversold/overbought reversal"""
    
    def __init__(self):
        super().__init__("RSI Extreme Reversal")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Oversold reversal
        if prev['rsi'] < 30 and curr['rsi'] >= 30:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Overbought reversal
        if prev['rsi'] > 70 and curr['rsi'] <= 70:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class Support_Resistance_Bounce(BaseStrategy):
    """Support/resistance level bounces"""
    
    def __init__(self):
        super().__init__("S/R Bounce")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        # Calculate support/resistance levels
        df['support'] = df['low'].rolling(20).min()
        df['resistance'] = df['high'].rolling(20).max()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        
        # Bounce off support
        if curr['low'] <= curr['support'] * 1.001:  # Within 0.1%
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['support'] - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Bounce off resistance
        if curr['high'] >= curr['resistance'] * 0.999:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['resistance'] + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class Range_Trading(BaseStrategy):
    """Trade within a defined range"""
    
    def __init__(self):
        super().__init__("Range Trading")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['range_high'] = df['high'].rolling(50).max()
        df['range_low'] = df['low'].rolling(50).min()
        df['range_mid'] = (df['range_high'] + df['range_low']) / 2
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        
        range_size = curr['range_high'] - curr['range_low']
        
        # Buy at bottom of range
        if curr['close'] <= curr['range_low'] + (range_size * 0.2):
            return {
                'direction': 'BUY',
                'stop_loss': curr['range_low'],
                'take_profit': curr['range_mid']
            }
        
        # Sell at top of range
        if curr['close'] >= curr['range_high'] - (range_size * 0.2):
            return {
                'direction': 'SELL',
                'stop_loss': curr['range_high'],
                'take_profit': curr['range_mid']
            }
        
        return None


class Stochastic_Reversal(BaseStrategy):
    """Stochastic oversold/overbought reversal"""
    
    def __init__(self):
        super().__init__("Stochastic Reversal")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Oversold reversal
        if prev['stoch_k'] < 20 and curr['stoch_k'] >= 20:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Overbought reversal
        if prev['stoch_k'] > 80 and curr['stoch_k'] <= 80:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None
