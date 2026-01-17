"""
PORTFOLIO MANAGER - Phase 14
============================
Centralized risk management and position sizing engine.
Calculates optimal lots based on:
1. Kelly Criterion (Historical edge)
2. ATR Volatility (Market noise)
3. Asset Correlation (Portfolio overlap)
4. Global Risk Guards (Drawdown & Volatility spikes)
"""

import sys, os
import logging
import sqlite3
import json
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory import factory_config as cfg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PortfolioManager")

class PortfolioManager:
    def __init__(self, db_path: str = cfg.STRATEGY_DB):
        self.db_path = db_path
        self.risk_per_trade = cfg.DEFAULT_RISK_PER_TRADE
        self.max_correlation = cfg.MAX_CORRELATION_THRESHOLD
        
    def calculate_optimal_size(self, strategy_id: str, symbol: str, entry: float, sl: float) -> float:
        """
        Main entry point for calculating position size for a specific strategy/symbol.
        """
        if not mt5.initialize():
            logger.error("MT5 failed to initialize")
            return 0.0
            
        account = mt5.account_info()
        balance = account.balance
        
        # 1. Base Kelly Scaling
        kelly_mult = self._get_kelly_multiplier(strategy_id)
        
        # 2. Volatility Adjustment (ATR)
        vol_mult = self._get_volatility_multiplier(symbol)
        
        # 3. Correlation Adjustment
        corr_mult = self._get_correlation_multiplier(symbol)
        
        # 4. Global Risk Brake
        global_mult = self._get_global_risk_multiplier()
        
        # Combined Risk Percentage
        final_risk_pct = self.risk_per_trade * kelly_mult * vol_mult * corr_mult * global_mult
        
        # Cap absolute risk per trade (e.g., 2% max even if Kelly is higher)
        final_risk_pct = min(final_risk_pct, 0.02)
        
        # 5. Calculate Lots
        lots = self._calculate_lots(symbol, balance, final_risk_pct, entry, sl)
        
        logger.info(f"Sizing {symbol} for {strategy_id[:8]}: Risk={final_risk_pct:.2%}, Kelly={kelly_mult:.2f}x, Vol={vol_mult:.2f}x, Corr={corr_mult:.2f}x, Global={global_mult:.2f}x -> Lots={lots}")
        
        return lots

    def _get_kelly_multiplier(self, strategy_id: str) -> float:
        """Calculate multiplier based on Fractional Kelly Criterion."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Use backtest Sharpe as a proxy if live trades are few
            query = "SELECT bt_sharpe, live_trades, live_pnl FROM strategies WHERE id = ?"
            row = conn.execute(query, (strategy_id,)).fetchone()
            conn.close()
            
            if not row or row[0] is None:
                return 0.5 # Default to conservative half-risk
                
            sharpe = row[0]
            # Simple Kelly-like scaling: Higher Sharpe gets more weight
            # Normalized so Sharpe 1.5 = 1.0x risk
            mult = sharpe / 1.5
            
            # Cap the Kelly multiplier to avoid over-leveraging
            return max(0.5, min(mult, 1.5))
        except Exception as e:
            logger.error(f"Kelly calculation error: {e}")
            return 0.5

    def _get_volatility_multiplier(self, symbol: str) -> float:
        """Reduce size if current volatility is high compared to historical."""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 30)
        if rates is None or len(rates) < 14:
            return 1.0
            
        df = pd.DataFrame(rates)
        df['tr'] = np.maximum(df['high'] - df['low'], 
                             np.maximum(abs(df['high'] - df['close'].shift()), 
                                      abs(df['low'] - df['close'].shift())))
        
        current_atr = df['tr'].iloc[-1]
        avg_atr = df['tr'].rolling(14).mean().iloc[-1]
        
        ratio = current_atr / avg_atr
        if ratio > 1.5: return 0.5
        if ratio > 1.2: return 0.75
        return 1.0

    def _get_correlation_multiplier(self, symbol: str) -> float:
        """Reduce size if portfolio already has highly correlated exposure."""
        positions = mt5.positions_get()
        if not positions:
            return 1.0
            
        active_symbols = set([p.symbol for p in positions])
        if not active_symbols:
            return 1.0
            
        # Simplified: If symbol is already open, or a close cousin, reduce size
        # A more complex version would fetch 30d correlation matrix
        cousins = {
            "EURUSD": ["GBPUSD", "USDCHF"],
            "GBPUSD": ["EURUSD"],
            "GOLD": ["SILVER"],
            "US100": ["US30", "US500", "GER40"]
        }
        
        penalty = 1.0
        for active in active_symbols:
            if active == symbol:
                penalty *= 0.5 # Half size for same symbol entries
            elif symbol in cousins and active in cousins[symbol]:
                penalty *= 0.7 # 30% reduction for highly correlated pairs
                
        return max(0.3, penalty)

    def _get_global_risk_multiplier(self) -> float:
        """Global brake based on portfolio health."""
        acc = mt5.account_info()
        equity = acc.equity
        balance = acc.balance
        
        # Portfolio Drawdown Check
        if balance > 0:
            dd = (balance - equity) / balance
            if dd > 0.10: return 0.0 # HALT if 10% unrealized DD
            if dd > 0.05: return 0.5 # Half risk if 5% unrealized DD
            
        return 1.0

    def _calculate_lots(self, symbol, balance, risk_pct, entry, sl):
        """Standard position size calculation."""
        sl_dist = abs(entry - sl)
        if sl_dist == 0: return 0.0
        
        info = mt5.symbol_info(symbol)
        if not info: return 0.0
        
        risk_amount = balance * risk_pct
        
        # Simple point-based calculation for lots
        # This is a simplification, full calc should use info.trade_contract_size
        point = info.point
        sl_points = sl_dist / point
        
        if "JPY" in symbol:
            pip_value = 0.01 * info.trade_contract_size / 100
        else:
            pip_value = 0.0001 * info.trade_contract_size
            
        # Lots = Risk / (Points * Value_per_point)
        # We'll use MT5's order_calc_margin as a sanity check if needed
        # But for now, standard formula:
        ticker_value = info.trade_tick_value
        tick_size = info.trade_tick_size
        
        if ticker_value and tick_size:
            lots = risk_amount / (sl_dist / tick_size * ticker_value)
        else:
            # Fallback
            lots = risk_amount / (sl_points * (info.trade_contract_size * point))

        # Clamp to symbol limits
        lots = round(lots, 2)
        lots = max(info.volume_min, min(lots, info.volume_max))
        
        return lots

if __name__ == "__main__":
    pm = PortfolioManager()
    # Test calc
    sz = pm.calculate_optimal_size("dummy_id", "GOLD", 2600, 2580)
    print(f"Test Sizing: {sz} lots")
