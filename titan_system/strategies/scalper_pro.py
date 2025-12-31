
import pandas as pd
import numpy as np
import pandas_ta as ta
from titan_system.strategies.base import BaseStrategy

class MomentumScalper(BaseStrategy):
    """
    High-Frequency Scalper for M1/M5 timeframes.
    Focus: Speed, Momentum, Tight Stops.
    """
    
    def __init__(self, config=None):
        super().__init__("MomentumScalper", config or {})
        # self.name is set by BaseStrategy
        self.rsi_period = self.config.get("rsi_period", 14)
        self.ema_fast = self.config.get("ema_fast", 9)
        self.ema_slow = self.config.get("ema_slow", 21)
        self.atr_period = self.config.get("atr_period", 14)
        
    def analyze(self, symbol: str, data: pd.DataFrame) -> dict:
        if data is None or len(data) < 50:
            return None
            
        df = data.copy()
        
        # Indicators
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_period)
        df['ema_fast'] = ta.ema(df['close'], length=self.ema_fast)
        df['ema_slow'] = ta.ema(df['close'], length=self.ema_slow)
        df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=self.atr_period)
        
        # Current Candle
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        atr = curr['atr']
        price = curr['close']
        
        signal = None
        confidence = 0.0
        
        # 1. EMA Crossover (Momentum) - AGGRESSIVE MODE
        bullish_cross = (prev['ema_fast'] <= prev['ema_slow']) and (curr['ema_fast'] > curr['ema_slow'])
        bearish_cross = (prev['ema_fast'] >= prev['ema_slow']) and (curr['ema_fast'] < curr['ema_slow'])
        
        # BUY LOGIC - NO RSI FILTER (Pure Momentum)
        if bullish_cross:
            signal = "BUY"
            confidence = 0.85  # High confidence on pure cross
            sl = price - (atr * 1.2) # Tighter stop for scalping
            tp = price + (atr * 1.5) # Quick 1:1.25 target
            
        # SELL LOGIC
        elif bearish_cross:
            signal = "SELL"
            confidence = 0.85
            sl = price + (atr * 1.2)
            tp = price - (atr * 1.5)
            
        # 3. Volatility Squeeze (Secondary Trigger - Optional)
        # If no cross, check for breakout of recent high/low? (Skipped for pure speed simplicity)

        if signal:
            return {
                "signal": signal,
                "confidence": confidence,
                "stop_loss": sl,
                "take_profit": tp,
                "strategy": self.name,
                "reason": f"EMA Cross + RSI {curr['rsi']:.1f}"
            }
            
        return None
