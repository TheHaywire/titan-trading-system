import pandas as pd
import ta

class Strategy:
    def __init__(self, symbol, timeframe, params=None):
        self.symbol = symbol
        self.timeframe = timeframe
        
        # Default Parameters (The "Genes")
        if params is None:
            params = {
                'sma_fast': 50,
                'sma_slow': 200,
                'rsi_period': 14,
                'rsi_overbought': 70,
                'rsi_oversold': 30
            }
        self.params = params

    def generate_signal(self, df):
        """
        Analyzes the dataframe and returns a signal based on dynamic params.
        """
        if df is None or len(df) < self.params['sma_slow']:
            return None

        # 1. Calculate Indicators
        # Using self.params for window sizes
        df['sma_fast'] = ta.trend.sma_indicator(df['close'], window=int(self.params['sma_fast']))
        df['sma_slow'] = ta.trend.sma_indicator(df['close'], window=int(self.params['sma_slow']))
        df['rsi'] = ta.momentum.rsi(df['close'], window=int(self.params['rsi_period']))

        # Get the last two rows to check for crossover/conditions
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]

        # 2. Logic
        # Condition A: Trend (SMA Crossover)
        bullish_cross = prev_row['sma_fast'] <= prev_row['sma_slow'] and last_row['sma_fast'] > last_row['sma_slow']
        bearish_cross = prev_row['sma_fast'] >= prev_row['sma_slow'] and last_row['sma_fast'] < last_row['sma_slow']
        
        # Condition B: Trend Following (Already crossed)
        bullish_trend = last_row['sma_fast'] > last_row['sma_slow']
        bearish_trend = last_row['sma_fast'] < last_row['sma_slow']

        # Condition C: RSI Filter (Don't buy top, Don't sell bottom)
        rsi_ok_buy = last_row['rsi'] < self.params['rsi_overbought']
        rsi_ok_sell = last_row['rsi'] > self.params['rsi_oversold']

        # Signal Generation
        # 1. Crossover Entry (Strongest)
        if bullish_cross and rsi_ok_buy:
            return 'BUY'
        if bearish_cross and rsi_ok_sell:
            return 'SELL'
            
        # 2. Pullback Entry (Optional - if RSI dips in trend)
        # (Keeping it simple for now, sticking to crossover as primary trigger)
        
        return None

    def get_market_regime(self, df):
        """
        Returns 'TRENDING' if ADX > 25, else 'RANGING'.
        Also returns the ADX value.
        """
        if df is None or len(df) < 50:
            return {'status': 'UNKNOWN', 'adx': 0}

        # Calculate ADX (Average Directional Index)
        adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        adx_value = adx_indicator.adx().iloc[-1]
        
        status = 'TRENDING' if adx_value > 25 else 'RANGING'
        return {'status': status, 'adx': round(adx_value, 2)}
