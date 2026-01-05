"""
VOLATILITY STRATEGIES
=====================
Strategies based on volatility patterns and ATR variations.
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class KeltnerChannel_Breakout(BaseStrategy):
    """Keltner Channel breakout strategy"""
    
    def __init__(self):
        super().__init__("Keltner Channel Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Keltner Channels = EMA ± (ATR * multiplier)
        df['kc_mid'] = df['ema21']
        df['kc_upper'] = df['kc_mid'] + (df['atr'] * 2)
        df['kc_lower'] = df['kc_mid'] - (df['atr'] * 2)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        
        # Breakout above upper channel
        if curr['close'] > curr['kc_upper']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['kc_mid'],
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Breakout below lower channel
        if curr['close'] < curr['kc_lower']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['kc_mid'],
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class VolatilityContraction_Expansion(BaseStrategy):
    """Trade volatility contraction followed by expansion"""
    
    def __init__(self):
        super().__init__("Vol Contraction-Expansion")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Volatility ratio
        df['atr_avg'] = df['atr'].rolling(20).mean()
        df['vol_ratio'] = df['atr'] / df['atr_avg']
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Contraction then expansion (squeeze then break)
        if prev['vol_ratio'] < 0.7 and curr['vol_ratio'] > 1.2:
            # Direction based on price action
            if curr['close'] > prev['close']:
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - (atr * 2),
                    'take_profit': curr['close'] + (atr * 4)
                }
            else:
                atr = curr['atr']
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + (atr * 2),
                    'take_profit': curr['close'] - (atr * 4)
                }
        
        return None


class DonchianChannel_Breakout(BaseStrategy):
    """Donchian Channel (high/low channel) breakout"""
    
    def __init__(self, period=20):
        super().__init__(f"Donchian {period}")
        self.period = period
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['don_upper'] = df['high'].rolling(self.period).max()
        df['don_lower'] = df['low'].rolling(self.period).min()
        df['don_mid'] = (df['don_upper'] + df['don_lower']) / 2
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < self.period + 5:
            return None
        
        curr = df.iloc[-1]
        
        # Breakout above
        if curr['close'] > curr['don_upper']:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['don_mid'],
                'take_profit': curr['close'] + (atr * 3)
            }
        
        # Breakout below
        if curr['close'] < curr['don_lower']:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['don_mid'],
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None
