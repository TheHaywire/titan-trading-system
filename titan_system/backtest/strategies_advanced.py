"""
ADDITIONAL STRATEGIES - BATCH 1 (Next 15 Quick Wins)
=====================================================
Expanding beyond initial 40 strategies
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


# 1. ICHIMOKU CLOUD
class Ichimoku_Strategy(BaseStrategy):
    """Ichimoku Cloud complete system"""
    
    def __init__(self):
        super().__init__("Ichimoku Cloud")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Tenkan-sen (Conversion Line): 9-period
        high_9 = df['high'].rolling(9).max()
        low_9 = df['low'].rolling(9).min()
        df['tenkan'] = (high_9 + low_9) / 2
        
        # Kijun-sen (Base Line): 26-period
        high_26 = df['high'].rolling(26).max()
        low_26 = df['low'].rolling(26).min()
        df['kijun'] = (high_26 + low_26) / 2
        
        # Senkou Span A (Leading Span A)
        df['senkou_a'] = ((df['tenkan'] + df['kijun']) / 2).shift(26)
        
        # Senkou Span B (Leading Span B): 52-period
        high_52 = df['high'].rolling(52).max()
        low_52 = df['low'].rolling(52).min()
        df['senkou_b'] = ((high_52 + low_52) / 2).shift(26)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 60:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # BUY: Tenkan crosses above Kijun + price above cloud
        if (prev['tenkan'] <= prev['kijun'] and curr['tenkan'] > curr['kijun'] and
            curr['close'] > max(curr['senkou_a'], curr['senkou_b'])):
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['kijun'],
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # SELL: Tenkan crosses below Kijun + price below cloud
        if (prev['tenkan'] >= prev['kijun'] and curr['tenkan'] < curr['kijun'] and
            curr['close'] < min(curr['senkou_a'], curr['senkou_b'])):
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['kijun'],
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


# 2. VWAP STRATEGY
class VWAP_Strategy(BaseStrategy):
    """Volume Weighted Average Price"""
    
    def __init__(self):
        super().__init__("VWAP")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # VWAP = Cumulative(Price × Volume) / Cumulative(Volume)
        df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
        df['vwap'] = (df['typical_price'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
        
        # VWAP deviation
        df['vwap_std'] = df['typical_price'].rolling(20).std()
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # BUY: Price crosses above VWAP from below
        if prev['close'] < prev['vwap'] and curr['close'] > curr['vwap']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['vwap'] - atr,
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # SELL: Price crosses below VWAP from above
        if prev['close'] > prev['vwap'] and curr['close'] < curr['vwap']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['vwap'] + atr,
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


# 3. PIVOT POINTS
class PivotPoints_Strategy(BaseStrategy):
    """Daily Pivot Point trading"""
    
    def __init__(self):
        super().__init__("Pivot Points")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Daily pivot
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        prev_close = df['close'].shift(1)
        
        df['pivot'] = (prev_high + prev_low + prev_close) / 3
        df['r1'] = 2 * df['pivot'] - prev_low
        df['s1'] = 2 * df['pivot'] - prev_high
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        
        # BUY at S1 support
        if curr['low'] <= curr['s1'] and curr['close'] > curr['s1']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['s1'] - atr,
                'take_profit': curr['pivot']
            }
        
        # SELL at R1 resistance  
        if curr['high'] >= curr['r1'] and curr['close'] < curr['r1']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['r1'] + atr,
                'take_profit': curr['pivot']
            }
        
        return None


# 4. SUPERTREND
class Supertrend_Strategy(BaseStrategy):
    """Supertrend indicator"""
    
    def __init__(self):
        super().__init__("Supertrend")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Supertrend calculation
        multiplier = 3
        df['hl_avg'] = (df['high'] + df['low']) / 2
        df['basic_ub'] = df['hl_avg'] + (multiplier * df['atr'])
        df['basic_lb'] = df['hl_avg'] - (multiplier * df['atr'])
        
        # Simplified supertrend
        df['supertrend'] = df['basic_ub']
        df['trend'] = -1
        
        for i in range(1, len(df)):
            if df.loc[df.index[i], 'close'] > df.loc[df.index[i-1], 'supertrend']:
                df.loc[df.index[i], 'trend'] = 1
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'basic_lb']
            else:
                df.loc[df.index[i], 'trend'] = -1
                df.loc[df.index[i], 'supertrend'] = df.loc[df.index[i], 'basic_ub']
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # BUY: Trend flips to bullish
        if prev['trend'] == -1 and curr['trend'] == 1:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['supertrend'],
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # SELL: Trend flips to bearish
        if prev['trend'] == 1 and curr['trend'] == -1:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['supertrend'],
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


# 5. RSI + MACD CONFLUENCE
class RSI_MACD_Confluence(BaseStrategy):
    """Both RSI and MACD must confirm"""
    
    def __init__(self):
        super().__init__("RSI+MACD Confluence")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 30:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # BUY: RSI crosses above 50 AND MACD crosses above signal
        rsi_bull = prev['rsi'] <= 50 and curr['rsi'] > 50
        macd_bull = prev['macd'] <= prev['macd_signal'] and curr['macd'] > curr['macd_signal']
        
        if rsi_bull and macd_bull:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # SELL: Both confirm bearish
        rsi_bear = prev['rsi'] >= 50 and curr['rsi'] < 50
        macd_bear = prev['macd'] >= prev['macd_signal'] and curr['macd'] < curr['macd_signal']
        
        if rsi_bear and macd_bear:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None
