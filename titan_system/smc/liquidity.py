"""
Liquidity Detection Engine
Maps liquidity pools: session highs/lows, round numbers, equal highs/lows
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, time

class LiquidityEngine:
    """
    Institutional liquidity pool detector
    """
    
    def __init__(self, proximity_threshold: float = 5.0):
        """
        Args:
            proximity_threshold: Points within which levels are considered "equal"
        """
        self.proximity_threshold = proximity_threshold
        
    def detect_session_levels(self, df: pd.DataFrame) -> Dict:
        """
        Detect session highs/lows (London, NY, Asia)
        
        Sessions (IST):
        - Asia: 06:00 - 11:00
        - London: 12:30 - 20:30
        - NY: 18:30 - 01:00
        """
        # For simplicity, detect previous day high/low
        # (Full session detection requires timestamp parsing)
        
        if 'time' in df.columns:
            df['datetime'] = pd.to_datetime(df['time'], unit='s')
            df['date'] = df['datetime'].dt.date
            
            # Group by date
            daily_highs = df.groupby('date')['high'].max()
            daily_lows = df.groupby('date')['low'].min()
            
            prev_day_high = daily_highs.iloc[-2] if len(daily_highs) > 1 else None
            prev_day_low = daily_lows.iloc[-2] if len(daily_lows) > 1 else None
        else:
            # Fallback: use last 24 bars as proxy for "previous day"
            prev_day_high = df['high'].iloc[-48:-24].max() if len(df) > 48 else None
            prev_day_low = df['low'].iloc[-48:-24].min() if len(df) > 48 else None
        
        return {
            'prev_day_high': prev_day_high,
            'prev_day_low': prev_day_low,
            'current_high': df['high'].iloc[-24:].max(),
            'current_low': df['low'].iloc[-24:].min()
        }
    
    def detect_round_numbers(self, current_price: float, symbol: str = "GOLD") -> List[float]:
        """
        Detect nearby round numbers (major liquidity magnets)
        
        For GOLD: 4200, 4210, 4220, etc. (every 10 points)
        """
        if symbol == "GOLD" or symbol.startswith("XAU"):
            # Round to nearest 10
            base = int(current_price / 10) * 10
            
            return [
                base - 20,
                base - 10,
                base,
                base + 10,
                base + 20
            ]
        else:
            # For FX: round to nearest 0.0050
            base = round(current_price * 200) / 200
            return [
                base - 0.0100,
                base - 0.0050,
                base,
                base + 0.0050,
                base + 0.0100
            ]
    
    def detect_equal_highs_lows(self, highs: np.ndarray, lows: np.ndarray) -> Dict:
        """
        Detect equal highs and equal lows (liquidity clusters)
        
        Equal high: Two or more highs within proximity_threshold
        """
        equal_highs = []
        equal_lows = []
        
        # Check last 20 bars for equals
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        for i in range(len(recent_highs) - 1):
            for j in range(i + 1, len(recent_highs)):
                if abs(recent_highs[i] - recent_highs[j]) <= self.proximity_threshold:
                    equal_highs.append({
                        'price': (recent_highs[i] + recent_highs[j]) / 2,
                        'count': 2,
                        'type': 'equal_high'
                    })
                    
        for i in range(len(recent_lows) - 1):
            for j in range(i + 1, len(recent_lows)):
                if abs(recent_lows[i] - recent_lows[j]) <= self.proximity_threshold:
                    equal_lows.append({
                        'price': (recent_lows[i] + recent_lows[j]) / 2,
                        'count': 2,
                        'type': 'equal_low'
                    })
        
        # Remove duplicates
        equal_highs = self._deduplicate_levels(equal_highs)
        equal_lows = self._deduplicate_levels(equal_lows)
        
        return {
            'equal_highs': equal_highs,
            'equal_lows': equal_lows
        }
    
    def detect_sweep(
        self, 
        current_price: float,
        current_low: float,
        current_high: float,
        liquidity_level: float,
        level_type: str = 'high'
    ) -> Dict:
        """
        Detect if a liquidity level has been swept
        
        Sweep = wick through level but close back inside
        """
        swept = False
        sweep_type = None
        
        if level_type == 'high':
            # Bullish sweep: high breaks level, close below it
            if current_high > liquidity_level and current_price < liquidity_level:
                swept = True
                sweep_type = 'bullish_liquidity_grab'
        else:
            # Bearish sweep: low breaks level, close above it
            if current_low < liquidity_level and current_price > liquidity_level:
                swept = True
                sweep_type = 'bearish_liquidity_grab'
        
        return {
            'swept': swept,
            'sweep_type': sweep_type,
            'level': liquidity_level
        }
    
    def _deduplicate_levels(self, levels: List[Dict]) -> List[Dict]:
        """Remove duplicate liquidity levels"""
        if not levels:
            return []
        
        unique = []
        for level in levels:
            is_duplicate = False
            for existing in unique:
                if abs(level['price'] - existing['price']) <= self.proximity_threshold:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(level)
        
        return unique
    
    def analyze(self, df: pd.DataFrame, symbol: str = "GOLD") -> Dict:
        """
        Complete liquidity analysis
        """
        current_price = df['close'].iloc[-1]
        current_high = df['high'].iloc[-1]
        current_low = df['low'].iloc[-1]
        
        # Session levels
        sessions = self.detect_session_levels(df)
        
        # Round numbers
        round_numbers = self.detect_round_numbers(current_price, symbol)
        
        # Equal highs/lows
        equals = self.detect_equal_highs_lows(df['high'].values, df['low'].values)
        
        # Check for sweeps
        sweeps = []
        if sessions['prev_day_high']:
            sweep = self.detect_sweep(
                current_price, current_low, current_high,
                sessions['prev_day_high'], 'high'
            )
            if sweep['swept']:
                sweeps.append(sweep)
                
        if sessions['prev_day_low']:
            sweep = self.detect_sweep(
                current_price, current_low, current_high,
                sessions['prev_day_low'], 'low'
            )
            if sweep['swept']:
                sweeps.append(sweep)
        
        return {
            'sessions': sessions,
            'round_numbers': round_numbers,
            'equal_highs': equals['equal_highs'],
            'equal_lows': equals['equal_lows'],
            'sweeps': sweeps,
            'current_price': current_price
        }
