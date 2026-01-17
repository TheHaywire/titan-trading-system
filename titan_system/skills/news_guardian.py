"""
News Guardian Skill
===================
Detects abnormal market behavior that suggests high-impact news.
Halts trading during 'Black Swan' moments.
"""

from .base import IntelligenceSkill
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from typing import Dict, Any

class NewsGuardianSkill(IntelligenceSkill):
    def __init__(self, volatility_threshold: float = 3.0):
        super().__init__(
            name="NewsGuardian",
            description="Protects capital during high-impact news via volatility proxy detection."
        )
        self.volatility_threshold = volatility_threshold  # Multiplier for ATR

    async def evaluate(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.active:
            return {'status': 'PASS', 'adjustment': 0, 'reason': 'Skill inactive'}

        symbol = context.get('symbol')
        if not symbol:
            return {'status': 'PASS', 'adjustment': 0, 'reason': 'No symbol provided'}

        # Fetch recent M5 data to check for sudden spikes
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 20)
        if rates is None or len(rates) < 14:
            return {'status': 'PASS', 'adjustment': 0, 'reason': 'Insufficient data for news detection'}

        df = pd.DataFrame(rates)
        df['range'] = df['high'] - df['low']
        
        # Calculate recent average range
        avg_range = df['range'].iloc[:-2].mean()
        current_range = df['range'].iloc[-1]
        
        # Detection logic
        if current_range > (avg_range * self.volatility_threshold):
            return {
                'status': 'BLOCK',
                'adjustment': -100,
                'reason': f"ABNORMAL VOLATILITY: Symbol {symbol} range ({current_range:.5f}) > {self.volatility_threshold}x average. NEWS DETECTED.",
                'metadata': {'current_range': current_range, 'avg_range': avg_range}
            }

        # Check for cumulative movement (trending news)
        move_3_bars = abs(df['close'].iloc[-1] - df['close'].iloc[-4])
        if move_3_bars > (avg_range * self.volatility_threshold * 1.5):
            return {
                'status': 'BLOCK',
                'adjustment': -80,
                'reason': f"IMPULSE DETECTED: 3-bar move ({move_3_bars:.5f}) suggests news breakthrough.",
                'metadata': {'move': move_3_bars}
            }

        return {
            'status': 'PASS',
            'adjustment': 0,
            'reason': 'Market volatility within normal parameters.',
            'metadata': {'volatility_ratio': current_range / avg_range if avg_range > 0 else 1}
        }
