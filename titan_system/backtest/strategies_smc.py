"""
SMART MONEY CONCEPTS (SMC) STRATEGIES
======================================
Institutional trading concepts focusing on order blocks, liquidity, and market structure.
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class OrderBlock_Strategy(BaseStrategy):
    """Trade based on order blocks (institutional buying/selling zones)"""
    
    def __init__(self):
        super().__init__("Order Block")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Identify order blocks (strong move followed by consolidation)
        df['body'] = abs(df['close'] - df['open'])
        df['range'] = df['high'] - df['low']
        df['strong_candle'] = df['body'] > (df['range'] * 0.7)
        
        # Bullish order block = strong down move followed by reversal
        df['bullish_ob'] = (df['strong_candle'].shift(1) & 
                           (df['close'].shift(1) < df['open'].shift(1)) &
                           (df['close'] > df['open']))
        
        # Bearish order block = strong up move followed by reversal  
        df['bearish_ob'] = (df['strong_candle'].shift(1) & 
                           (df['close'].shift(1) > df['open'].shift(1)) &
                           (df['close'] < df['open']))
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        
        # Buy when price returns to bullish order block
        if curr.get('bullish_ob', False):
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['low'] - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Sell when price returns to bearish order block
        if curr.get('bearish_ob', False):
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['high'] + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class FairValueGap_Strategy(BaseStrategy):
    """Trade Fair Value Gaps (FVG) - imbalances in price"""
    
    def __init__(self):
        super().__init__("Fair Value Gap")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # FVG = gap between 3 consecutive candles
        # Bullish FVG: candle[1].low > candle[3].high
        df['bullish_fvg'] = df['low'].shift(1) > df['high'].shift(3)
        
        # Bearish FVG: candle[1].high < candle[3].low
        df['bearish_fvg'] = df['high'].shift(1) < df['low'].shift(3)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        
        if curr.get('bullish_fvg', False):
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        if curr.get('bearish_fvg', False):
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class BreakOfStructure_Strategy(BaseStrategy):
    """Break of Structure (BOS) - trend change detection"""
    
    def __init__(self):
        super().__init__("Break of Structure")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Identify swing highs and lows
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        # Last swing high/low
        df['last_swing_high'] = df[df['swing_high']]['high'].ffill()
        df['last_swing_low'] = df[df['swing_low']]['low'].ffill()
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish BOS: Price breaks above previous swing high
        if curr['close'] > curr.get('last_swing_high', float('inf')):
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr.get('last_swing_high', curr['close']) - (atr * 1),
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Bearish BOS: Price breaks below previous swing low
        if curr['close'] < curr.get('last_swing_low', float('-inf')):
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr.get('last_swing_low', curr['close']) + (atr * 1),
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class LiquidityGrab_Strategy(BaseStrategy):
    """Liquidity Grab - fakeout followed by reversal"""
    
    def __init__(self):
        super().__init__("Liquidity Grab")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Recent high/low
        df['recent_high'] = df['high'].rolling(10).max()
        df['recent_low'] = df['low'].rolling(10).min()
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 15:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish liquidity grab: Sweep low then reverse up
        if prev['low'] <= prev['recent_low'] and curr['close'] > prev['high']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': prev['low'] - (atr * 0.5),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Bearish liquidity grab: Sweep high then reverse down
        if prev['high'] >= prev['recent_high'] and curr['close'] < prev['low']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': prev['high'] + (atr * 0.5),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None
