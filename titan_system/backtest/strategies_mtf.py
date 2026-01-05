"""
MULTI-TIMEFRAME (MTF) STRATEGIES
=================================
Strategies that combine signals from multiple timeframes for confluence.
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
import MetaTrader5 as mt5


class H4_Trend_M15_Entry(BaseStrategy):
    """H4 trend direction with M15 entry timing"""
    
    def __init__(self):
        super().__init__("H4 Trend + M15 Entry")
        self.symbol = None
        self.h4_trend = None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        # This would need H4 data as well
        # For backtest simplicity, using single TF EMA
        if len(df) < 50:
            return None
        
        curr = df.iloc[-1]
        
        # Simulate H4 trend using EMA200
        h4_bullish = curr['ema200'] is not None and curr['close'] > curr['ema200']
        h4_bearish = curr['ema200'] is not None and curr['close'] < curr['ema200']
        
        # M15 entry on EMA21 cross
        prev = df.iloc[-2]
        
        if h4_bullish and prev['close'] <= prev['ema21'] and curr['close'] > curr['ema21']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        if h4_bearish and prev['close'] >= prev['ema21'] and curr['close'] < curr['ema21']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class Daily_Bias_H1_Entry(BaseStrategy):
    """Daily trend bias with H1 entry"""
    
    def __init__(self):
        super().__init__("Daily Bias + H1 Entry")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Daily bias = EMA50 direction
        daily_bullish = curr['ema50'] is not None and curr['ema50'] > curr['ema50']
        daily_bearish = curr['ema50'] is not None and curr['ema50'] < prev['ema50']
        
        # H1 entry on pullback
        if daily_bullish and curr['rsi'] < 40:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        if daily_bearish and curr['rsi'] > 60:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None
