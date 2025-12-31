
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator, StochasticOscillator, WilliamsRIndicator
from ta.trend import MACD, EMAIndicator, ADXIndicator, IchimokuIndicator, CCIIndicator
from ta.volatility import BollingerBands, AverageTrueRange, KeltnerChannel
from ta.volume import OnBalanceVolumeIndicator

class IndicatorFactory:
    """
    Centralized factory for calculating technical indicators.
    Provides standard settings for 'Titan Intelligence'.
    """

    @staticmethod
    def calculate_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Applies a full suite of technical indicators to the dataframe.
        Expects: 'open', 'high', 'low', 'close', 'volume' columns.
        """
        if df is None or len(df) < 50:
            return df

        # --- Trend Indicators ---
        
        # EMAs
        df['ema_9'] = EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_21'] = EMAIndicator(close=df['close'], window=21).ema_indicator()
        df['ema_50'] = EMAIndicator(close=df['close'], window=50).ema_indicator()
        df['ema_200'] = EMAIndicator(close=df['close'], window=200).ema_indicator()
        
        # MACD (12, 26, 9)
        macd = MACD(close=df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        # ADX (14) - Trend Strength
        adx = ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14)
        df['adx'] = adx.adx()
        
        # Ichimoku Cloud (9, 26, 52)
        ichimoku = IchimokuIndicator(high=df['high'], low=df['low'])
        df['ichimoku_a'] = ichimoku.ichimoku_a()
        df['ichimoku_b'] = ichimoku.ichimoku_b()
        df['ichimoku_base_line'] = ichimoku.ichimoku_base_line()
        df['ichimoku_conversion_line'] = ichimoku.ichimoku_conversion_line()

        # --- Momentum Indicators ---
        
        # RSI (14)
        df['rsi'] = RSIIndicator(close=df['close'], window=14).rsi()
        
        # Stochastic (14, 3, 3)
        stoch = StochasticOscillator(high=df['high'], low=df['low'], close=df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()

        # --- Volatility Indicators ---
        
        # Bollinger Bands (20, 2)
        bb = BollingerBands(close=df['close'], window=20, window_dev=2)
        df['bb_upper'] = bb.bollinger_hband()
        df['bb_lower'] = bb.bollinger_lband()
        df['bb_width'] = bb.bollinger_wband()
        
        # ATR (14)
        df['atr'] = AverageTrueRange(high=df['high'], low=df['low'], close=df['close']).average_true_range()

        # Keltner Channels
        keltner = KeltnerChannel(high=df['high'], low=df['low'], close=df['close'], window=20)
        df['keltner_h'] = keltner.keltner_channel_hband()
        df['keltner_l'] = keltner.keltner_channel_lband()
        
        # --- Other Oscillators ---
        
        # CCI (20)
        df['cci'] = CCIIndicator(high=df['high'], low=df['low'], close=df['close'], window=20).cci()
        
        # Williams %R (14)
        df['willr'] = WilliamsRIndicator(high=df['high'], low=df['low'], close=df['close'], lbp=14).williams_r()
        
        # --- Volume ---
        # Note: OBV sensitive to broker volume data quality
        df['obv'] = OnBalanceVolumeIndicator(close=df['close'], volume=df['volume']).on_balance_volume()


        # --- Price Action Levels ---
        df = IndicatorFactory._calculate_pivot_points(df)
        df = IndicatorFactory._detect_candlestick_patterns(df)

        return df

    @staticmethod
    def _detect_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
        """Detects simple patterns: Doji, Engulfing."""
        # Doji
        body_size = (df['close'] - df['open']).abs()
        range_size = df['high'] - df['low']
        df['is_doji'] = body_size <= (range_size * 0.1)
        
        # Engulfing (Bullish)
        prev_close = df['close'].shift(1)
        prev_open = df['open'].shift(1)
        is_bullish = (df['close'] > df['open'])
        prev_red = (prev_close < prev_open)
        
        df['engulfing_bull'] = is_bullish & prev_red & (df['close'] > prev_open) & (df['open'] < prev_close)
        
        # Engulfing (Bearish)
        is_bearish = (df['close'] < df['open'])
        prev_green = (prev_close > prev_open)
        
        df['engulfing_bear'] = is_bearish & prev_green & (df['close'] < prev_open) & (df['open'] > prev_close)
        
        return df


    @staticmethod
    def _calculate_pivot_points(df: pd.DataFrame) -> pd.DataFrame:
        """Calculates Classic Pivot Points based on the previous candle."""
        # Note: This calculates pivot for the current candle based on previous.
        # Ideally, easy way is (High + Low + Close) / 3 of PREVIOUS row
        
        df['pivot_pp'] = (df['high'].shift(1) + df['low'].shift(1) + df['close'].shift(1)) / 3
        df['pivot_r1'] = (2 * df['pivot_pp']) - df['low'].shift(1)
        df['pivot_s1'] = (2 * df['pivot_pp']) - df['high'].shift(1)
        df['pivot_r2'] = df['pivot_pp'] + (df['high'].shift(1) - df['low'].shift(1))
        df['pivot_s2'] = df['pivot_pp'] - (df['high'].shift(1) - df['low'].shift(1))
        
        return df

    @staticmethod
    def get_market_state(df: pd.DataFrame) -> dict:
        """
        analyzes the latest candle to determine the 'Market State'.
        Returns: Dict with trend, bias, and key signals.
        """
        if df is None or len(df) < 1:
            return {}

        last = df.iloc[-1]
        
        # 1. Determine Trend (EMA Alignment)
        trend = "NEUTRAL"
        if last['close'] > last['ema_50'] > last['ema_200']:
            trend = "BULLISH"
        elif last['close'] < last['ema_50'] < last['ema_200']:
            trend = "BEARISH"
            
        # 2. Determine Momentum (RSI + MACD)
        momentum = "NEUTRAL"
        if last['rsi'] > 50 and last['macd'] > last['macd_signal']:
            momentum = "BULLISH"
        elif last['rsi'] < 50 and last['macd'] < last['macd_signal']:
            momentum = "BEARISH"
            
        return {
            "trend": trend,
            "momentum": momentum,
            "volatility": "HIGH" if last['bb_width'] > df['bb_width'].mean() else "LOW",
            "rsi": round(last['rsi'], 2),
            "adx": round(last['adx'], 2)
        }
