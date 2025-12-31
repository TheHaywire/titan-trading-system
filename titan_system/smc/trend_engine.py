"""
Trend Engine (TE-1)
Institutional Trend Classification using EMA Stack and Trend Strength Score (TSS)
"""

import numpy as np
import pandas as pd
from typing import Dict

class TrendEngine:
    """
    Implements the TE-1 Trend Classification Model
    """
    
    def __init__(self, ema_fast: int = 9, ema_med: int = 21, ema_slow: int = 50):
        self.ema_fast = ema_fast
        self.ema_med = ema_med
        self.ema_slow = ema_slow
        
    def calculate_emas(self, closes: pd.Series) -> pd.DataFrame:
        """Calculate the 3 EMAs"""
        df = pd.DataFrame(index=closes.index)
        df['ema_9'] = closes.ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_21'] = closes.ewm(span=self.ema_med, adjust=False).mean()
        df['ema_50'] = closes.ewm(span=self.ema_slow, adjust=False).mean()
        return df

    def calculate_slope(self, series: pd.Series, lookback: int = 5) -> float:
        """
        Calculate the angle/slope of an EMA.
        Simple approximation: Price change over lookback / lookback.
        Normalized to be somewhat comparable to degrees depending on scale.
        """
        if len(series) < lookback + 1:
            return 0.0
            
        y = series.values[-lookback:]
        x = np.arange(lookback)
        
        # Linear regression slope
        slope, _ = np.polyfit(x, y, 1)
        
        # To convert to degrees, we need strictly normalized quantity. 
        # For now, we return raw slope value.
        return slope

    def calculate_tss(self, 
                      closes: pd.Series, 
                      ema_df: pd.DataFrame, 
                      structure_trend: str, 
                      atr_expanding: bool) -> Dict:
        """
        Calculate Trend Strength Score (TSS) 0-5
        
        Criteria:
        1. EMA Alignment (+1)
        2. EMA Slope (+1)
        3. Price Location vs EMA50 (+1)
        4. Market Structure (+1) (from MarketStructure module)
        5. ATR Expansion (+1)
        """
        score = 0
        bias = "NEUTRAL"
        
        last_close = closes.iloc[-1]
        e9 = ema_df['ema_9'].iloc[-1]
        e21 = ema_df['ema_21'].iloc[-1]
        e50 = ema_df['ema_50'].iloc[-1]
        
        # 1. EMA Alignment
        bullish_stack = e9 > e21 > e50
        bearish_stack = e9 < e21 < e50
        
        if bullish_stack:
            score += 1
            bias = "BULLISH"
        elif bearish_stack:
            score += 1
            bias = "BEARISH"
            
        # 2. EMA Slope (EMA 50)
        slope_50 = self.calculate_slope(ema_df['ema_50'])
        
        # Thresholds tailored for Gold H1 ~ approx
        slope_threshold = 0.5 
        
        if bias == "BULLISH" and slope_50 > slope_threshold:
            score += 1
        elif bias == "BEARISH" and slope_50 < -slope_threshold:
            score += 1
            
        # 3. Price vs EMA50
        if bias == "BULLISH" and last_close > e50:
            score += 1
        elif bias == "BEARISH" and last_close < e50:
            score += 1
            
        # 4. Market Structure (Passed from external analysis)
        if bias == "BULLISH" and structure_trend == "BULLISH":
            score += 1
        elif bias == "BEARISH" and structure_trend == "BEARISH":
            score += 1
            
        # 5. ATR Expansion
        if atr_expanding:
            score += 1
            
        return {
            'tss': score,
            'bias': bias,
            'ema_alignment': 'bullish' if bullish_stack else 'bearish' if bearish_stack else 'mixed',
            'slope_50': slope_50
        }
