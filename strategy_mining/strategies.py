"""
Vectorized Trading Strategies for Mining Engine
Optimized for speed using NumPy and Pandas vectorization.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import logging

# Setup logging
logger = logging.getLogger(__name__)

class AlphaArchetypes:
    """Collection of vectorized strategy implementations."""
    
    @staticmethod
    def mean_reversion_zscore_vwap(df: pd.DataFrame, vwap_window: int = 20, z_threshold: float = 2.0) -> pd.Series:
        """
        Archetype: Mean Reversion
        Logic: Z-Score of Price relative to VWAP.
        Returns: Signal Series (+1 for Long, -1 for Short, 0 for None)
        """
        # Calculate VWAP: (Price * Volume).cumsum() / Volume.cumsum()
        # Using typical price (H+L+C)/3 for better sensitivity
        tp = (df['high'] + df['low'] + df['close']) / 3
        v = df['volume']
        
        # Rolling VWAP
        tpv = tp * v
        vwap = tpv.rolling(window=vwap_window).sum() / v.rolling(window=vwap_window).sum()
        
        # Rolling Standard Deviation
        std = df['close'].rolling(window=vwap_window).std()
        
        # Z-Score
        z_score = (df['close'] - vwap) / std
        
        # Signals
        signals = pd.Series(0, index=df.index)
        signals[z_score < -z_threshold] = 1   # Oversold -> Long
        signals[z_score > z_threshold] = -1   # Overbought -> Short
        
        return signals

    @staticmethod
    def trend_following_ema_cross(df: pd.DataFrame, fast_period: int = 5, slow_period: int = 20) -> pd.Series:
        """
        Archetype: Trend Following
        Logic: Dual EMA Crossover.
        Returns: Signal Series
        """
        ema_fast = df['close'].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow_period, adjust=False).mean()
        
        signals = pd.Series(0, index=df.index)
        signals[ema_fast > ema_slow] = 1   # Uptrend
        signals[ema_fast < ema_slow] = -1  # Downtrend
        
        return signals

    @staticmethod
    def volatility_expansion_keltner(df: pd.DataFrame, ema_period: int = 20, atr_period: int = 14, multiplier: float = 2.0) -> pd.Series:
        """
        Archetype: Volatility Expansion
        Logic: ATR-based Keltner Channel Breakout.
        Returns: Signal Series
        """
        # Middle Band
        basis = df['close'].ewm(span=ema_period, adjust=False).mean()
        
        # ATR Calculation
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=atr_period).mean()
        
        upper_band = basis + (multiplier * atr)
        lower_band = basis - (multiplier * atr)
        
        signals = pd.Series(0, index=df.index)
        signals[df['close'] > upper_band] = 1   # Breakout Up
        signals[df['close'] < lower_band] = -1  # Breakout Down
        
        return signals

def calculate_performance_vectorized(df: pd.DataFrame, signals: pd.Series) -> Dict[str, Any]:
    """
    Calculate strategy performance metrics using vectorization.
    df must include 'close' price.
    """
    # Returns (shifted signal to avoid lookahead bias)
    next_returns = df['close'].pct_change().shift(-1)
    
    # Strategy returns
    strat_returns = signals * next_returns
    
    # Metrics
    win_rate = (strat_returns > 0).sum() / (strat_returns != 0).sum() if (strat_returns != 0).sum() > 0 else 0
    total_return = strat_returns.sum()
    sharpe = np.sqrt(252) * strat_returns.mean() / strat_returns.std() if strat_returns.std() != 0 else 0
    
    # Profit Factor
    gross_profits = strat_returns[strat_returns > 0].sum()
    gross_losses = abs(strat_returns[strat_returns < 0].sum())
    profit_factor = gross_profits / gross_losses if gross_losses != 0 else 0
    
    return {
        'total_return': total_return,
        'win_rate': win_rate,
        'sharpe_ratio': sharpe,
        'profit_factor': profit_factor,
        'num_trades': (signals != 0).sum()
    }
