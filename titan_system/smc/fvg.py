"""
Fair Value Gap (FVG) / Imbalance Detection
"""

import numpy as np
import pandas as pd
from typing import List, Dict

class FVGDetector:
    """
    Detects Fair Value Gaps (3-candle imbalances)
    """
    
    def __init__(self, min_gap_size: float = 1.5):
        """
        Args:
            min_gap_size: Minimum gap size as multiple of average candle body
        """
        self.min_gap_size = min_gap_size
        
    def detect_fvg(
        self, 
        opens: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray
    ) -> List[Dict]:
        """
        Detect Fair Value Gaps
        
        Bullish FVG:
        - Candle 1 (low)
        - Candle 2 (big bullish move)
        - Candle 3 (high)
        - Gap = Candle1.high < Candle3.low
        
        Bearish FVG:
        - Candle 1 (high)
        - Candle 2 (big bearish move)
        - Candle 3 (low)
        - Gap = Candle1.low > Candle3.high
        """
        fvgs = []
        
        # Need at least 3 candles
        if len(closes) < 3:
            return fvgs
        
        # Calculate average body size for filtering
        bodies = np.abs(closes - opens)
        avg_body = np.mean(bodies[-20:]) if len(bodies) > 20 else np.mean(bodies)
        
        # Check last 50 candles for FVGs
        start_idx = max(0, len(closes) - 50)
        
        for i in range(start_idx, len(closes) - 2):
            candle1_high = highs[i]
            candle1_low = lows[i]
            
            candle2_high = highs[i + 1]
            candle2_low = lows[i + 1]
            candle2_body = abs(closes[i + 1] - opens[i + 1])
            
            candle3_high = highs[i + 2]
            candle3_low = lows[i + 2]
            
            # Bullish FVG
            if candle1_high < candle3_low:
                gap_size = candle3_low - candle1_high
                
                # Filter by size
                if gap_size >= self.min_gap_size * avg_body:
                    fvgs.append({
                        'type': 'bullish_fvg',
                        'index': i,
                        'top': candle3_low,
                        'bottom': candle1_high,
                        'size': gap_size,
                        'displacement_body': candle2_body,
                        'filled': False
                    })
            
            # Bearish FVG
            if candle1_low > candle3_high:
                gap_size = candle1_low - candle3_high
                
                if gap_size >= self.min_gap_size * avg_body:
                    fvgs.append({
                        'type': 'bearish_fvg',
                        'index': i,
                        'top': candle1_low,
                        'bottom': candle3_high,
                        'size': gap_size,
                        'displacement_body': candle2_body,
                        'filled': False
                    })
        
        return fvgs
    
    def check_fvg_retest(
        self,
        fvg: Dict,
        current_price: float,
        current_high: float,
        current_low: float
    ) -> Dict:
        """
        Check if price has retested an FVG
        
        Valid retest: Price enters 50-70% of the gap
        """
        fvg_top = fvg['top']
        fvg_bottom = fvg['bottom']
        fvg_mid = (fvg_top + fvg_bottom) / 2
        
        retest_zone_top = fvg_mid + (fvg_top - fvg_mid) * 0.3  # 65% level
        retest_zone_bottom = fvg_mid - (fvg_mid - fvg_bottom) * 0.3
        
        retested = False
        entry_price = None
        
        if fvg['type'] == 'bullish_fvg':
            # Price should come down into FVG
            if current_low <= retest_zone_top and current_low >= fvg_bottom:
                retested = True
                entry_price = retest_zone_top
                
        elif fvg['type'] == 'bearish_fvg':
            # Price should come up into FVG
            if current_high >= retest_zone_bottom and current_high <= fvg_top:
                retested = True
                entry_price = retest_zone_bottom
        
        return {
            'retested': retested,
            'entry_price': entry_price,
            'fvg': fvg
        }
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete FVG analysis
        """
        opens = df['open'].values
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        current_price = closes[-1]
        current_high = highs[-1]
        current_low = lows[-1]
        
        # Detect all FVGs
        fvgs = self.detect_fvg(opens, highs, lows, closes)
        
        # Check for untested FVGs
        untested_fvgs = []
        retest_opportunities = []
        
        for fvg in fvgs:
            # Check if filled
            if fvg['type'] == 'bullish_fvg' and current_low <= fvg['bottom']:
                fvg['filled'] = True
            elif fvg['type'] == 'bearish_fvg' and current_high >= fvg['top']:
                fvg['filled'] = True
            
            if not fvg['filled']:
                untested_fvgs.append(fvg)
                
                # Check for retest
                retest = self.check_fvg_retest(fvg, current_price, current_high, current_low)
                if retest['retested']:
                    retest_opportunities.append(retest)
        
        return {
            'all_fvgs': fvgs,
            'untested_fvgs': untested_fvgs,
            'retest_opportunities': retest_opportunities,
            'total_fvgs': len(fvgs),
            'unfilled_count': len(untested_fvgs)
        }
