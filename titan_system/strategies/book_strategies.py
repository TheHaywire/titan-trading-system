
import pandas as pd
import numpy as np

class BookTechnicalStrategy:
    """
    Implements classic technical analysis strategies from 'Technical Analysis For Dummies 2nd Edition'.
    Focuses on:
    1. Moving Average Crossovers (Chapter 12)
    2. RSI Momentum (Chapter 13)
    3. Bollinger Band Breakouts (Chapter 14)
    """

    def __init__(self, use_trend_filter=False, require_confluence=False):
        self.use_trend_filter = use_trend_filter
        self.require_confluence = require_confluence

    def calculate_indicators(self, df):
        """
        Adds technical indicators to the DataFrame.
        """
        df = df.copy()
        
        # --- Chapter 12: Dynamic Lines (Moving Averages) ---
        df['SMA_50'] = df['close'].rolling(window=50).mean()
        df['SMA_200'] = df['close'].rolling(window=200).mean()
        
        # --- Chapter 13: Measuring Momentum (RSI) ---
        # Standard RSI 14 calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        
        # Avoid division by zero
        rs = gain / loss.replace(0, np.nan)
        df['RSI_14'] = 100 - (100 / (1 + rs))
        df['RSI_14'] = df['RSI_14'].fillna(50) # Default to neutral

        # --- Chapter 14: Estimating Volatility (Bollinger Bands) ---
        # 20 SMA +/- 2 StdDev
        df['BB_Mid'] = df['close'].rolling(window=20).mean()
        df['BB_Std'] = df['close'].rolling(window=20).std()
        df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])

        # --- Chapter 14: Estimating Volatility (ATR) ---
        # TR = Max(High-Low, Abs(High-ClosePrev), Abs(Low-ClosePrev))
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR_14'] = tr.rolling(window=14).mean()
        
        return df

    def analyze(self, df):
        """
        Analyzes the dataframe for trade signals based on book concepts.
        Returns a list of signal dictionaries.
        """
        df = self.calculate_indicators(df)
        signals = []

        # We need at least 200 bars for SMA_200
        if len(df) < 201:
            return signals

        # Check the last closed candle (index -2 if -1 is current forming cap)
        # But commonly in backtests we look at -1 as "just closed".
        # Let's look for a crossover that happened at index i (defaults to last completed)
        
        i = len(df) - 1
        curr = df.iloc[i]
        prev = df.iloc[i-1]

        # --- Base Filters ---
        # 1. Trend Filter: "The Trend is Your Friend" (Chapter 12)
        # Only Buy if Price > 200 SMA (Long-term Bullish)
        # Only Sell if Price < 200 SMA (Long-term Bearish)
        trend_long = True
        trend_short = True
        
        if self.use_trend_filter:
            trend_long = curr['close'] > curr['SMA_200']
            trend_short = curr['close'] < curr['SMA_200']

        # --- Signal Generation ---

        # --- Strategy 1: The Golden Cross / Death Cross (Chapter 12) ---
        # Golden Cross: 50 crosses above 200
        # (This is a trend reversal signal itself, so we might skip the trend filter check aka SMA200 check creates a circular logic for the cross itself, 
        # but usually you take the cross regardless, OR you wait for price to settle. 
        # For a pure golden cross, the cross IS the trend change. We'll exempt it from the 'Price > SMA 200' filter or logic holds implicitly)
        if prev['SMA_50'] <= prev['SMA_200'] and curr['SMA_50'] > curr['SMA_200']:
            signals.append({
                'strategy': 'MA_Golden_Cross',
                'signal': 'BUY',
                'price': curr['close'],
                'time': curr['time'],
                'comment': 'Bullish Trend Reversal: 50 SMA crossed above 200 SMA'
            })
        
        # Death Cross: 50 crosses below 200
        if prev['SMA_50'] >= prev['SMA_200'] and curr['SMA_50'] < curr['SMA_200']:
            signals.append({
                'strategy': 'MA_Death_Cross',
                'signal': 'SELL',
                'price': curr['close'],
                'time': curr['time'],
                'comment': 'Bearish Trend Reversal: 50 SMA crossed below 200 SMA'
            })

        # --- Strategy 2: RSI Extremes (Chapter 13) ---
        # Buy when crossing back up above 30 (Leaving Oversold)
        if prev['RSI_14'] < 30 and curr['RSI_14'] >= 30:
             if not self.use_trend_filter or trend_long:
                 signals.append({
                    'strategy': 'RSI_Oversold_Reversal',
                    'signal': 'BUY',
                    'price': curr['close'],
                    'time': curr['time'],
                    'comment': 'Momentum Recovery: RSI crossed back above 30'
                })
             
        # Sell when crossing back down below 70 (Leaving Overbought)
        if prev['RSI_14'] > 70 and curr['RSI_14'] <= 70:
             if not self.use_trend_filter or trend_short:
                 signals.append({
                    'strategy': 'RSI_Overbought_Reversal',
                    'signal': 'SELL',
                    'price': curr['close'],
                    'time': curr['time'],
                    'comment': 'Momentum Exhaustion: RSI crossed back below 70'
                })

        # --- Strategy 3: Bollinger Band Breakout (Chapter 14) ---
        # Close above upper band (Strong Momentum)
        # Note: Some treat this as mean reversion (sell), but the book emphasizes "walking the bands" as trend confirmation.
        # We will treat a fresh breakout as a Buy Signal (Breakout Principle - Chapter 19).
        if prev['close'] <= prev['BB_Upper'] and curr['close'] > curr['BB_Upper']:
             if not self.use_trend_filter or trend_long:
                 signals.append({
                    'strategy': 'Bollinger_Breakout_Upper',
                    'signal': 'BUY',
                    'price': curr['close'],
                    'time': curr['time'],
                    'comment': 'Volatility Breakout: Close above Upper Bollinger Band'
                })

        if prev['close'] >= prev['BB_Lower'] and curr['close'] < curr['BB_Lower']:
             if not self.use_trend_filter or trend_short:
                 signals.append({
                    'strategy': 'Bollinger_Breakout_Lower',
                    'signal': 'SELL',
                    'price': curr['close'],
                    'time': curr['time'],
                    'comment': 'Volatility Breakout: Close below Lower Bollinger Band'
                })

        return signals

