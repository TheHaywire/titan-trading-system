
import pandas as pd
import numpy as np
from titan_system.strategies.base import BaseStrategy
import logging

logger = logging.getLogger("Titan.Strategies.LiquidityHunter")

class LiquidityHunterStrategy(BaseStrategy):
    """
    The 'Sniper'. Trades pure price action stop hunts (Liquidity Sweeps).
    
    Logic:
    1. Identify Swing Highs/Lows (Fractals) over last N candles.
    2. Wait for price to BREAK a level but CLOSE back inside (The 'Fakeout').
    3. Enter in opposite direction of the break.
    """
    
    def __init__(self, config={}):
        super().__init__("LiquidityHunter", config)
        self.lookback = 20 # Swing detection
        self.min_sweep_pips = 1.0 # Min pips to clean stop losses
        self.max_sweep_pips = 15.0 # Max pips (if more, it's a real breakout)

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Analyzes M5/M15 data for Sweep & Reclaim setups.
        """
        if df.empty or len(df) < 50:
            return None
            
        current_candle = df.iloc[-1]
        prev_candle = df.iloc[-2]
        
        # 1. Identify previous Key Levels (Swing Highs/Lows)
        # Simplify: Use max/min of last 20 candles (excluding current/prev)
        window = df.iloc[-22:-2] 
        recent_high = window['high'].max()
        recent_low = window['low'].min()
        
        signal = None
        
        # 2. Check for BEARISH SWEEP (Bull Trap)
        # Price went ABOVE high, but Closed BELOW high
        if prev_candle['high'] > recent_high and prev_candle['close'] < recent_high:
            sweep_size = (prev_candle['high'] - recent_high) * 10 # Approx pips for Gold? (Need strict pip calc)
            # Logic: We are reclaiming the range
            signal = {
                "signal": "SELL",
                "setup": "BEARISH_SWEEP",
                "stop_loss": prev_candle['high'] + 0.5, # Slightly above wick
                "take_profit": recent_low, # Target opposing liquidity
                "confidence": 0.85
            }
            
        # 3. Check for BULLISH SWEEP (Bear Trap)
        # Price went BELOW low, but Closed ABOVE low
        elif prev_candle['low'] < recent_low and prev_candle['close'] > recent_low:
            # Logic: Reclaiming the range
            signal = {
                "signal": "BUY",
                "setup": "BULLISH_SWEEP",
                "stop_loss": prev_candle['low'] - 0.5, # Slightly below wick
                "take_profit": recent_high, # Target opposing liquidity
                "confidence": 0.85
            }
            
        return signal
