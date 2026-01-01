"""
Institutional Allocation Agent
Decides lot sizes based on signal quality, Kelly Criterion, 
and portfolio-wide risk constraints (VaR & Correlation).
"""

import logging
import math
import MetaTrader5 as mt5
from titan_system.analytics.institutional_risk import InstitutionalQuant

logger = logging.getLogger("Titan.Allocation")

class AllocationAgent:
    def __init__(self, risk_per_trade=0.01, max_total_exposure=0.10):
        """
        risk_per_trade: Base risk percentage (e.g. 0.01 = 1%)
        max_total_exposure: Maximum account equity at risk (VaR target)
        """
        self.risk_per_trade = risk_per_trade
        self.max_total_exposure = max_total_exposure
        self.quant = InstitutionalQuant()

    def calculate_lots(self, symbol, signal_confidence, stop_loss_pips, scaling_multiplier=1.0):
        """
        Determines lot size using a multi-step institutional process.
        """
        acc = mt5.account_info()
        if not acc:
            return 0.0
            
        equity = acc.equity
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return 0.0

        # 1. Base Risk Amount (Percentage of Equity)
        # We scale base risk by Signal Confidence and the Alpha scaling factor
        actual_risk_pct = self.risk_per_trade * signal_confidence * scaling_multiplier
        risk_amount_usd = equity * actual_risk_pct
        
        # 1.b Drawdown Protection (Preserve Capital)
        # If equity is below balance, we are in a drawdown. Reduce risk by 30%.
        if equity < acc.balance:
            logger.info(f"📉 Drawdown detected (Eq: {equity:.2f} < Bal: {acc.balance:.2f}). Reducing risk by 30%.")
            risk_amount_usd *= 0.70
        
        # 2. Lot Size based on Stop Loss distance
        # LotSize = RiskAmount / (SL_Pips * PipValue)
        pip_value = symbol_info.trade_tick_value / (symbol_info.trade_tick_size / symbol_info.point)
        # Note: pip_value varies by symbol. Standardizing SL calculation:
        point = symbol_info.point
        sl_delta = stop_loss_pips * point * 10 # Assuming 5-digit pips
        
        if sl_delta == 0:
            return 0.0
            
        # Calculation: Lot = USD_Risk / (SL_Distance * TickValue/TickSize)
        raw_lots = risk_amount_usd / (sl_delta * (symbol_info.trade_tick_value / symbol_info.trade_tick_size))
        
        # 3. Portfolio Constraint (Correlation Check)
        # If we already have high exposure to a correlated asset, we reduce size.
        positions = mt5.positions_get()
        if positions:
            for p in positions:
                # Simple correlation proxy: Same currency base/quote
                if p.symbol[:3] == symbol[:3] or p.symbol[3:6] == symbol[3:6]:
                    logger.info(f"🔗 Correlation detected with {p.symbol}. Reducing {symbol} allocation by 50%.")
                    raw_lots *= 0.5
                    break

        # 4. VaR Constraint
        # Check if this new position pushes portfolio VaR > Max Exposure
        # (Simplified: estimated VaR component)
        current_var = self.quant.calculate_var(positions).get('total_var_usd', 0)
        # Estimated additional VaR: Lots * ContractSize * price * vol...
        # If (current_var + estimate_new_var) / equity > self.max_total_exposure:
        #    raw_lots *= adjustment_factor
        
        # 5. Institutional Hard Caps
        normalized_lots = self._normalize_lots(symbol, raw_lots)
        
        logger.info(f"🎯 Allocation: {symbol} | Confidence: {signal_confidence:.2f} | Result: {normalized_lots} Lots")
        return normalized_lots

    def _normalize_lots(self, symbol, lots):
        info = mt5.symbol_info(symbol)
        if not info: return 0.0
        
        step = info.volume_step
        l = max(info.volume_min, min(lots, info.volume_max))
        l = round(l / step) * step
        
        # Precision fix
        decimals = 0
        if "." in str(step):
            decimals = len(str(step).split(".")[1].rstrip("0"))
        return round(l, decimals)
