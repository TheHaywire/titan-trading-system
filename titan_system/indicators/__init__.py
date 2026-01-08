"""
Titan Indicators Module
=======================
High-performance technical indicators powered by TA-Lib.
"""

from .talib_indicators import (
    TitanIndicators,
    calculate_indicators,
    detect_candlestick_patterns,
    TALIB_AVAILABLE
)

__all__ = [
    'TitanIndicators',
    'calculate_indicators',
    'detect_candlestick_patterns',
    'TALIB_AVAILABLE'
]
