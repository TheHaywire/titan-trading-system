
import pandas as pd
import ta
import logging
from titan_system.strategies.base import BaseStrategy

logger = logging.getLogger("Titan.Strategy.GoldBreakout")

class LiveGoldBreakout(BaseStrategy):
    """
    REGIME-LIMITED BREAKOUT (Optimized for GOLD)
    
    Configuration (Deep Optimization):
    - Entry Lookback: 35 Days
    - Exit Lookback: 10 Days
    - Regime Filter: Volatility Expansion (ATR > SMA20_ATR)
    
    Logic:
    - GOLD trends best when volatility expands.
    - We use Donchian Channels for entry/exit.
    - We FILTER OUT breakouts that occur during low-volatility squeezes (Fakeouts).
    """
    
    def __init__(self, config=None):
        if config is None: config = {}
        # Default to Optimized Parameters
        config.setdefault('entry_period', 35)
        config.setdefault('exit_period', 10)
        config.setdefault('risk_mult', 1.0)
        
        super().__init__("GoldBreakout_Donchian", config)
        
        self.entry_period = config['entry_period']
        self.exit_period = config['exit_period']
        self.risk_mult = config['risk_mult']

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Analyze logic:
        1. Check Data Sufficiency
        2. Calculate Volatility Regime (Expansion)
        3. Determine Breakout Levels
        """
        min_bars = self.entry_period + 30 
        if df is None or len(df) < min_bars:
            return {"signal": "HOLD", "reason": "Insufficient Data"}

        # --- 1. REGIME FILTER (Volatility Expansion) ---
        # Gold moves fast. We want to be in "Fast" markets.
        atr_ind = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14)
        atr = atr_ind.average_true_range()
        sma_atr = atr.rolling(20).mean()
        
        current_atr = atr.iloc[-1]
        current_sma_atr = sma_atr.iloc[-1]
        
        is_expanding = current_atr > current_sma_atr
        
        # --- 2. DONCHIAN CHANNELS ---
        # Shift 1 to use "Previous N Days" High (so we don't lookahead or trade on current bar close only)
        # Actually for LIVE trading, we look at the 'Level' to beat.
        
        upper = df['high'].rolling(self.entry_period).max().shift(1).iloc[-1]
        lower = df['low'].rolling(self.exit_period).min().shift(1).iloc[-1]
        
        close = df['close'].iloc[-1]
        prev_close = df['close'].iloc[-2]
        
        signal = "HOLD"
        reason = "Neutral"
        confidence = 0.0
        
        # LOGIC:
        if is_expanding:
            if close > upper and prev_close <= upper: 
                # Fresh Breakout today
                signal = "BUY"
                reason = "Volatility-Backed Breakout (New High)"
                confidence = 0.9 * self.risk_mult
                
            elif close < lower:
                # Exit Signal (Trend Ended)
                signal = "SELL" # Or CLOSE if we have position logic
                reason = "Trend Correction (Hit 10d Low)"
                confidence = 1.0
        else:
            # Volatility Crunch -> Beware of Fakeouts
            # But if we are ALREADY in a trade, we hold. Strategy analyze() returns NEW entry signals.
            # To handle exits, we should still respect the Lower Band even in chop to protect capital.
             if close < lower:
                signal = "SELL"
                reason = "Protective Exit (Hit 10d Low)"
                confidence = 1.0
             else:
                reason = "Volatility Squeeze (Ignored Breakout)"

        return {
            "signal": signal,
            "reason": reason,
            "confidence": confidence,
            "regime": "EXPANDING" if is_expanding else "SQUEEZE",
            "metrics": {
                "atr": round(current_atr, 2),
                "upper_breakout": round(upper, 2),
                "lower_exit": round(lower, 2)
            }
        }
