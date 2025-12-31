
import pandas as pd
import numpy as np
import ta
from titan_system.strategies.base import BaseStrategy
import logging

logger = logging.getLogger("Titan.Strategies.MeanReversion")

class MeanReversionStrategy(BaseStrategy):
    """
    Bollinger Band + RSI Mean Reversion Strategy.
    
    Logic:
    - Long: Price < Lower BB (2.5) AND RSI < 30.
    - Short: Price > Upper BB (2.5) AND RSI > 70.
    - Exit: Reaches Middle Band (SMA 20).
    """
    
    def __init__(self, config={}):
        super().__init__("MeanReversion", config)
        self.bb_period = config.get("bb_period", 20)
        self.bb_std = config.get("bb_std", 2.0)
        self.rsi_period = config.get("rsi_period", 14)
        self.rsi_overbought = config.get("rsi_overbought", 70)
        self.rsi_oversold = config.get("rsi_oversold", 30)

    def analyze(self, symbol: str, df: pd.DataFrame) -> dict:
        """
        Analyzes dataframe for Mean Reversion setups.
        """
        if df.empty or len(df) < 50:
            return None
            
        # 1. Calculate Indicators
        # Bollinger Bands
        indicator_bb = ta.volatility.BollingerBands(close=df["close"], window=self.bb_period, window_dev=self.bb_std)
        df['bb_upper'] = indicator_bb.bollinger_hband()
        df['bb_lower'] = indicator_bb.bollinger_lband()
        df['bb_mid'] = indicator_bb.bollinger_mavg()
        
        # RSI
        df['rsi'] = ta.momentum.rsi(df["close"], window=self.rsi_period)
        
        current = df.iloc[-1]
        
        signal = None
        
        # 2. Check Signals
        # SHORT
        if current['close'] > current['bb_upper'] and current['rsi'] > self.rsi_overbought:
            signal = {
                "signal": "SELL",
                "setup": "BB_OVERSHOOT_RSI_DIV",
                "stop_loss": current['high'] + (current['close'] * 0.002), # 0.2% above high
                "take_profit": current['bb_mid'], # Target Mean
                "confidence": 0.80,
                "metrics": {"std_dev": (current['bb_upper'] - current['bb_mid'])}
            }
            
        # LONG
        elif current['close'] < current['bb_lower'] and current['rsi'] < self.rsi_oversold:
            signal = {
                "signal": "BUY",
                "setup": "BB_UNDERSHOOT_RSI_DIV",
                "stop_loss": current['low'] - (current['close'] * 0.002), # 0.2% below low
                "take_profit": current['bb_mid'],
                "confidence": 0.80,
                "metrics": {"std_dev": (current['bb_mid'] - current['bb_lower'])}
            }
            
        return signal
