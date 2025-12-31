
from .base import BaseStrategy
import pandas as pd
import numpy as np
from titan_system.math_core.regression import LinearRegressionChannel
from titan_system.math_core.statistics import StatisticalMetrics

class RegressionSurfer(BaseStrategy):
    """
    Quantitative Mean Reversion Strategy.
    Trades standard deviation extremes around a Linear Regression Channel.
    
    Logic:
    - BUY when Price is < -2.0 Sigma (Statistically Cheap)
    - SELL when Price is > +2.0 Sigma (Statistically Expensive)
    - FILTER: Only trade if Half-Life < 25 (Fast Mean Reversion)
    - EXIT when Price returns to Mean (Z-Score ~ 0)
    """
    
    def __init__(self, config=None):
        super().__init__("RegressionSurfer", config or {})
        self.period = self.config.get("period", 100)
        self.entry_z = self.config.get("entry_z", 2.0)
        self.exit_z = self.config.get("exit_z", 0.5) 
        self.max_half_life = self.config.get("max_half_life", 25.0) # Filter
        self.math = LinearRegressionChannel(period=self.period)
        
    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        if df is None or len(df) < self.period:
            return {"signal": "HOLD", "reason": "Insufficient Data"}
            
        closes = df['close'].values
        
        # 1. Calculate Regression Channel
        stats = self.math.calculate(closes)
        z_score = stats['z_score']
        slope = stats['slope']
        
        # 2. Calculate Half-Life (The "Snap Speed")
        # We usage the residuals (price - line) to check if the NOISE is mean reverting
        # Or just the price itself if it's ranging. 
        # For a channel, we want the DETRENDED series (Residuals) to mean revert.
        
        # Re-calc residuals manually here or update math_core to return them?
        # Let's calc simply on price for now, or better:
        expected_prices = stats['slope'] * np.arange(len(closes)) + stats['intercept']
        residuals = closes[-self.period:] - expected_prices[-self.period:]
        
        half_life = StatisticalMetrics.calculate_half_life(residuals)
        stats['half_life'] = half_life
        
        signal = "HOLD"
        reason = f"Z: {z_score:.2f} | HL: {half_life:.1f}"
        confidence = 0.0
        
        # Regime Filter: Is this asset mean-reverting enough?
        if half_life > self.max_half_life:
             return {
                 "signal": "HOLD", 
                 "reason": f"Structuring Broken (HL: {half_life:.1f} > {self.max_half_life})",
                 "metrics": stats
             }
        
        # 1. LONG Condition (Oversold)
        # We prefer buying when trend (slope) is UP or FLAT.
        # Buying in a steep downtrend is catching a falling knife.
        if z_score < -self.entry_z:
            if slope > -0.05: # Allow slight counter-trend but avoid steep drops
                signal = "BUY"
                reason = f"Oversold (Z: {z_score:.2f}) in Up/Flat Channel"
                confidence = abs(z_score) / 4.0 # 2.0 -> 0.5, 4.0 -> 1.0
            else:
                 reason = f"Oversold but Downtrend (Slope: {slope:.4f})"

        # 2. SHORT Condition (Overbought)
        elif z_score > self.entry_z:
            if slope < 0.05:
                signal = "SELL"
                reason = f"Overbought (Z: {z_score:.2f}) in Down/Flat Channel"
                confidence = abs(z_score) / 4.0
            else:
                reason = f"Overbought but Uptrend (Slope: {slope:.4f})"
                
        # 3. EXIT Condition (Mean Reversion)
        # If we are holding a position (Engine handles this check usually), 
        # but here we can signal "NEUTRAL" or "EXIT" if close to mean.
        if abs(z_score) < self.exit_z:
             # This is a "Take Profit" signal basically
             pass # The engine manages exits usually, but we note it.

        return {
            "signal": signal,
            "reason": reason,
            "confidence": min(confidence, 1.0),
            "metrics": stats
        }
