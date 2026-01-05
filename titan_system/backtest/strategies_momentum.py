"""
MOMENTUM STRATEGIES
===================
Collection of momentum-based trading strategies.
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class EMA_Cross_9_21(BaseStrategy):
    """EMA 9/21 crossover strategy"""
    
    def __init__(self):
        super().__init__("EMA Cross 9/21")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish cross
        if prev['ema9'] <= prev['ema21'] and curr['ema9'] > curr['ema21']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Bearish cross
        if prev['ema9'] >= prev['ema21'] and curr['ema9'] < curr['ema21']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class EMA_Cross_21_50(BaseStrategy):
    """EMA 21/50 crossover strategy"""
    
    def __init__(self):
        super().__init__("EMA Cross 21/50")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        if prev['ema21'] <= prev['ema50'] and curr['ema21'] > curr['ema50']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        if prev['ema21'] >= prev['ema50'] and curr['ema21'] < curr['ema50']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class MACD_Signal(BaseStrategy):
    """MACD signal line crossover"""
    
    def __init__(self):
        super().__init__("MACD Signal Cross")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish cross
        if prev['macd'] <= prev['macd_signal'] and curr['macd'] > curr['macd_signal']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Bearish cross
        if prev['macd'] >= prev['macd_signal'] and curr['macd'] < curr['macd_signal']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class RSI_Momentum(BaseStrategy):
    """RSI momentum strategy - trade when RSI crosses 50"""
    
    def __init__(self):
        super().__init__("RSI Momentum")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # RSI crosses above 50 (bullish)
        if prev['rsi'] <= 50 and curr['rsi'] > 50:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # RSI crosses below 50 (bearish)
        if prev['rsi'] >= 50 and curr['rsi'] < 50:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class ADX_Trend(BaseStrategy):
    """ADX trend following - trade when ADX > 25 and price follows EMA"""
    
    def __init__(self):
        super().__init__("ADX Trend Following")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Strong trend detected
        if curr['adx'] > 25:
            # Bullish trend
            if curr['close'] > curr['ema21'] and prev['close'] <= prev['ema21']:
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - (atr * 2),
                    'take_profit': curr['close'] + (atr * 4)
                }
            
            # Bearish trend
            if curr['close'] < curr['ema21'] and prev['close'] >= prev['ema21']:
                atr = curr['atr']
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + (atr * 2),
                    'take_profit': curr['close'] - (atr * 4)
                }
        
        return None


class Stochastic_Momentum(BaseStrategy):
    """Stochastic oscillator momentum"""
    
    def __init__(self):
        super().__init__("Stochastic Momentum")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 2:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Bullish cross above 20
        if prev['stoch_k'] <= prev['stoch_d'] and curr['stoch_k'] > curr['stoch_d'] and curr['stoch_k'] < 30:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Bearish cross below 80
        if prev['stoch_k'] >= prev['stoch_d'] and curr['stoch_k'] < curr['stoch_d'] and curr['stoch_k'] > 70:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None
