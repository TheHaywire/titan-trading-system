from .base import BaseStrategy
import pandas as pd
import ta
import numpy as np

class MomentumScalper(BaseStrategy):
    """
    Aggressive Scalping Strategy.
    
    Logic:
    1. Identify strong short-term momentum (RSI + MACD).
    2. Enter on pullbacks to short-term EMAs.
    3. Tight Stop Loss, Quick Take Profit.
    4. High Frequency logic.
    """
    
    def __init__(self, config=None):
        super().__init__("MomentumScalper", config or {})
        self.rsi_period = self.config.get('rsi_period', 14)
        self.ema_short = self.config.get('ema_short', 9)
        self.ema_long = self.config.get('ema_long', 21)
        self.adx_threshold = self.config.get('adx_threshold', 20)

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        if df is None or len(df) < 50:
            return {"signal": "HOLD", "reason": "Not enough data"}

        # 1. Indicators
        df['rsi'] = ta.momentum.rsi(df['close'], window=self.rsi_period)
        df['ema_short'] = ta.trend.ema_indicator(df['close'], window=self.ema_short)
        df['ema_long'] = ta.trend.ema_indicator(df['close'], window=self.ema_long)
        
        adx = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['adx'] = adx.adx()
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # 2. Logic
        signal = "HOLD"
        reason = "Wait"
        confidence = 0.0
        
        # Trend Filter: ADX > 20
        if curr['adx'] < self.adx_threshold:
            return {"signal": "HOLD", "reason": "Low Volatility", "metrics": {"adx": curr['adx']}}

        # BULLISH SCALP
        # - Price > EMA Long (Trend Up)
        # - Price dipped below EMA Short (Pullback)
        # - RSI Oversold in Up Trend (< 40) OR RSI curling up
        # Aggressive: Enter when price crosses back above EMA short
        
        is_uptrend = curr['close'] > curr['ema_long']
        pullback_buy = (prev['close'] < prev['ema_short']) and (curr['close'] > curr['ema_short'])
        
        if is_uptrend and pullback_buy and curr['rsi'] > 50:
            signal = "BUY"
            reason = "EMA Crossover Pullback"
            confidence = 0.85
            
        # BEARISH SCALP
        is_downtrend = curr['close'] < curr['ema_long']
        pullback_sell = (prev['close'] > prev['ema_short']) and (curr['close'] < curr['ema_short'])
        
        if is_downtrend and pullback_sell and curr['rsi'] < 50:
            signal = "SELL"
            reason = "EMA Crossover Pullback"
            confidence = 0.85
            
        return {
            "signal": signal,
            "reason": reason,
            "confidence": confidence,
            "metrics": {
                "rsi": round(curr['rsi'], 2),
                "adx": round(curr['adx'], 2)
            }
        }
