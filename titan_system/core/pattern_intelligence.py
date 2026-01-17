"""
Titan Deep Pattern Miner
========================
Identifies institutional footprints and high-probability price 
action patterns using wick physics and volume clustering.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

class PatternMiner:
    """Detects advanced price action patterns (Wick Physics, Squeezes, Sweeps)."""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        
    def detect_liquidity_sweep(self, lookback: int = 20) -> Dict:
        """Detects a 'Stop Hunt' or Liquidity Sweep pattern."""
        # A sweep is when price breaks a recent swing high/low then reverses sharply
        last = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        swing_high = self.df['high'].iloc[-lookback:-1].max()
        swing_low = self.df['low'].iloc[-lookback:-1].min()
        
        pattern = "NONE"
        intensity = 0.0
        
        # Bullish Sweep: Price went below low, but closed back above
        if last['low'] < swing_low and last['close'] > swing_low:
            pattern = "BULLISH_SWEEP"
            intensity = (swing_low - last['low']) / (last['high'] - last['low'])
            
        # Bearish Sweep: Price went above high, but closed back below
        elif last['high'] > swing_high and last['close'] < swing_high:
            pattern = "BEARISH_SWEEP"
            intensity = (last['high'] - swing_high) / (last['high'] - last['low'])
            
        return {"pattern": pattern, "intensity": round(intensity, 2)}

    def detect_volatility_squeeze(self) -> Dict:
        """Detects Bollinger Band Squeeze (low vol consolidation)."""
        # Calculate BB Width
        sma20 = self.df['close'].rolling(window=20).mean()
        std20 = self.df['close'].rolling(window=20).std()
        bb_width = (std20 * 4) / sma20 # Width in percentage
        
        avg_width = bb_width.rolling(window=100).mean().iloc[-1]
        curr_width = bb_width.iloc[-1]
        
        status = "NORMAL"
        if curr_width < (avg_width * 0.7):
            status = "SQUEEZE_ACTIVE"
        elif curr_width > (avg_width * 1.5):
            status = "EXPANSION_ACTIVE"
            
        return {"status": status, "compression": round(curr_width / avg_width, 2)}

    def analyze_wick_physics(self) -> Dict:
        """Analyzes wick size relative to body to find rejection levels."""
        last = self.df.iloc[-1]
        body = abs(last['open'] - last['close'])
        total_range = last['high'] - last['low']
        
        upper_wick = last['high'] - max(last['open'], last['close'])
        lower_wick = min(last['open'], last['close']) - last['low']
        
        # Ratios
        upper_ratio = upper_wick / total_range if total_range > 0 else 0
        lower_ratio = lower_wick / total_range if total_range > 0 else 0
        
        rejection = "NONE"
        if upper_ratio > 0.4: # Loosened from 0.6
            rejection = "BEARISH_REJECTION"
        elif lower_ratio > 0.4: # Loosened from 0.6
            rejection = "BULLISH_REJECTION"
            
        return {
            "rejection": rejection,
            "upper_wick_ratio": round(upper_ratio, 2),
            "lower_wick_ratio": round(lower_ratio, 2)
        }

    def detect_absorption(self) -> Dict:
        """Detects high volume with small price range (Absorption)."""
        if 'tick_volume' not in self.df.columns:
            return {"status": "UNKNOWN"}
            
        last = self.df.iloc[-1]
        avg_vol = self.df['tick_volume'].rolling(window=20).mean().iloc[-1]
        vol_ratio = last['tick_volume'] / avg_vol
        
        body = abs(last['open'] - last['close'])
        avg_body = abs(self.df['open'] - self.df['close']).rolling(window=20).mean().iloc[-1]
        
        status = "NONE"
        if vol_ratio > 1.5 and body < avg_body:
            status = "INSTITUTIONAL_ABSORPTION"
            
        return {"status": status, "volume_surge": round(vol_ratio, 2)}

    def get_all_patterns(self) -> Dict:
        """Consolidate all pattern insights."""
        if len(self.df) < 100:
            return {"error": "Insufficient data"}
            
        return {
            "liquidity": self.detect_liquidity_sweep(),
            "volatility": self.detect_volatility_squeeze(),
            "physics": self.analyze_wick_physics(),
            "absorption": self.detect_absorption()
        }

if __name__ == "__main__":
    # Test with dummy data
    data = {
        'open': [100]*100,
        'high': [105]*99 + [120],
        'low': [95]*99 + [100],
        'close': [102]*99 + [105]
    }
    df = pd.DataFrame(data)
    miner = PatternMiner(df)
    print(miner.get_all_patterns())
