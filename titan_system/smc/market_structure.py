"""
Market Structure Detection Engine
Detects swing highs/lows, BOS (Break of Structure), CHoCH (Change of Character)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple

class MarketStructure:
    """
    Institutional market structure detector
    """
    
    def __init__(self, swing_length: int = 5):
        """
        Args:
            swing_length: Number of bars to each side for swing detection
        """
        self.swing_length = swing_length
        
    def detect_swing_highs_lows(self, highs: np.ndarray, lows: np.ndarray) -> Dict:
        """
        Detect swing highs and swing lows
        
        A swing high: high[i] > high[i-n:i] AND high[i] > high[i+1:i+n]
        A swing low: low[i] < low[i-n:i] AND low[i] < low[i+1:i+n]
        """
        swing_highs = []
        swing_lows = []
        
        n = self.swing_length
        
        for i in range(n, len(highs) - n):
            # Check if current high is highest in window
            left_highs = highs[i-n:i]
            right_highs = highs[i+1:i+n+1]
            
            if highs[i] > max(left_highs) and highs[i] > max(right_highs):
                swing_highs.append({
                    'index': i,
                    'price': highs[i],
                    'type': 'swing_high'
                })
                
            # Check if current low is lowest in window
            left_lows = lows[i-n:i]
            right_lows = lows[i+1:i+n+1]
            
            if lows[i] < min(left_lows) and lows[i] < min(right_lows):
                swing_lows.append({
                    'index': i,
                    'price': lows[i],
                    'type': 'swing_low'
                })
                
        return {
            'swing_highs': swing_highs,
            'swing_lows': swing_lows
        }
    
    def detect_bos_choch(
        self, 
        closes: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        swings: Dict
    ) -> Dict:
        """
        Detect Break of Structure (BOS) and Change of Character (CHoCH)
        
        BOS: Price breaks last swing in direction of trend (continuation)
        CHoCH: Price breaks last swing against trend (reversal)
        """
        swing_highs = swings['swing_highs']
        swing_lows = swings['swing_lows']
        
        # Determine current trend by comparing recent swing highs/lows
        trend = self._determine_trend(swing_highs, swing_lows)
        
        bos_events = []
        choch_events = []
        
        # Get last swing high and low
        if swing_highs:
            last_swing_high = swing_highs[-1]
        else:
            last_swing_high = None
            
        if swing_lows:
            last_swing_low = swing_lows[-1]
        else:
            last_swing_low = None
        
        current_price = closes[-1]
        
        # Check for BOS/CHoCH
        if trend == 'bullish' and last_swing_high:
            # In uptrend, breaking last high = BOS (continuation)
            if current_price > last_swing_high['price']:
                bos_events.append({
                    'type': 'BOS',
                    'direction': 'bullish',
                    'price': current_price,
                    'broken_level': last_swing_high['price']
                })
                
        if trend == 'bullish' and last_swing_low:
            # In uptrend, breaking last low = CHoCH (reversal)
            if current_price < last_swing_low['price']:
                choch_events.append({
                    'type': 'CHoCH',
                    'direction': 'bearish',
                    'price': current_price,
                    'broken_level': last_swing_low['price']
                })
                
        if trend == 'bearish' and last_swing_low:
            # In downtrend, breaking last low = BOS (continuation)
            if current_price < last_swing_low['price']:
                bos_events.append({
                    'type': 'BOS',
                    'direction': 'bearish',
                    'price': current_price,
                    'broken_level': last_swing_low['price']
                })
                
        if trend == 'bearish' and last_swing_high:
            # In downtrend, breaking last high = CHoCH (reversal)
            if current_price > last_swing_high['price']:
                choch_events.append({
                    'type': 'CHoCH',
                    'direction': 'bullish',
                    'price': current_price,
                    'broken_level': last_swing_high['price']
                })
        
        return {
            'trend': trend,
            'bos': bos_events,
            'choch': choch_events,
            'last_swing_high': last_swing_high,
            'last_swing_low': last_swing_low
        }
    
    def _determine_trend(self, swing_highs: List, swing_lows: List) -> str:
        """
        Determine trend based on swing points
        
        Bullish: Higher Highs + Higher Lows
        Bearish: Lower Highs + Lower Lows
        """
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 'neutral'
        
        # Check last 2 swing highs
        recent_highs = swing_highs[-2:]
        higher_high = recent_highs[1]['price'] > recent_highs[0]['price']
        
        # Check last 2 swing lows
        recent_lows = swing_lows[-2:]
        higher_low = recent_lows[1]['price'] > recent_lows[0]['price']
        
        lower_high = recent_highs[1]['price'] < recent_highs[0]['price']
        lower_low = recent_lows[1]['price'] < recent_lows[0]['price']
        
        if higher_high and higher_low:
            return 'bullish'
        elif lower_high and lower_low:
            return 'bearish'
        else:
            return 'neutral'
    
    def analyze(self, df: pd.DataFrame) -> Dict:
        """
        Complete market structure analysis
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            Dict with all structural information
        """
        highs = df['high'].values
        lows = df['low'].values
        closes = df['close'].values
        
        # Detect swings
        swings = self.detect_swing_highs_lows(highs, lows)
        
        # Detect BOS/CHoCH
        structure = self.detect_bos_choch(closes, highs, lows, swings)
        
        return {
            **swings,
            **structure
        }
