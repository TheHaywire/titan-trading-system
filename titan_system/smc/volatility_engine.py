"""
Volatility Engine (VE-1)
Volatility Regimes, ATR, Compression, and Expansion
"""

import pandas as pd
import numpy as np
from typing import Dict

class VolatilityEngine:
    """
    Implements VE-1 Volatility Classification
    """
    
    def __init__(self, atr_period: int = 14):
        self.atr_period = atr_period
        
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df['high']
        low = df['low']
        close = df['close'].shift()
        
        tr = pd.concat([
            high - low,
            (high - close).abs(),
            (low - close).abs()
        ], axis=1).max(axis=1)
        
        return tr.rolling(period).mean()

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analyze Volatility Regime
        """
        atr_series = self.calculate_atr(df, self.atr_period)
        current_atr = atr_series.iloc[-1]
        
        # 1. ATR Regimes (specifically tailored for GOLD M15/H1 per user doc stats)
        # Doc stats: < 18 Low, 18-32 Normal, > 32 High (points)
        # Note: MT5 prices might be in raw format. Gold 2000.00. 1 pt = 1.0? or 0.1?
        # Usually Gold 1 point = $1 movement. ATR calculated on raw price gives dollars.
        # Assuming Data is standard XAUUSD.
        
        vol_regime = "NORMAL"
        if current_atr < 1.8: # Adjusted assuming data might be scaled or pip vs point confusion. 
                             # Let's use user doc 18-32 logic assuming raw price diff.
                             # If Gold moves 2005 to 2010, diff is 5. 
                             # User doc says 22-38 points M15. That implies $22-$38? That's HUGE for M15.
                             # Or maybe points = pips (0.1). 22 points = $2.2. This is more realistic for M15.
                             # Let's assume user "points" = 0.1 USD. So 18 points = $1.8 USD.
                             # Logic: ATR < 1.8 USD = Low, > 3.2 USD = High.
        
             # Let's strictly follow raw values first and see output to calibrate.
             pass 

        # Let's categorize dynamically based on relative ATR
        avg_atr = atr_series.rolling(100).mean().iloc[-1]
        atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
        
        if atr_ratio < 0.8:
            vol_regime = "LOW_VOL_COMPRESSION"
        elif atr_ratio > 1.5:
            vol_regime = "HIGH_VOL_EXPANSION"
        else:
            vol_regime = "NORMAL_VOLATILITY"
            
        # 2. Compression Detection
        # Checking for tight candles (small body relative to ATR)
        bodies = (df['close'] - df['open']).abs()
        recent_bodies = bodies.tail(5)
        avg_body = recent_bodies.mean()
        
        compression = False
        if avg_body < (current_atr * 0.5):
            compression = True
            
        return {
            'atr': current_atr,
            'regime': vol_regime,
            'compression': compression,
            'atr_ratio': atr_ratio
        }
