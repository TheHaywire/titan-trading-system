"""
Titan Risk Management Engine
============================
Calculates dynamic position sizing based on equity risk and 
implements "Adding to Winners" (Pyramiding) logic.
"""

import math
import logging
import MetaTrader5 as mt5
from typing import Dict, Optional

logger = logging.getLogger("Titan.Risk")

class RiskManager:
    def __init__(self, execution_hub):
        self.execution = execution_hub
        self.risk_per_trade = 0.01  # Default 1% risk
        self.max_pyramid_levels = 3 # Max 3 units per symbol
        self.daily_loss_limit = 0.03 # 3% Daily Stop
        self.initial_daily_equity = self._get_starting_equity()
        
    def _get_starting_equity(self):
        acc = self.execution.get_account_info()
        return acc.get('equity', 0)

    def is_circuit_breaker_tripped(self) -> bool:
        """Institutional Safeguard: Checks if daily loss limit is hit."""
        acc = self.execution.get_account_info()
        current_equity = acc.get('equity', 0)
        
        if self.initial_daily_equity <= 0:
            self.initial_daily_equity = current_equity
            return False
            
        drawdown = (self.initial_daily_equity - current_equity) / self.initial_daily_equity
        if drawdown >= self.daily_loss_limit:
            logger.critical(f"🚨 CIRCUIT BREAKER TRIPPED: Daily loss limit hit ({drawdown*100:.2f}%)")
            return True
        return False
        
    def calculate_lot_size(self, symbol: str, risk_percent: float, sl_pips: float, win_rate: float = 0.5, rr_ratio: float = 2.0, hurst: float = 0.5) -> float:
        """
        Calculates lot size based on:
        1. Fixed Fractional Risk (Standard)
        2. Optionally adjusted by Kelly Criterion if win_rate/rr provided.
        3. Scaled by Hurst Exponent (H > 0.5 = Trending = more stickiness).
        """
        if not self.execution.connected:
            return 0.1 
            
        acc_info = self.execution.get_account_info()
        equity = acc_info.get('equity', 0)
        
        # Kelly Fraction = W - [(1-W)/R] where W is WinRate, R is RiskReward
        # Use Half-Kelly for safety
        kelly_fraction = max(0.01, (win_rate - ((1 - win_rate) / rr_ratio)) * 0.5)
        
        # Hurst Multiplier (Scale size up for trending, down for mean-reverting)
        # H=0.5 (Normal), H=0.6 (+20%), H=0.4 (-20%)
        hurst_mult = 1.0 + (hurst - 0.5) * 2.0
        hurst_mult = max(0.5, min(1.5, hurst_mult))
        
        # Use the smaller of fixed risk or kelly, then apply hurst mult
        effective_risk = min(risk_percent/100.0, kelly_fraction) * hurst_mult
        
        risk_amount = equity * effective_risk
        
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.1
            
        tick_value = symbol_info.trade_tick_value
        if tick_value <= 0 or sl_pips <= 0:
            return 0.1
            
        sl_points = sl_pips * 10 
        lots = risk_amount / (sl_points * tick_value)
        
        return self.execution.normalize_volume(symbol, lots)

    def can_add_to_winner(self, symbol: str, current_action: str) -> bool:
        """
        Logic for 'Adding to Winners' (Pyramiding).
        Criteria:
        1. Existing position must be in profit.
        2. Current position count < max_pyramid_levels.
        3. New direction matches existing direction.
        """
        positions = self.execution.get_positions()
        symbol_positions = [p for p in positions if p['symbol'] == symbol]
        
        if not symbol_positions:
            return True # Not adding, it's a new trade
            
        if len(symbol_positions) >= self.max_pyramid_levels:
            logger.info(f"🛡️ Max pyramid level reached for {symbol}.")
            return False
            
        # Check if latest position is in profit
        latest_pos = symbol_positions[-1]
        pnl = latest_pos['profit']
        
        # Check direction alignment
        pos_type = "BUY" if latest_pos['type'] == mt5.POSITION_TYPE_BUY else "SELL"
        
        if pos_type != current_action:
            logger.warning(f"⚠️ Scale-in rejected: Mismatch direction ({current_action} vs {pos_type})")
            return False
            
        if pnl <= 0:
            logger.info(f"⏳ Scale-in pending: Current position for {symbol} is not yet in profit.")
            return False
            
        logger.info(f"🚀 Adding to winner: {symbol} is profitable (+{pnl}). Scaling in...")
        return True
        
    def get_pyramid_risk_multiplier(self, level: int) -> float:
        """Aggressive scaling uses smaller sizes for subsequent units."""
        # Unit 1: 100%, Unit 2: 75%, Unit 3: 50%
        multipliers = {1: 1.0, 2: 0.75, 3: 0.5}
        return multipliers.get(level, 0.25)
