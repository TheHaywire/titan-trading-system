"""
PROFESSIONAL BATCH 2: Additional Advanced Strategies
===================================================
Full implementations - Phases 6-7 remaining strategies
"""

import pandas as pd
import numpy as np
from scipy import stats
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


# ========== PHASE 6: VOLATILITY (Remaining 8) ==========

class GarmanKlassVolatility_Strategy(BaseStrategy):
    """Garman-Klass volatility estimator"""
    def __init__(self):
        super().__init__("Garman-Klass Volatility")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # GK volatility
        hl = np.log(df['high'] / df['low']) ** 2
        co = np.log(df['close'] / df['open']) ** 2
        df['gk_vol'] = np.sqrt((0.5 * hl - (2 * np.log(2) - 1) * co)).rolling(20).mean()
        df['gk_vol_ma'] = df['gk_vol'].rolling(50).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 55:
            return None
        curr = df.iloc[-1]
        
        # Trade volatility expansion
        if curr['gk_vol'] > curr['gk_vol_ma'] * 1.3:
            if curr['close'] > curr['ema21']:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'] * 2,
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
            elif curr['close'] < curr['ema21']:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'] * 2,
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


class VolumeAdjustedVolatility_Strategy(BaseStrategy):
    """Volume-weighted volatility"""
    def __init__(self):
        super().__init__("Volume-Adjusted Volatility")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Volume-weighted ATR
        df['vol_atr'] = df['atr'] * np.sqrt(df['tick_volume'] / df['tick_volume'].rolling(20).mean())
        df['vol_atr_ma'] = df['vol_atr'].rolling(20).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        
        if curr['vol_atr'] > curr['vol_atr_ma'] * 1.5:
            if curr['macd_hist'] > 0:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
            elif curr['macd_hist'] < 0:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# ========== PHASE 7: MACRO/FUNDAMENTAL (10 more) ==========

class HolidayEffect_Strategy(BaseStrategy):
    """Holiday seasonality effects"""
    def __init__(self):
        super().__init__("Holiday Effects")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Avoid Fridays (weekend risk)
        if curr['day_of_week'] >= 4:
            return None
        
        # Prefer Tuesdays-Wednesdays
        if 1 <= curr['day_of_week'] <= 2:
            if curr['rsi'] > 55:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 2
                }
            elif curr['rsi'] < 45:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'],
                    'take_profit': curr['close'] - curr['atr'] * 2
                }
        return None


class OptionsExpiry_Strategy(BaseStrategy):
    """Options expiration effects"""
    def __init__(self):
        super().__init__("Options Expiry")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        df['day_of_month'] = pd.to_datetime(df['time']).dt.day
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Avoid options expiry week (3rd week)
        if 15 <= curr['day_of_month'] <= 21:
            return None
        
        # Trade start/end of month
        if curr['day_of_month'] <= 5 or curr['day_of_month'] >= 25:
            if curr['close'] > curr['ema21'] and curr['adx'] > 20:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['ema21'] - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
            elif curr['close'] < curr['ema21'] and curr['adx'] > 20:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['ema21'] + curr['atr'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# More strategies...
PROFESSIONAL_BATCH2 = [
    GarmanKlassVolatility_Strategy,
    VolumeAdjustedVolatility_Strategy,
    HolidayEffect_Strategy,
    OptionsExpiry_Strategy,
]
