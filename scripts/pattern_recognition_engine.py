"""
TITAN PATTERN RECOGNITION ENGINE (FinViz Simulation)
====================================================
Simulates FinViz-style pattern detection locally using Price Action.
Detects: Wedge Up/Down, Channel Up/Down, Double Top/Bottom.
"""

import pandas as pd
import numpy as np

class PatternEngine:
    
    def analyze(self, df):
        """
        Analyzes a DataFrame (OHLC) for classic chart patterns.
        Returns a list of detected pattern strings.
        """
        patterns = []
        if len(df) < 50: return ["Insuff. Data"]
        
        closes = df['close'].values
        highs = df['high'].values
        lows = df['low'].values
        
        # 1. CHANNEL DETECTION (Parallel Slope check)
        x = np.arange(len(closes))
        slope_h, intercept_h = np.polyfit(x, highs, 1)
        slope_l, intercept_l = np.polyfit(x, lows, 1)
        
        slope_diff = abs(slope_h - slope_l)
        avg_slope = (slope_h + slope_l) / 2
        
        # Use Standard Deviation of residuals to confirm 'tightness'
        err_h = np.std(highs - (slope_h * x + intercept_h))
        err_l = np.std(lows - (slope_l * x + intercept_l))
        
        if slope_diff < 0.02 and err_h < (highs.mean() * 0.005): 
            if avg_slope > 0.0001: patterns.append("Channel Up")
            elif avg_slope < -0.0001: patterns.append("Channel Down")
            else: patterns.append("Channel")
            
        # 2. WEDGE DETECTION (Converging slopes)
        # Wedge Up: Both slopes up, but Lows rising faster than Highs (Converging at top)
        if slope_h > 0.0001 and slope_l > slope_h * 1.5:
            patterns.append("Wedge Up")
        # Wedge Down: Both slopes down, but Highs falling faster than Lows (Converging at bottom)
        elif slope_h < -0.0001 and slope_h < slope_l * 1.5:
            patterns.append("Wedge Down")
            
        # 4. TRIANGLE DETECTION (Converging with one horizontal)
        if abs(slope_h) < 0.00005 and slope_l > 0.0001: patterns.append("Ascending Triangle")
        elif abs(slope_l) < 0.00005 and slope_h < -0.0001: patterns.append("Descending Triangle")
        
        # 5. RECTANGLE (Consolidation)
        if abs(slope_h) < 0.00005 and abs(slope_l) < 0.00005 and err_h < (highs.mean() * 0.002):
            patterns.append("Rectangle / Consolidation")

        # 6. HEAD & SHOULDERS (Simplified 3-peak check)
        peaks = []
        for i in range(5, len(highs)-5):
            if highs[i] == max(highs[i-5:i+6]):
                peaks.append((i, highs[i]))
        
        if len(peaks) >= 3:
            p1, p2, p3 = peaks[-3][1], peaks[-2][1], peaks[-1][1]
            if p2 > p1 and p2 > p3 and abs(p1 - p3) / p1 < 0.002:
                patterns.append("Head & Shoulders")
            elif p2 < p1 and p2 < p3 and abs(p1 - p3) / p1 < 0.002:
                patterns.append("Inv. Head & Shoulders")

        if not patterns:
            patterns.append("Neutral / No Clear Pattern")
            
        return patterns

# Quick Test
if __name__ == "__main__":
    # Mock data
    print("Pattern Engine Loaded.")
