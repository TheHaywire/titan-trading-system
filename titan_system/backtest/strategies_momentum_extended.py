"""
ADDITIONAL MOMENTUM STRATEGIES
===============================
Extended momentum strategy collection.
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class ParabolicSAR_Strategy(BaseStrategy):
    """Parabolic SAR trend following"""
    
    def __init__(self):
        super().__init__("Parabolic SAR")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Simplified SAR calculation
        # (Full SAR is complex, this is approximation using ATR)
        df['sar'] = df['close'].shift(1)  # Placeholder
        df['sar_direction'] = (df['close'] > df['sar']).astype(int) * 2 - 1
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 5:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Direction change
        if prev['sar_direction'] < 0 and curr['sar_direction'] > 0:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['sar'],
                'take_profit': curr['close'] + (atr * 3)
            }
        
        if prev['sar_direction'] > 0 and curr['sar_direction'] < 0:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['sar'],
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class WilliamsR_Strategy(BaseStrategy):
    """Williams %R oscillator"""
    
    def __init__(self):
        super().__init__("Williams %R")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Williams %R = (Highest High - Close) / (Highest High - Lowest Low) * -100
        high14 = df['high'].rolling(14).max()
        low14 = df['low'].rolling(14).min()
        df['williams_r'] = ((high14 - df['close']) / (high14 - low14)) * -100
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Oversold reversal (< -80 then crosses above)
        if prev['williams_r'] < -80 and curr['williams_r'] >= -80:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Overbought reversal (> -20 then crosses below)
        if prev['williams_r'] > -20 and curr['williams_r'] <= -20:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class ROC_Strategy(BaseStrategy):
    """Rate of Change momentum"""
    
    def __init__(self):
        super().__init__("Rate of Change")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # ROC = (Close - Close[n]) / Close[n] * 100
        period = 12
        df['roc'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Positive momentum acceleration
        if prev['roc'] <= 0 and curr['roc'] > 0:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Negative momentum acceleration
        if prev['roc'] >= 0 and curr['roc'] < 0:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class CCI_Strategy(BaseStrategy):
    """Commodity Channel Index"""
    
    def __init__(self):
        super().__init__("CCI")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # CCI = (Typical Price - SMA) / (0.015 * Mean Deviation)
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        sma = df['tp'].rolling(20).mean()
        mad = (df['tp'] - sma).abs().rolling(20).mean()
        df['cci'] = (df['tp'] - sma) / (0.015 * mad)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Oversold (< -100) reversal
        if prev['cci'] < -100 and curr['cci'] >= -100:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Overbought (> 100) reversal
        if prev['cci'] > 100 and curr['cci'] <= 100:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class EMA_Golden_Cross(BaseStrategy):
    """EMA 50/200 Golden Cross - classic long-term signal"""
    
    def __init__(self):
        super().__init__("Golden Cross 50/200")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return add_indicators(df)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 205:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Golden Cross
        if prev['ema50'] <= prev['ema200'] and curr['ema50'] > curr['ema200']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 3),
                'take_profit': curr['close'] + (atr * 6)
            }
        
        # Death Cross
        if prev['ema50'] >= prev['ema200'] and curr['ema50'] < curr['ema200']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 3),
                'take_profit': curr['close'] - (atr * 6)
            }
        
        return None


class MFI_Strategy(BaseStrategy):
    """Money Flow Index - volume-weighted RSI"""
    
    def __init__(self):
        super().__init__("Money Flow Index")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Typical Price
        df['tp'] = (df['high'] + df['low'] + df['close']) / 3
        # Money Flow
        df['mf'] = df['tp'] * df['tick_volume']
        
        # Positive and Negative Money Flow
        df['mf_pos'] = df['mf'].where(df['tp'] > df['tp'].shift(), 0)
        df['mf_neg'] = df['mf'].where(df['tp'] < df['tp'].shift(), 0)
        
        # MFI
        mf_ratio = df['mf_pos'].rolling(14).sum() / df['mf_neg'].rolling(14).sum()
        df['mfi'] = 100 - (100 / (1 + mf_ratio))
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Oversold reversal
        if prev['mfi'] < 20 and curr['mfi'] >= 20:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # Overbought reversal
        if prev['mfi'] > 80 and curr['mfi'] <= 80:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class TripleEMA_Strategy(BaseStrategy):
    """Triple EMA (8/21/55) confluence"""
    
    def __init__(self):
        super().__init__("Triple EMA 8/21/55")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        df['ema8'] = df['close'].ewm(span=8).mean()
        df['ema55'] = df['close'].ewm(span=55).mean()
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 60:
            return None
        
        curr = df.iloc[-1]
        
        # All EMAs aligned bullish
        if curr['ema8'] > curr['ema21'] > curr['ema55']:
            # Entry on pullback to EMA21
            if curr['close'] <= curr['ema21'] * 1.002:  # Within 0.2%
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['ema55'],
                    'take_profit': curr['close'] + (atr * 4)
                }
        
        # All EMAs aligned bearish
        if curr['ema8'] < curr['ema21'] < curr['ema55']:
            if curr['close'] >= curr['ema21'] * 0.998:
                atr = curr['atr']
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['ema55'],
                    'take_profit': curr['close'] - (atr * 4)
                }
        
        return None


class DMI_Strategy(BaseStrategy):
    """Directional Movement Index"""
    
    def __init__(self):
        super().__init__("DMI")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Calculate +DI and -DI (simplified)
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        plus_dm = df['high'].diff()
        minus_dm = -df['low'].diff()
        plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
        minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
        
        atr14 = tr.rolling(14).mean()
        df['plus_di'] = 100 * (plus_dm.rolling(14).mean() / atr14)
        df['minus_di'] = 100 * (minus_dm.rolling(14).mean() / atr14)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # +DI crosses above -DI
        if prev['plus_di'] <= prev['minus_di'] and curr['plus_di'] > curr['minus_di']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - (atr * 2),
                'take_profit': curr['close'] + (atr * 4)
            }
        
        # -DI crosses above +DI
        if prev['plus_di'] >= prev['minus_di'] and curr['plus_di'] < curr['minus_di']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + (atr * 2),
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None
