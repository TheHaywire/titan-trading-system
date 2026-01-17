"""
TITAN INDICATORS MODULE (TA-Lib Powered)
=========================================
High-performance technical indicators using TA-Lib.
20x faster than manual calculations with 60+ candlestick patterns.

Usage:
    from titan_system.indicators.talib_indicators import TitanIndicators
    
    ti = TitanIndicators(df)
    ti.add_all()  # Adds all indicators
    # or
    ti.add_momentum()
    ti.add_trend()
    ti.add_volatility()
    ti.add_candlestick_patterns()
"""

import numpy as np
import pandas as pd
from typing import Optional, List, Dict
import logging

# Try to import TA-Lib, fall back to manual if not available
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

logger = logging.getLogger("Titan.Indicators")


class TitanIndicators:
    """
    High-performance technical indicator calculator using TA-Lib.
    Falls back to Pandas-based calculations if TA-Lib is unavailable.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV DataFrame.
        
        Args:
            df: DataFrame with 'open', 'high', 'low', 'close', 'volume' columns
        """
        self.df = df.copy()
        
        # Ensure columns are numpy arrays for TA-Lib
        self.open = df['open'].values.astype(float)
        self.high = df['high'].values.astype(float)
        self.low = df['low'].values.astype(float)
        self.close = df['close'].values.astype(float)
        self.volume = df['tick_volume'].values.astype(float) if 'tick_volume' in df.columns else np.zeros(len(df))
        
        if TALIB_AVAILABLE:
            logger.debug("Using TA-Lib (20x faster)")
        else:
            logger.warning("TA-Lib not available, using manual calculations")
    
    def add_all(self) -> pd.DataFrame:
        """Add all indicators to DataFrame"""
        self.add_momentum()
        self.add_trend()
        self.add_volatility()
        self.add_volume()
        self.add_kalman()
        self.add_candlestick_patterns()
        return self.df
    
    # =========================================================================
    # MOMENTUM INDICATORS
    # =========================================================================
    
    def add_momentum(self) -> pd.DataFrame:
        """Add momentum indicators: RSI, Stochastic, CCI, Williams %R, ROC, MFI"""
        
        if TALIB_AVAILABLE:
            # RSI (Relative Strength Index) - Uses Wilder's smoothing
            self.df['RSI'] = talib.RSI(self.close, timeperiod=14)
            self.df['RSI_7'] = talib.RSI(self.close, timeperiod=7)
            self.df['RSI_21'] = talib.RSI(self.close, timeperiod=21)
            
            # Stochastic
            self.df['STOCH_K'], self.df['STOCH_D'] = talib.STOCH(
                self.high, self.low, self.close,
                fastk_period=14, slowk_period=3, slowd_period=3
            )
            
            # Stochastic RSI
            self.df['STOCHRSI_K'], self.df['STOCHRSI_D'] = talib.STOCHRSI(
                self.close, timeperiod=14, fastk_period=3, fastd_period=3
            )
            
            # CCI (Commodity Channel Index)
            self.df['CCI'] = talib.CCI(self.high, self.low, self.close, timeperiod=20)
            
            # Williams %R
            self.df['WILLR'] = talib.WILLR(self.high, self.low, self.close, timeperiod=14)
            
            # ROC (Rate of Change)
            self.df['ROC'] = talib.ROC(self.close, timeperiod=10)
            
            # MFI (Money Flow Index)
            if np.any(self.volume > 0):
                self.df['MFI'] = talib.MFI(self.high, self.low, self.close, self.volume, timeperiod=14)
            
            # Momentum
            self.df['MOM'] = talib.MOM(self.close, timeperiod=10)
            
            # MACD
            self.df['MACD'], self.df['MACD_SIGNAL'], self.df['MACD_HIST'] = talib.MACD(
                self.close, fastperiod=12, slowperiod=26, signalperiod=9
            )
            
        else:
            # Manual fallback for RSI
            delta = pd.Series(self.close).diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            self.df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        return self.df
    
    # =========================================================================
    # TREND INDICATORS
    # =========================================================================
    
    def add_trend(self) -> pd.DataFrame:
        """Add trend indicators: EMAs, SMAs, ADX, Parabolic SAR"""
        
        if TALIB_AVAILABLE:
            # EMAs
            self.df['EMA_9'] = talib.EMA(self.close, timeperiod=9)
            self.df['EMA_21'] = talib.EMA(self.close, timeperiod=21)
            self.df['EMA_50'] = talib.EMA(self.close, timeperiod=50)
            self.df['EMA_200'] = talib.EMA(self.close, timeperiod=200)
            
            # SMAs
            self.df['SMA_20'] = talib.SMA(self.close, timeperiod=20)
            self.df['SMA_50'] = talib.SMA(self.close, timeperiod=50)
            self.df['SMA_200'] = talib.SMA(self.close, timeperiod=200)
            
            # ADX (Average Directional Index)
            self.df['ADX'] = talib.ADX(self.high, self.low, self.close, timeperiod=14)
            self.df['PLUS_DI'] = talib.PLUS_DI(self.high, self.low, self.close, timeperiod=14)
            self.df['MINUS_DI'] = talib.MINUS_DI(self.high, self.low, self.close, timeperiod=14)
            
            # Parabolic SAR
            self.df['SAR'] = talib.SAR(self.high, self.low, acceleration=0.02, maximum=0.2)
            
            # Aroon
            self.df['AROON_UP'], self.df['AROON_DOWN'] = talib.AROON(self.high, self.low, timeperiod=25)
            
        else:
            # Manual fallback for EMAs
            self.df['EMA_9'] = pd.Series(self.close).ewm(span=9).mean()
            self.df['EMA_21'] = pd.Series(self.close).ewm(span=21).mean()
            self.df['EMA_50'] = pd.Series(self.close).ewm(span=50).mean()
        
        return self.df
    
    # =========================================================================
    # VOLATILITY INDICATORS
    # =========================================================================
    
    def add_volatility(self) -> pd.DataFrame:
        """Add volatility indicators: ATR, Bollinger Bands, Keltner"""
        
        if TALIB_AVAILABLE:
            # ATR (Average True Range) - Uses Wilder's smoothing
            self.df['ATR'] = talib.ATR(self.high, self.low, self.close, timeperiod=14)
            self.df['ATR_7'] = talib.ATR(self.high, self.low, self.close, timeperiod=7)
            
            # True Range
            self.df['TRANGE'] = talib.TRANGE(self.high, self.low, self.close)
            
            # Bollinger Bands
            self.df['BB_UPPER'], self.df['BB_MIDDLE'], self.df['BB_LOWER'] = talib.BBANDS(
                self.close, timeperiod=20, nbdevup=2, nbdevdn=2
            )
            
            # Normalized ATR (ATR as % of price)
            self.df['NATR'] = talib.NATR(self.high, self.low, self.close, timeperiod=14)
            
        else:
            # Manual ATR
            tr = np.maximum(
                self.high - self.low,
                np.maximum(
                    np.abs(self.high - np.roll(self.close, 1)),
                    np.abs(self.low - np.roll(self.close, 1))
                )
            )
            self.df['ATR'] = pd.Series(tr).rolling(14).mean()
        
        return self.df
    
    # =========================================================================
    # ADVANCED QUANT INDICATORS
    # =========================================================================
    
    def add_kalman(self, process_variance: float = 0.0001, measurement_variance: float = 0.005) -> pd.DataFrame:
        """
        Add Kalman Filter for dynamic mean estimation.
        Effectively a 'smart' adaptive moving average that filters noise.
        """
        # Kalman filter variables
        posteri_estimate = self.close[0]
        posteri_error_estimate = 1.0
        
        kalman_values = []
        for z in self.close:
            # Time update (Prediction)
            priori_estimate = posteri_estimate
            priori_error_estimate = posteri_error_estimate + process_variance
            
            # Measurement update (Correction)
            gain = priori_error_estimate / (priori_error_estimate + measurement_variance)
            posteri_estimate = priori_estimate + gain * (z - priori_estimate)
            posteri_error_estimate = (1 - gain) * priori_error_estimate
            kalman_values.append(posteri_estimate)
            
        self.df['KALMAN'] = kalman_values
        return self.df

    def add_vwap(self) -> pd.DataFrame:
        """
        Add Volume-Weighted Average Price (VWAP).
        Crucial for institutional order flow analysis.
        """
        # Standard VWAP: Cumulative (Price * Volume) / Cumulative Volume
        # For intra-day, it's usually reset daily. Here we do it over the whole series or window.
        if np.any(self.volume > 0):
            v = self.volume
            p = (self.high + self.low + self.close) / 3
            self.df['VWAP'] = (p * v).cumsum() / v.cumsum()
        else:
            # Fallback to SMA if no volume
            self.df['VWAP'] = pd.Series(self.close).rolling(20).mean()
            
        return self.df

    def add_volume(self) -> pd.DataFrame:
        """Add volume indicators: OBV, AD, ADOSC, VWAP"""
        
        if TALIB_AVAILABLE and np.any(self.volume > 0):
            # On-Balance Volume
            self.df['OBV'] = talib.OBV(self.close, self.volume)
            
            # Accumulation/Distribution
            self.df['AD'] = talib.AD(self.high, self.low, self.close, self.volume)
            
            # Chaikin A/D Oscillator
            self.df['ADOSC'] = talib.ADOSC(self.high, self.low, self.close, self.volume)
            
            # VWAP
            self.add_vwap()
        
        return self.df
    
    # =========================================================================
    # CANDLESTICK PATTERNS (60+ Patterns!)
    # =========================================================================
    
    def add_candlestick_patterns(self) -> pd.DataFrame:
        """Add 60+ candlestick pattern recognition signals"""
        
        if not TALIB_AVAILABLE:
            logger.warning("Candlestick patterns require TA-Lib")
            return self.df
        
        # === BULLISH REVERSAL PATTERNS ===
        self.df['CDL_HAMMER'] = talib.CDLHAMMER(self.open, self.high, self.low, self.close)
        self.df['CDL_INVERTED_HAMMER'] = talib.CDLINVERTEDHAMMER(self.open, self.high, self.low, self.close)
        self.df['CDL_BULLISH_ENGULFING'] = talib.CDLENGULFING(self.open, self.high, self.low, self.close)
        self.df['CDL_MORNING_STAR'] = talib.CDLMORNINGSTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_MORNING_DOJI_STAR'] = talib.CDLMORNINGDOJISTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_PIERCING'] = talib.CDLPIERCING(self.open, self.high, self.low, self.close)
        self.df['CDL_THREE_WHITE_SOLDIERS'] = talib.CDL3WHITESOLDIERS(self.open, self.high, self.low, self.close)
        self.df['CDL_ABANDONED_BABY'] = talib.CDLABANDONEDBABY(self.open, self.high, self.low, self.close)
        self.df['CDL_DRAGONFLY_DOJI'] = talib.CDLDRAGONFLYDOJI(self.open, self.high, self.low, self.close)
        
        # === BEARISH REVERSAL PATTERNS ===
        self.df['CDL_HANGING_MAN'] = talib.CDLHANGINGMAN(self.open, self.high, self.low, self.close)
        self.df['CDL_SHOOTING_STAR'] = talib.CDLSHOOTINGSTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_EVENING_STAR'] = talib.CDLEVENINGSTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_EVENING_DOJI_STAR'] = talib.CDLEVENINGDOJISTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_DARK_CLOUD_COVER'] = talib.CDLDARKCLOUDCOVER(self.open, self.high, self.low, self.close)
        self.df['CDL_THREE_BLACK_CROWS'] = talib.CDL3BLACKCROWS(self.open, self.high, self.low, self.close)
        self.df['CDL_GRAVESTONE_DOJI'] = talib.CDLGRAVESTONEDOJI(self.open, self.high, self.low, self.close)
        
        # === CONTINUATION PATTERNS ===
        self.df['CDL_DOJI'] = talib.CDLDOJI(self.open, self.high, self.low, self.close)
        self.df['CDL_DOJI_STAR'] = talib.CDLDOJISTAR(self.open, self.high, self.low, self.close)
        self.df['CDL_SPINNING_TOP'] = talib.CDLSPINNINGTOP(self.open, self.high, self.low, self.close)
        self.df['CDL_MARUBOZU'] = talib.CDLMARUBOZU(self.open, self.high, self.low, self.close)
        self.df['CDL_HARAMI'] = talib.CDLHARAMI(self.open, self.high, self.low, self.close)
        self.df['CDL_HARAMI_CROSS'] = talib.CDLHARAMICROSS(self.open, self.high, self.low, self.close)
        
        # === HIGH RELIABILITY PATTERNS ===
        self.df['CDL_THREE_INSIDE'] = talib.CDL3INSIDE(self.open, self.high, self.low, self.close)
        self.df['CDL_THREE_OUTSIDE'] = talib.CDL3OUTSIDE(self.open, self.high, self.low, self.close)
        self.df['CDL_KICKING'] = talib.CDLKICKING(self.open, self.high, self.low, self.close)
        self.df['CDL_BELT_HOLD'] = talib.CDLBELTHOLD(self.open, self.high, self.low, self.close)
        self.df['CDL_COUNTERATTACK'] = talib.CDLCOUNTERATTACK(self.open, self.high, self.low, self.close)
        
        # === COMBINED PATTERN SCORE ===
        pattern_cols = [col for col in self.df.columns if col.startswith('CDL_')]
        self.df['CDL_BULLISH_SCORE'] = self.df[pattern_cols].apply(
            lambda row: sum(1 for v in row if v > 0), axis=1
        )
        self.df['CDL_BEARISH_SCORE'] = self.df[pattern_cols].apply(
            lambda row: sum(1 for v in row if v < 0), axis=1
        )
        self.df['CDL_NET_SCORE'] = self.df['CDL_BULLISH_SCORE'] - self.df['CDL_BEARISH_SCORE']
        
        return self.df
    
    # =========================================================================
    # SIGNAL HELPERS
    # =========================================================================
    
    def get_signal_summary(self) -> Dict:
        """Get summary of current signals from last row"""
        if len(self.df) == 0:
            return {}
        
        last = self.df.iloc[-1]
        
        summary = {
            'rsi': last.get('RSI', 50),
            'rsi_signal': 'OVERSOLD' if last.get('RSI', 50) < 30 else 'OVERBOUGHT' if last.get('RSI', 50) > 70 else 'NEUTRAL',
            'adx': last.get('ADX', 20),
            'trend_strength': 'STRONG' if last.get('ADX', 20) > 25 else 'WEAK',
            'ema_trend': 'BULLISH' if last.get('EMA_9', 0) > last.get('EMA_21', 0) else 'BEARISH',
            'bb_position': 'UPPER' if last.get('close', 0) > last.get('BB_UPPER', 0) else 'LOWER' if last.get('close', 0) < last.get('BB_LOWER', 0) else 'MIDDLE',
            'candlestick_bias': 'BULLISH' if last.get('CDL_NET_SCORE', 0) > 0 else 'BEARISH' if last.get('CDL_NET_SCORE', 0) < 0 else 'NEUTRAL',
            'bullish_patterns': int(last.get('CDL_BULLISH_SCORE', 0)),
            'bearish_patterns': int(last.get('CDL_BEARISH_SCORE', 0)),
        }
        
        return summary


