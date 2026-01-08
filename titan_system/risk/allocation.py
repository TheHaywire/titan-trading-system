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
        
        # 3. Portfolio Constraint (Dynamic Correlation Check)
        # Use actual correlation matrix instead of string matching
        positions = mt5.positions_get()
        if positions:
            existing_symbols = [p.symbol for p in positions]
            if existing_symbols and symbol not in existing_symbols:
                # Calculate actual correlation matrix
                corr_data = self.quant.calculate_correlation_matrix(
                    existing_symbols + [symbol], 
                    lookback=100
                )
                
                if corr_data and 'matrix' in corr_data:
                    corr_matrix = corr_data['matrix']
                    
                    # Check if new symbol is highly correlated with any existing position
                    for existing_sym in existing_symbols:
                        if symbol in corr_matrix and existing_sym in corr_matrix.get(symbol, {}):
                            correlation = abs(corr_matrix[symbol].get(existing_sym, 0))
                            
                            if correlation > 0.7:
                                reduction = 1.0 - (correlation - 0.5)  # Higher corr = bigger reduction
                                reduction = max(0.3, min(1.0, reduction))  # Cap between 30-100%
                                logger.info(f"[CORR] {symbol} <-> {existing_sym}: {correlation:.2f}. Reducing allocation to {reduction*100:.0f}%")
                                raw_lots *= reduction
                                break
                            elif correlation > 0.5:
                                logger.info(f"[CORR] {symbol} <-> {existing_sym}: {correlation:.2f} (moderate, no reduction)")
                else:
                    # Fallback to simple check if correlation calc fails
                    for p in positions:
                        if p.symbol[:3] == symbol[:3] or p.symbol[3:6] == symbol[3:6]:
                            logger.info(f"[CORR] Currency match with {p.symbol}. Reducing {symbol} by 50%.")
                            raw_lots *= 0.5
                            break

        # 4. VaR Constraint (Hard Limit)
        # Check if this new position pushes portfolio VaR > Max Exposure
        if positions:
            current_var_data = self.quant.calculate_var(positions)
            current_var_pct = current_var_data.get('var_percentage', 0) / 100
            
            # Estimate new position's contribution to VaR
            # If already near max, scale down
            if current_var_pct > self.max_total_exposure * 0.8:  # 80% of limit
                remaining_budget = self.max_total_exposure - current_var_pct
                scale_factor = remaining_budget / (self.max_total_exposure * 0.2)  # Remaining share of 20%
                scale_factor = max(0.25, min(1.0, scale_factor))  # Floor at 25%
                logger.info(f"[VaR] Portfolio at {current_var_pct*100:.1f}% VaR. Scaling new position to {scale_factor*100:.0f}%")
                raw_lots *= scale_factor
        
        # 5. Institutional Hard Caps
        normalized_lots = self._normalize_lots(symbol, raw_lots)
        
        logger.info(f"[ALLOC] {symbol} | Confidence: {signal_confidence:.2f} | Result: {normalized_lots} Lots")
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
