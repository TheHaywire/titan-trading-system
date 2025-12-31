"""
VWAP Engine (VE-2)
Implements Institutional VWAP interactions, deviations, and reclaims.
"""

import numpy as np
import pandas as pd
from typing import Dict

class VWAPEngine:
    """
    Calculates Volume Weighted Average Price and Standard Deviation Bands.
    """
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Calculate VWAP, Bands, and Current Regime.
        """
        # Ensure 'tick_volume' serves as volume proxy if 'real_volume' is missing/zero
        volume = df['tick_volume']
        
        # Typical Price
        tp = (df['high'] + df['low'] + df['close']) / 3
        
        # Cumulative VWAP Calculation (Anchored to start of data provided, usually session start)
        # Note: In a proper production session-based VWAP, we reset at session boundaries.
        # For H1 timeframe data, we might treat the supplied dataframe as the relevant window.
        
        vwap = (tp * volume).cumsum() / volume.cumsum()
        
        # Standard Deviation Bands Calculation
        # Variance = Average(Price^2) - Average(Price)^2
        # This is the "weighted" standard deviation formula used in institutional VWAPs
        
        vwap_var = (volume * (tp - vwap)**2).cumsum() / volume.cumsum()
        vwap_std = np.sqrt(vwap_var)
        
        df['vwap'] = vwap
        df['vwap_upper_1'] = vwap + vwap_std
        df['vwap_lower_1'] = vwap - vwap_std
        df['vwap_upper_2'] = vwap + (2 * vwap_std)
        df['vwap_lower_2'] = vwap - (2 * vwap_std)
        
        current_price = df['close'].iloc[-1]
        current_vwap = df['vwap'].iloc[-1]
        
        # Classify Regime
        regime = "NEUTRAL"
        if current_price > df['vwap_upper_1'].iloc[-1]:
            regime = "BULLISH_EXTENSION"
        elif current_price < df['vwap_lower_1'].iloc[-1]:
            regime = "BEARISH_EXTENSION"
        elif current_price > current_vwap:
            regime = "BULLISH_INSIDE"
        else:
            regime = "BEARISH_INSIDE"
            
        return {
            'vwap': current_vwap,
            'upper_1': df['vwap_upper_1'].iloc[-1],
            'lower_1': df['vwap_lower_1'].iloc[-1],
            'regime': regime,
            'distance_pct': ((current_price - current_vwap) / current_vwap) * 100
        }
