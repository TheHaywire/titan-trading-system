
from .base import BaseStrategy
import pandas as pd
import ta
import numpy as np

class DivergenceHunter(BaseStrategy):
    """
    Advanced Pattern Recognition Strategy.
    Detects RSI Divergences (Price vs Momentum disagreement).
    
    Logic:
    1. Identify local Peaks and Troughs in Price and RSI.
    2. Bullish Divergence: Price Lower Low + RSI Higher Low.
    3. Bearish Divergence: Price Higher High + RSI Lower High.
    4. Multi-Timeframe: Uses M15 for Signal, H1/H4 for Context.
    """
    
    def __init__(self, config=None):
        super().__init__("DivergenceHunter", config or {})
        self.rsi_period = 14
        self.lookback = 30 # How far back to check for the "previous" peak/trough
        
    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Expects a DF. For full power, the engine should pass a Dictionary of DFs {M5, M15, H1}.
        However, base class signature is (str, DF).
        We will assume 'df' is the PRIMARY trading timeframe (e.g. M15) for now.
        """
        if df is None or len(df) < 50:
             return {"signal": "HOLD", "reason": "No Data"}
             
        # 1. Calculate Indicators
        df['rsi'] = ta.momentum.rsi(df['close'], window=self.rsi_period)
        
        # 2. Find Peaks/Troughs (Local Extrema)
        # We define a peak if it's higher than neighbors
        n = 3 # 3 bars left/right
        
        df['min'] = df['low'].rolling(window=2*n+1, center=True).min() == df['low']
        df['max'] = df['high'].rolling(window=2*n+1, center=True).max() == df['high']
        
        curr = df.iloc[-1]
        
        # We need to find the LAST Confirmed Peak/Trough.
        # Note: Rolling with center=True introduces lookahead if we aren't careful, 
        # but for the "Last" completed peak it's fine (it happened n bars ago).
        # Actually in live streaming, we can't usage center=True easily without lag.
        # Pivot logic: High[i] > High[i-1]...High[i-n] AND High[i] > High[i+1]...
        # We will usage a simpler approach: Detect pivot N bars ago.
        
        # Let's verify if we have a POTENTIAL divergence forming NOW.
        # Price is making a new low, but RSI is NOT.
        
        # Scan last 20 bars
        window = df.iloc[-30:]
        
        # BULLISH DIVERGENCE CHECK
        # Current Price is near a Low
        recent_low = window['low'].min()
        recent_low_idx = window['low'].idxmin()
        
        # Price Low was very recent (last 3 bars) behavior
        if (window.index[-1] - recent_low_idx) > 5:
             # The low is old.
             return {"signal": "HOLD", "reason": "No recent low"}
             
        # Find the Previous Significant Low
        # Slice window BEFORE the recent low
        # e.g. lookback 60 bars
        long_window = df.iloc[-60:-5] # Exclude recent bars to find distinct previous trough
        prev_low = long_window['low'].min()
        prev_low_idx = long_window['low'].idxmin()
        
        if pd.isna(prev_low):
             return {"signal": "HOLD", "reason": "No history"}
        
        # Compare Price
        price_lower_low = recent_low < prev_low
        
        # Compare RSI
        # Get RSI at the moment of those Lows
        rsi_recent = df.loc[recent_low_idx, 'rsi']
        rsi_prev = df.loc[prev_low_idx, 'rsi']
        
        rsi_higher_low = rsi_recent > rsi_prev
        
        if price_lower_low and rsi_higher_low:
             # DIVERGENCE FOUND
             # Filter: RSI value should be somewhat low (e.g. < 40 or 50) to ensure oversold context
             if rsi_recent < 50:
                 return {
                     "signal": "BUY",
                     "reason": f"Bullish Divergence (Price LL, RSI HL)",
                     "confidence": 0.9,
                     "metrics": {"rsi1": rsi_prev, "rsi2": rsi_recent}
                 }

        # BEARISH DIVERGENCE CHECK
        recent_high = window['high'].max()
        recent_high_idx = window['high'].idxmin() # Wait, max
        recent_high_idx = window['high'].idxmax()
        
        if (window.index[-1] - recent_high_idx) > 5:
             pass # check failed
        else:
             prev_high = long_window['high'].max()
             prev_high_idx = long_window['high'].idxmax()
             
             price_higher_high = recent_high > prev_high
             
             rsi_recent = df.loc[recent_high_idx, 'rsi']
             rsi_prev = df.loc[prev_high_idx, 'rsi']
             
             rsi_lower_high = rsi_recent < rsi_prev
             
             if price_higher_high and rsi_lower_high:
                 if rsi_recent > 50:
                      return {
                         "signal": "SELL",
                         "reason": f"Bearish Divergence (Price HH, RSI LH)",
                         "confidence": 0.9,
                         "metrics": {"rsi1": rsi_prev, "rsi2": rsi_recent}
                     }
                     
        return {"signal": "HOLD", "reason": "No Divergence"}
