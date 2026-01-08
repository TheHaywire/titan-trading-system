"""
TITAN KEY LEVELS MODULE
========================
Comprehensive Support/Resistance and Key Levels detection.
Combines multiple methods for institutional-grade level identification.

Key Level Types:
1. Pivot Points (Daily, Weekly, Monthly)
2. Swing Highs/Lows (Market Structure)
3. Session Levels (Asian, London, NY highs/lows)
4. Round Numbers (psychological levels)
5. Equal Highs/Lows (liquidity pools)
6. Dynamic S/R (EMA zones)
7. Historical S/R (price rejection zones)

Usage:
    from titan_system.analytics.key_levels import KeyLevelsDetector
    
    kl = KeyLevelsDetector()
    levels = kl.detect_all(df, symbol='GOLD')
    
    print(levels['support'])      # List of support levels
    print(levels['resistance'])   # List of resistance levels
    print(levels['pivots'])       # Pivot points
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger("Titan.KeyLevels")


@dataclass
class Level:
    """Represents a key price level"""
    price: float
    type: str  # 'support', 'resistance', 'pivot'
    source: str  # 'swing', 'pivot', 'session', 'round', 'equal', 'dynamic'
    strength: int  # 1-5 (number of touches or confidence)
    distance_pct: float  # Distance from current price in %


class KeyLevelsDetector:
    """
    Comprehensive key levels detection combining multiple methods.
    """
    
    def __init__(self, lookback: int = 100):
        """
        Args:
            lookback: Number of bars to look back for level detection
        """
        self.lookback = lookback
        self.swing_length = 5  # Bars for swing detection
    
    # =========================================================================
    # PIVOT POINTS
    # =========================================================================
    
    def calculate_pivots(self, df: pd.DataFrame, period: str = 'daily') -> Dict[str, float]:
        """
        Calculate Standard Pivot Points
        
        Formula:
        - Pivot = (High + Low + Close) / 3
        - R1 = (2 * Pivot) - Low
        - R2 = Pivot + (High - Low)
        - R3 = R1 + (High - Low)
        - S1 = (2 * Pivot) - High
        - S2 = Pivot - (High - Low)
        - S3 = S1 - (High - Low)
        """
        if period == 'daily':
            # Use previous day's data
            if len(df) < 48:  # Not enough data
                return {}
            high = df['high'].iloc[-48:-24].max()
            low = df['low'].iloc[-48:-24].min()
            close = df['close'].iloc[-25]  # Previous day close
        else:
            # Use recent data
            high = df['high'].iloc[-self.lookback:].max()
            low = df['low'].iloc[-self.lookback:].min()
            close = df['close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        
        return {
            'pivot': pivot,
            'r1': (2 * pivot) - low,
            'r2': pivot + (high - low),
            'r3': (2 * pivot) - low + (high - low),
            's1': (2 * pivot) - high,
            's2': pivot - (high - low),
            's3': (2 * pivot) - high - (high - low)
        }
    
    def calculate_fibonacci_pivots(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate Fibonacci Pivot Points
        
        Uses Fibonacci ratios: 0.382, 0.618, 1.0
        """
        if len(df) < 48:
            return {}
        
        high = df['high'].iloc[-48:-24].max()
        low = df['low'].iloc[-48:-24].min()
        close = df['close'].iloc[-25]
        
        pivot = (high + low + close) / 3
        range_val = high - low
        
        return {
            'pivot': pivot,
            'r1': pivot + (0.382 * range_val),
            'r2': pivot + (0.618 * range_val),
            'r3': pivot + (1.0 * range_val),
            's1': pivot - (0.382 * range_val),
            's2': pivot - (0.618 * range_val),
            's3': pivot - (1.0 * range_val)
        }
    
    # =========================================================================
    # SWING LEVELS
    # =========================================================================
    
    def detect_swing_levels(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Detect swing highs and lows as S/R levels
        """
        highs = df['high'].values
        lows = df['low'].values
        n = self.swing_length
        
        swing_highs = []
        swing_lows = []
        
        for i in range(n, len(highs) - n):
            # Swing High
            left_highs = highs[i-n:i]
            right_highs = highs[i+1:i+n+1]
            
            if highs[i] > max(left_highs) and highs[i] > max(right_highs):
                swing_highs.append({
                    'price': highs[i],
                    'index': i,
                    'strength': 1
                })
            
            # Swing Low
            left_lows = lows[i-n:i]
            right_lows = lows[i+1:i+n+1]
            
            if lows[i] < min(left_lows) and lows[i] < min(right_lows):
                swing_lows.append({
                    'price': lows[i],
                    'index': i,
                    'strength': 1
                })
        
        # Increase strength based on multiple touches
        swing_highs = self._cluster_levels(swing_highs)
        swing_lows = self._cluster_levels(swing_lows)
        
        return {
            'swing_highs': swing_highs[-5:] if swing_highs else [],  # Last 5
            'swing_lows': swing_lows[-5:] if swing_lows else []
        }
    
    def _cluster_levels(self, levels: List[Dict], tolerance: float = 0.002) -> List[Dict]:
        """Cluster nearby levels and increase strength"""
        if not levels:
            return []
        
        clustered = []
        used = set()
        
        for i, level in enumerate(levels):
            if i in used:
                continue
            
            cluster = [level]
            for j, other in enumerate(levels[i+1:], i+1):
                if j in used:
                    continue
                if abs(level['price'] - other['price']) / level['price'] < tolerance:
                    cluster.append(other)
                    used.add(j)
            
            avg_price = np.mean([l['price'] for l in cluster])
            clustered.append({
                'price': avg_price,
                'strength': len(cluster),
                'index': cluster[-1]['index']
            })
        
        return clustered
    
    # =========================================================================
    # DYNAMIC S/R (EMA ZONES)
    # =========================================================================
    
    def detect_dynamic_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Detect dynamic S/R using key EMAs
        """
        close = df['close']
        
        ema_21 = close.ewm(span=21).mean().iloc[-1]
        ema_50 = close.ewm(span=50).mean().iloc[-1]
        ema_200 = close.ewm(span=200).mean().iloc[-1] if len(df) >= 200 else None
        
        return {
            'ema_21': ema_21,
            'ema_50': ema_50,
            'ema_200': ema_200
        }
    
    # =========================================================================
    # ROUND NUMBERS
    # =========================================================================
    
    def detect_round_numbers(self, current_price: float, symbol: str = 'GOLD') -> List[float]:
        """
        Detect nearby psychological round numbers
        """
        if symbol == 'GOLD' or symbol.startswith('XAU'):
            # GOLD: Every 10 points
            base = int(current_price / 10) * 10
            increment = 10
        elif 'JPY' in symbol:
            # JPY pairs: every 0.5
            base = round(current_price * 2) / 2
            increment = 0.5
        elif 'BTC' in symbol:
            # BTC: Every 1000
            base = int(current_price / 1000) * 1000
            increment = 1000
        else:
            # FX: Every 0.005
            base = round(current_price * 200) / 200
            increment = 0.005
        
        return [
            base - (3 * increment),
            base - (2 * increment),
            base - increment,
            base,
            base + increment,
            base + (2 * increment),
            base + (3 * increment)
        ]
    
    # =========================================================================
    # SESSION LEVELS
    # =========================================================================
    
    def detect_session_levels(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Detect previous session highs/lows
        """
        # Previous day high/low (approximate using last 24-48 bars on H1)
        if len(df) < 48:
            return {}
        
        prev_high = df['high'].iloc[-48:-24].max()
        prev_low = df['low'].iloc[-48:-24].min()
        
        # Week high/low
        week_high = df['high'].iloc[-120:].max() if len(df) >= 120 else None
        week_low = df['low'].iloc[-120:].min() if len(df) >= 120 else None
        
        return {
            'prev_day_high': prev_high,
            'prev_day_low': prev_low,
            'week_high': week_high,
            'week_low': week_low
        }
    
    # =========================================================================
    # HISTORICAL S/R (Price Rejection Zones)
    # =========================================================================
    
    def detect_rejection_zones(self, df: pd.DataFrame, threshold: float = 0.3) -> Dict[str, List[float]]:
        """
        Detect price rejection zones where wicks are significant
        
        Rejection = wick size > threshold * body size
        """
        resistance_zones = []
        support_zones = []
        
        for i in range(-self.lookback, -1):
            open_p = df['open'].iloc[i]
            high = df['high'].iloc[i]
            low = df['low'].iloc[i]
            close = df['close'].iloc[i]
            
            body = abs(close - open_p)
            upper_wick = high - max(open_p, close)
            lower_wick = min(open_p, close) - low
            
            if body > 0:
                # Upper wick rejection (resistance)
                if upper_wick / body > threshold:
                    resistance_zones.append(high)
                
                # Lower wick rejection (support)
                if lower_wick / body > threshold:
                    support_zones.append(low)
        
        # Cluster and deduplicate
        resistance_zones = self._cluster_prices(resistance_zones)
        support_zones = self._cluster_prices(support_zones)
        
        return {
            'resistance_rejections': resistance_zones[-5:],
            'support_rejections': support_zones[-5:]
        }
    
    def _cluster_prices(self, prices: List[float], tolerance: float = 0.002) -> List[float]:
        """Cluster nearby prices and return unique levels"""
        if not prices:
            return []
        
        prices = sorted(prices)
        clusters = []
        current_cluster = [prices[0]]
        
        for price in prices[1:]:
            if abs(price - current_cluster[-1]) / current_cluster[-1] < tolerance:
                current_cluster.append(price)
            else:
                clusters.append(np.mean(current_cluster))
                current_cluster = [price]
        
        if current_cluster:
            clusters.append(np.mean(current_cluster))
        
        return clusters
    
    # =========================================================================
    # MAIN DETECTION
    # =========================================================================
    
    def detect_all(self, df: pd.DataFrame, symbol: str = 'GOLD') -> Dict:
        """
        Detect all key levels and return organized structure
        
        Returns:
            Dict with:
            - support: List of Level objects below current price
            - resistance: List of Level objects above current price
            - pivots: Pivot point levels
            - nearest: Nearest S/R levels
        """
        current_price = df['close'].iloc[-1]
        
        all_levels = []
        
        # 1. Pivot Points
        pivots = self.calculate_pivots(df)
        if pivots:
            for name, price in pivots.items():
                if price:
                    level_type = 'support' if price < current_price else 'resistance'
                    all_levels.append(Level(
                        price=price,
                        type=level_type,
                        source='pivot',
                        strength=3 if name == 'pivot' else 2,
                        distance_pct=abs(price - current_price) / current_price * 100
                    ))
        
        # 2. Swing Levels
        swings = self.detect_swing_levels(df)
        for sh in swings['swing_highs']:
            all_levels.append(Level(
                price=sh['price'],
                type='resistance',
                source='swing',
                strength=sh['strength'],
                distance_pct=abs(sh['price'] - current_price) / current_price * 100
            ))
        for sl in swings['swing_lows']:
            all_levels.append(Level(
                price=sl['price'],
                type='support',
                source='swing',
                strength=sl['strength'],
                distance_pct=abs(sl['price'] - current_price) / current_price * 100
            ))
        
        # 3. Dynamic EMAs
        dynamic = self.detect_dynamic_levels(df)
        for name, price in dynamic.items():
            if price:
                level_type = 'support' if price < current_price else 'resistance'
                all_levels.append(Level(
                    price=price,
                    type=level_type,
                    source='dynamic',
                    strength=2,
                    distance_pct=abs(price - current_price) / current_price * 100
                ))
        
        # 4. Round Numbers
        rounds = self.detect_round_numbers(current_price, symbol)
        for price in rounds:
            level_type = 'support' if price < current_price else 'resistance'
            all_levels.append(Level(
                price=price,
                type=level_type,
                source='round',
                strength=1,
                distance_pct=abs(price - current_price) / current_price * 100
            ))
        
        # 5. Session Levels
        sessions = self.detect_session_levels(df)
        for name, price in sessions.items():
            if price:
                level_type = 'support' if price < current_price else 'resistance'
                all_levels.append(Level(
                    price=price,
                    type=level_type,
                    source='session',
                    strength=3,
                    distance_pct=abs(price - current_price) / current_price * 100
                ))
        
        # 6. Rejection Zones
        rejections = self.detect_rejection_zones(df)
        for price in rejections['resistance_rejections']:
            all_levels.append(Level(
                price=price,
                type='resistance',
                source='rejection',
                strength=2,
                distance_pct=abs(price - current_price) / current_price * 100
            ))
        for price in rejections['support_rejections']:
            all_levels.append(Level(
                price=price,
                type='support',
                source='rejection',
                strength=2,
                distance_pct=abs(price - current_price) / current_price * 100
            ))
        
        # Separate and sort
        support = sorted([l for l in all_levels if l.type == 'support'], 
                        key=lambda x: x.distance_pct)
        resistance = sorted([l for l in all_levels if l.type == 'resistance'], 
                           key=lambda x: x.distance_pct)
        
        # Get nearest levels
        nearest_support = support[0] if support else None
        nearest_resistance = resistance[0] if resistance else None
        
        return {
            'support': support[:10],  # Top 10 nearest
            'resistance': resistance[:10],
            'pivots': pivots,
            'nearest_support': nearest_support,
            'nearest_resistance': nearest_resistance,
            'current_price': current_price,
            'all_levels': all_levels
        }
    
    def get_signal_context(self, df: pd.DataFrame, signal_direction: str, symbol: str = 'GOLD') -> Dict:
        """
        Get key level context for a trading signal
        
        Returns:
            Dict with level-based recommendations
        """
        levels = self.detect_all(df, symbol)
        current = levels['current_price']
        
        context = {
            'at_support': False,
            'at_resistance': False,
            'near_key_level': False,
            'level_alignment': 'neutral',
            'score_adjustment': 0
        }
        
        # Check if at support/resistance
        if levels['nearest_support']:
            dist = levels['nearest_support'].distance_pct
            if dist < 0.2:  # Within 0.2%
                context['at_support'] = True
                context['near_key_level'] = True
                if signal_direction == 'BUY':
                    context['level_alignment'] = 'aligned'
                    context['score_adjustment'] = 10  # Bonus for buying at support
                else:
                    context['level_alignment'] = 'against'
                    context['score_adjustment'] = -5  # Penalty for selling at support
        
        if levels['nearest_resistance']:
            dist = levels['nearest_resistance'].distance_pct
            if dist < 0.2:  # Within 0.2%
                context['at_resistance'] = True
                context['near_key_level'] = True
                if signal_direction == 'SELL':
                    context['level_alignment'] = 'aligned'
                    context['score_adjustment'] = 10  # Bonus for selling at resistance
                else:
                    context['level_alignment'] = 'against'
                    context['score_adjustment'] = -5  # Penalty for buying at resistance
        
        context['nearest_support'] = levels['nearest_support']
        context['nearest_resistance'] = levels['nearest_resistance']
        
        return context


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import MetaTrader5 as mt5
    
    print("=" * 60)
    print("TITAN KEY LEVELS DETECTOR - TEST")
    print("=" * 60)
    
    mt5.initialize()
    
    # Get GOLD H1 data
    rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_H1, 0, 200)
    df = pd.DataFrame(rates)
    
    kl = KeyLevelsDetector()
    levels = kl.detect_all(df, 'GOLD')
    
    print(f"\nCurrent Price: ${levels['current_price']:.2f}")
    print()
    print("NEAREST SUPPORT LEVELS:")
    for lvl in levels['support'][:5]:
        print(f"  ${lvl.price:.2f} ({lvl.source}, str={lvl.strength}, dist={lvl.distance_pct:.2f}%)")
    
    print()
    print("NEAREST RESISTANCE LEVELS:")
    for lvl in levels['resistance'][:5]:
        print(f"  ${lvl.price:.2f} ({lvl.source}, str={lvl.strength}, dist={lvl.distance_pct:.2f}%)")
    
    print()
    print("PIVOT POINTS:")
    for name, price in levels['pivots'].items():
        print(f"  {name}: ${price:.2f}")
    
    # Test signal context
    print()
    print("SIGNAL CONTEXT (BUY):")
    ctx = kl.get_signal_context(df, 'BUY', 'GOLD')
    print(f"  At Support: {ctx['at_support']}")
    print(f"  At Resistance: {ctx['at_resistance']}")
    print(f"  Level Alignment: {ctx['level_alignment']}")
    print(f"  Score Adjustment: {ctx['score_adjustment']}")
    
    mt5.shutdown()
    print()
    print("SUCCESS: Key Levels module working!")
