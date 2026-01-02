
import pandas as pd
import ta
import logging
from titan_system.strategies.base import BaseStrategy

logger = logging.getLogger("Titan.Strategy.CryptoTrend")

class LiveCryptoTrend(BaseStrategy):
    """
    REGIME-BASED TREND FOLLOWER (Optimized for ETH/BTC)
    
    Configuration (WFA Optimized):
    - Fast EMA: 8
    - Slow EMA: 45
    - Signal: 9
    - Regime Filter: ADX(14) > 20
    
    This strategy ONLY attempts to trade when the market is in a confirmed TRENDING regime.
    If ADX < 20, it returns NEUTRAL/HOLD to preserve capital during chop.
    """
    
    def __init__(self, config=None):
        if config is None: config = {}
        # Default to Optimized Parameters
        config.setdefault('fast_period', 8)
        config.setdefault('slow_period', 45)
        config.setdefault('signal_period', 9)
        config.setdefault('adx_threshold', 20)
        
        super().__init__("CryptoTrend_MACD", config)
        
        self.fast_period = config['fast_period']
        self.slow_period = config['slow_period']
        self.signal_period = config['signal_period']
        self.adx_threshold = config['adx_threshold']

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Analyze logic:
        1. Check Data Sufficiency
        2. Calculate ADX (Regime)
        3. If Regime == TRENDING: Calculate MACD & Signal
        4. Else: RETURN HOLD
        """
        # Data Requirement: Need at least slow_period + extra for ADX/Signal smoothness
        min_bars = self.slow_period + 30 
        if df is None or len(df) < min_bars:
            return {"signal": "HOLD", "reason": "Insufficient Data"}

        # --- 1. REGIME FILTER (ADX) ---
        adx_ind = ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14)
        current_adx = adx_ind.adx().iloc[-1]
        
        regime = "TRENDING" if current_adx > self.adx_threshold else "CHOP"
        
        if regime == "CHOP":
            return {
                "signal": "HOLD",
                "reason": f"Regime Filter: ADX {current_adx:.1f} < {self.adx_threshold}",
                "confidence": 0.0,
                "regime": regime,
                "metrics": {"adx": round(current_adx, 2)}
            }

        # --- 2. TREND SIGNAL (MACD) ---
        macd = ta.trend.MACD(
            df['close'], 
            window_slow=self.slow_period, 
            window_fast=self.fast_period, 
            window_sign=self.signal_period
        )
        
        macd_line = macd.macd().iloc[-1]
        signal_line = macd.macd_signal().iloc[-1]
        hist = macd.macd_diff().iloc[-1]
        
        # Check Crossover (Current vs Previous) NOT strictly necessary if we are just checking state
        # But 'State' is better for daily trend following than strict crossover (re-entry)
        
        signal = "HOLD"
        reason = "Neutral"
        confidence = 0.0
        
        if macd_line > signal_line:
            signal = "BUY"
            reason = "MACD Bullish Trend"
            confidence = 0.8 + (0.1 if hist > 0 else 0) # Boost if histogram expanding
            
        elif macd_line < signal_line:
            signal = "SELL"
            reason = "MACD Bearish Trend"
            confidence = 0.8 + (0.1 if hist < 0 else 0)

        return {
            "signal": signal,
            "reason": reason,
            "confidence": confidence,
            "regime": regime,
            "metrics": {
                "adx": round(current_adx, 2),
                "macd": round(macd_line, 5),
                "signal": round(signal_line, 5),
                "hist": round(hist, 5)
            }
        }