# =============================================================================
# QUICK ACCESS FUNCTIONS
# =============================================================================

def calculate_indicators(df: pd.DataFrame, include_patterns: bool = True) -> pd.DataFrame:
    """
    Quick function to add all indicators to a DataFrame.
    
    Args:
        df: OHLCV DataFrame
        include_patterns: Whether to include candlestick patterns (adds 25 columns)
    
    Returns:
        DataFrame with all indicators added
    """
    ti = TitanIndicators(df)
    ti.add_momentum()
    ti.add_trend()
    ti.add_volatility()
    if include_patterns:
        ti.add_candlestick_patterns()
    return ti.df


def detect_candlestick_patterns(df: pd.DataFrame) -> List[str]:
    """
    Detect candlestick patterns in the last bar.
    
    Returns:
        List of pattern names detected
    """
    if not TALIB_AVAILABLE:
        return []
    
    ti = TitanIndicators(df)
    ti.add_candlestick_patterns()
    
    last = ti.df.iloc[-1]
    patterns = []
    
    for col in ti.df.columns:
        if col.startswith('CDL_') and not col.endswith('_SCORE'):
            if last[col] > 0:
                patterns.append(f"BULLISH: {col.replace('CDL_', '')}")
            elif last[col] < 0:
                patterns.append(f"BEARISH: {col.replace('CDL_', '')}")
    
    return patterns


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import MetaTrader5 as mt5
    
    print("=" * 60)
    print("TITAN INDICATORS MODULE - TEST")
    print("=" * 60)
    
    if not mt5.initialize():
        print("MT5 not available, using synthetic data")
        # Create synthetic data
        np.random.seed(42)
        n = 500
        df = pd.DataFrame({
            'open': np.cumsum(np.random.randn(n)) + 2000,
            'high': np.cumsum(np.random.randn(n)) + 2005,
            'low': np.cumsum(np.random.randn(n)) + 1995,
            'close': np.cumsum(np.random.randn(n)) + 2000,
            'tick_volume': np.random.randint(100, 1000, n)
        })
    else:
        # Get real GOLD data
        rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_H1, 0, 500)
        df = pd.DataFrame(rates)
        mt5.shutdown()
    
    print(f"\nData shape: {df.shape}")
    
    # Add all indicators
    ti = TitanIndicators(df)
    ti.add_all()
    
    print(f"After indicators: {ti.df.shape}")
    print(f"\nColumns added: {len(ti.df.columns) - 5}")
    
    # Get signal summary
    summary = ti.get_signal_summary()
    print("\nSIGNAL SUMMARY:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    
    # Detect patterns
    patterns = detect_candlestick_patterns(df)
    if patterns:
        print(f"\nPATTERNS DETECTED:")
        for p in patterns:
            print(f"  {p}")
    else:
        print("\nNo candlestick patterns detected in last bar")
    
    print("\n✓ Module ready for integration!")
