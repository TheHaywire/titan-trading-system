"""
STRATEGY BASE CLASS
===================
Base class that all strategies inherit from.
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, name: str, params: dict = None):
        self.name = name
        self.params = params or {}
    
    @abstractmethod
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all indicators needed for this strategy"""
        pass
    
    @abstractmethod
    def analyze(self, df: pd.DataFrame) -> dict:
        """
        Analyze current market state and return signal.
        
        Returns:
            dict with keys: direction ('BUY' or 'SELL'), stop_loss, take_profit
            or None if no signal
        """
        pass
    
    def check_exit(self, df: pd.DataFrame, position: dict) -> str:
        """
        Check if we should exit the position.
        
        Returns:
            Exit reason string or None
        """
        current = df.iloc[-1]
        
        # Check SL/TP
        if position['direction'] == 'BUY':
            if position['sl'] and current['low'] <= position['sl']:
                return 'Stop Loss'
            if position['tp'] and current['high'] >= position['tp']:
                return 'Take Profit'
        else:
            if position['sl'] and current['high'] >= position['sl']:
                return 'Stop Loss'
            if position['tp'] and current['low'] <= position['tp']:
                return 'Take Profit'
        
        return None


def wilders_smoothing(series: pd.Series, period: int) -> pd.Series:
    """Wilder's Smoothing (Running Moving Average). Used by MT5."""
    return series.ewm(alpha=1/period, adjust=False).mean()


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add common indicators to dataframe, using Wilder's Smoothing where appropriate."""
    
    # EMAs (Standard EMA)
    df['ema9'] = df['close'].ewm(span=9).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    df['ema200'] = df['close'].ewm(span=200).mean()
    
    # RSI (Uses Wilder's Smoothing/RMA)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta.where(delta < 0, 0))
    
    avg_gain = wilders_smoothing(gain, 14)
    avg_loss = wilders_smoothing(loss, 14)
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ATR (Uses Wilder's Smoothing/RMA)
    high_low = df['high'] - df['low']
    high_close = abs(df['high'] - df['close'].shift())
    low_close = abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = wilders_smoothing(tr, 14)
    
    # MACD
    ema12 = df['close'].ewm(span=12).mean()
    ema26 = df['close'].ewm(span=26).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    
    # Bollinger Bands
    df['bb_mid'] = df['close'].rolling(20).mean()
    bb_std = df['close'].rolling(20).std()
    df['bb_upper'] = df['bb_mid'] + (2 * bb_std)
    df['bb_lower'] = df['bb_mid'] - (2 * bb_std)
    
    # ADX (Uses Wilder's Smoothing/RMA)
    plus_dm = df['high'].diff()
    minus_dm = -df['low'].diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    atr14 = df['atr']
    plus_di = 100 * (wilders_smoothing(plus_dm, 14) / atr14)
    minus_di = 100 * (wilders_smoothing(minus_dm, 14) / atr14)
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    df['adx'] = wilders_smoothing(dx, 14)
    
    # Stochastic
    low14 = df['low'].rolling(14).min()
    high14 = df['high'].rolling(14).max()
    df['stoch_k'] = 100 * (df['close'] - low14) / (high14 - low14).replace(0, np.nan)
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()
    
    return df
