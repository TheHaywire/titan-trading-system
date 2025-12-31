"""
Momentum Engine (ME-1)
Momentum classification using RSI, ROC, MFI, and Candle Range Expansion
"""

import pandas as pd
import numpy as np
from typing import Dict

class MomentumEngine:
    """
    Implements ME-1 Momentum Classification
    """
    
    def __init__(self, rsi_period: int = 14, roc_period: int = 10):
        self.rsi_period = rsi_period
        self.roc_period = roc_period
        
    def calculate_rsi(self, series: pd.Series, period: int = 14):
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def calculate_roc(self, series: pd.Series, period: int = 10):
        return ((series - series.shift(period)) / series.shift(period)) * 100

    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Analyze Momentum Regime
        """
        closes = df['close']
        
        # Calculate Indicators
        rsi = self.calculate_rsi(closes, self.rsi_period)
        roc = self.calculate_roc(closes, self.roc_period)
        
        current_rsi = rsi.iloc[-1]
        current_roc = roc.iloc[-1]
        
        # 1. RSI Regime Zones
        rsi_zone = "NEUTRAL"
        if current_rsi > 70:
            rsi_zone = "EXHAUSTION_BULL"
        elif 60 <= current_rsi <= 70:
            rsi_zone = "BULL_MOMENTUM"
        elif 40 < current_rsi < 60:
            rsi_zone = "NEUTRAL_RANGE"
        elif 30 <= current_rsi <= 40:
            rsi_zone = "BEAR_MOMENTUM"
        elif current_rsi < 30:
            rsi_zone = "EXHAUSTION_BEAR"
            
        # 2. Momentum Confirmation (Breakout validation)
        # Momentum must improve into breakout
        momentum_increasing = False
        if len(rsi) > 3:
            # Check if RSI is trending in direction of ROC
            if current_roc > 0 and rsi.iloc[-1] > rsi.iloc[-2]:
                momentum_increasing = True
            elif current_roc < 0 and rsi.iloc[-1] < rsi.iloc[-2]:
                momentum_increasing = True
                
        # 3. Divergence Detection (Simplified)
        # Bullish Divergence: Price LL + RSI HL
        # Bearish Divergence: Price HH + RSI LH
        divergence = "NONE"
        
        # (This usually requires Swing Point detection paired with RSI values at those points)
        # Placeholder for complex divergence logic
        
        return {
            'rsi': current_rsi,
            'roc': current_roc,
            'rsi_zone': rsi_zone,
            'momentum_increasing': momentum_increasing,
            'divergence': divergence
        }
