"""
Shared Technical Pattern Recognition Module
Used by Institutional Analyst and Alert Monitor.
"""

import numpy as np
import pandas as pd
from scipy.signal import argrelextrema

def detect_candlestick_patterns(df: pd.DataFrame) -> list:
    """Detect common candlestick patterns"""
    patterns = []
    
    if len(df) < 3:
        return patterns
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    body = abs(latest['close'] - latest['open'])
    upper_wick = latest['high'] - max(latest['close'], latest['open'])
    lower_wick = min(latest['close'], latest['open']) - latest['low']
    candle_range = latest['high'] - latest['low']
    
    # Generic Body Size for comparison
    avg_body = df['close'].diff().abs().tail(20).mean()
    
    # Hammer (Bullish Reversal)
    if lower_wick > (2 * body) and upper_wick < (0.3 * body) and candle_range > 0:
        if latest['close'] > latest['open']:
            patterns.append("🔨 HAMMER (Bullish Reversal)")
    
    # Shooting Star (Bearish Reversal)
    if upper_wick > (2 * body) and lower_wick < (0.3 * body) and candle_range > 0:
        if latest['close'] < latest['open']:
            patterns.append("⭐ SHOOTING STAR (Bearish Reversal)")
    
    # Bullish Engulfing
    if (prev['close'] < prev['open'] and latest['close'] > latest['open'] and
        latest['open'] <= prev['close'] and latest['close'] >= prev['open']):
        patterns.append("📈 BULLISH ENGULFING (Strong Buy)")
    
    # Bearish Engulfing
    if (prev['close'] > prev['open'] and latest['close'] < latest['open'] and
        latest['open'] >= prev['close'] and latest['close'] <= prev['open']):
        patterns.append("📉 BEARISH ENGULFING (Strong Sell)")
    
    # Doji (Indecision)
    if candle_range > 0 and body < (0.1 * candle_range):
        patterns.append("✖️ DOJI (Indecision/Reversal)")
    
    return patterns

def detect_chart_patterns(df: pd.DataFrame) -> list:
    """Detect advanced chart patterns like double tops/bottoms, triangles, etc."""
    patterns = []
    
    # Use a slice for pattern recognition (last 100 bars)
    recent = df.tail(100)
    if len(recent) < 50:
        return []
        
    # Double Top
    highs_idx = argrelextrema(recent['high'].values, np.greater, order=5)[0]
    if len(highs_idx) >= 2:
        last_two_highs = recent['high'].iloc[highs_idx[-2:]].values
        if abs(last_two_highs[0] - last_two_highs[1]) / last_two_highs[0] < 0.002:  # Within 0.2%
            patterns.append("📉 DOUBLE TOP (Bearish Reversal)")
    
    # Double Bottom
    lows_idx = argrelextrema(recent['low'].values, np.less, order=5)[0]
    if len(lows_idx) >= 2:
        last_two_lows = recent['low'].iloc[lows_idx[-2:]].values
        if abs(last_two_lows[0] - last_two_lows[1]) / last_two_lows[0] < 0.002:
            patterns.append("📈 DOUBLE BOTTOM (Bullish Reversal)")
    
    # Consolidation / Range
    recent_50 = df.tail(50)
    recent_range = recent_50['high'].max() - recent_50['low'].min()
    if recent_range / recent_50['close'].iloc[-1] < 0.015:  # Less than 1.5% range
        patterns.append("📦 TIGHT CONSOLIDATION (Breakout Pending)")
    
    # Pennant/Triangle
    if len(highs_idx) >= 3 and len(lows_idx) >= 3:
        try:
            high_slope = np.polyfit(highs_idx[-3:], recent['high'].iloc[highs_idx[-3:]].values, 1)[0]
            low_slope = np.polyfit(lows_idx[-3:], recent['low'].iloc[lows_idx[-3:]].values, 1)[0]
            
            # Pennant: converging trendlines
            if high_slope < 0 and low_slope > 0:
                patterns.append("🚩 PENNANT (Continuation Pattern)")
            # Ascending Triangle
            elif abs(high_slope) < 0.1 and low_slope > 0:
                patterns.append("📐 ASCENDING TRIANGLE (Bullish Bias)")
            # Descending Triangle
            elif high_slope < 0 and abs(low_slope) < 0.1:
                patterns.append("📐 DESCENDING TRIANGLE (Bearish Bias)")
        except:
            pass
            
    return patterns

def detect_divergences(df: pd.DataFrame) -> list:
    """Detect RSI divergences"""
    divergences = []
    
    if 'RSI' not in df.columns:
        return []
        
    recent = df.tail(100)
    if len(recent) < 20:
        return []
        
    # peaks for price and RSI
    price_highs_idx = argrelextrema(recent['close'].values, np.greater, order=5)[0]
    rsi_highs_idx = argrelextrema(recent['RSI'].values, np.greater, order=5)[0]
    
    # Bearish Divergence
    if len(price_highs_idx) >= 2 and len(rsi_highs_idx) >= 2:
        if (recent['close'].iloc[price_highs_idx[-1]] > recent['close'].iloc[price_highs_idx[-2]] and
            recent['RSI'].iloc[rsi_highs_idx[-1]] < recent['RSI'].iloc[rsi_highs_idx[-2]]):
            divergences.append("🔴 BEARISH DIVERGENCE (Price HH, RSI LH)")
    
    # Bullish Divergence
    price_lows_idx = argrelextrema(recent['close'].values, np.less, order=5)[0]
    rsi_lows_idx = argrelextrema(recent['RSI'].values, np.less, order=5)[0]
    
    if len(price_lows_idx) >= 2 and len(rsi_lows_idx) >= 2:
        if (recent['close'].iloc[price_lows_idx[-1]] < recent['close'].iloc[price_lows_idx[-2]] and
            recent['RSI'].iloc[rsi_lows_idx[-1]] > recent['RSI'].iloc[rsi_lows_idx[-2]]):
            divergences.append("🟢 BULLISH DIVERGENCE (Price LL, RSI HL)")
            
    return divergences

def get_all_patterns(df: pd.DataFrame) -> list:
    """Run all pattern detection logic"""
    return detect_candlestick_patterns(df) + detect_chart_patterns(df) + detect_divergences(df)
