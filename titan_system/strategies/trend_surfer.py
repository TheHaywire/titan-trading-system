
import pandas as pd
import ta
import logging
from titan_system.strategies.base import BaseStrategy

logger = logging.getLogger("Titan.Strategy.TrendSurfer")

class TrendSurfer(BaseStrategy):
    """
    Classic trend following strategy with Market Regime filter.
    buy: SMA_fast > SMA_slow AND RSI < 70 AND ADX > 25
    sell: SMA_fast < SMA_slow AND RSI > 30 AND ADX > 25
    """
    def __init__(self, config=None):
        super().__init__("TrendSurfer", config or {})
        self.fast_period = config.get("fast_period", 50)
        self.slow_period = config.get("slow_period", 200)
        self.rsi_period = config.get("rsi_period", 14)
        self.adx_threshold = config.get("adx_threshold", 25)

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        if df is None or len(df) < self.slow_period:
            return {"signal": "HOLD", "reason": "Not enough data"}

        # 1. Feature Engineering
        df['sma_fast'] = ta.trend.sma_indicator(df['close'], window=self.fast_period)
        df['sma_slow'] = ta.trend.sma_indicator(df['close'], window=self.slow_period)
        df['rsi'] = ta.momentum.rsi(df['close'], window=self.rsi_period)
        
        # ADX (Market Regime)
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        df['adx'] = adx_ind.adx()

        curr = df.iloc[-1]
        prev = df.iloc[-2]

        # 2. Logic
        signal = "HOLD"
        reason = "Wait"
        confidence = 0.0

        # REGIME CHECK
        if curr['adx'] < self.adx_threshold:
            return {
                "signal": "HOLD", 
                "reason": f"Choppy Market (ADX {curr['adx']:.1f} < {self.adx_threshold})",
                "regime": "RANGING"
            }

        # TREND CHECK
        if curr['sma_fast'] > curr['sma_slow']:
            # Uptrend
            if curr['rsi'] < 70: # Not overbought
                            # Crossover confirmed or pull-back entry?
                # Simple Logic: Price above Fast SMA
                if curr['close'] > curr['sma_fast']:
                    signal = "BUY"
                    reason = "Uptrend + Momentum"
                    confidence = 0.8
        
        elif curr['sma_fast'] < curr['sma_slow']:
            # Downtrend
            if curr['rsi'] > 30: # Not oversold
                if curr['close'] < curr['sma_fast']:
                    signal = "SELL"
                    reason = "Downtrend + Momentum"
                    confidence = 0.8

        return {
            "signal": signal,
            "reason": reason,
            "confidence": confidence,
            "regime": "TRENDING",
            "metrics": {
                "adx": round(curr['adx'], 2),
                "rsi": round(curr['rsi'], 2),
                "sma_fast": round(curr['sma_fast'], 5),
                "sma_slow": round(curr['sma_slow'], 5)
            }
        }
