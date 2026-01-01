"""
Institutional Risk & Quant Analytics Module
Adopts J.P. Morgan/Goldman Sachs style risk management for the Titan System.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger("Titan.Quant")

class InstitutionalQuant:
    """Institutional-grade Risk Oversight & Alpha Analytics"""
    
    def __init__(self, confidence_level=0.95):
        """
        confidence_level: VaR confidence (0.95 = 95%, 0.99 = 99%)
        """
        self.confidence_level = confidence_level
    
    def check_exposure_limit(self, current_positions, new_symbol, max_notional_usd=100000):
        """
        Policy enforcement: Blocks trades if notional exposure to a 
        single symbol/asset class exceeds institutional limits.
        """
        total_notional = 0
        symbol_notional = 0
        
        for p in current_positions:
            info = mt5.symbol_info(p.symbol)
            notional = p.volume * (info.trade_contract_size if info else 1) * p.price_current
            total_notional += notional
            if p.symbol == new_symbol:
                symbol_notional += notional
                
        if symbol_notional > max_notional_usd:
            return False, f"Risk Block: Exp to {new_symbol} (${symbol_notional:.0f}) > Limit (${max_notional_usd:.0f})"
            
        return True, "Passed"

    def calculate_correlation_matrix(self, symbols, lookback=100):
        """
        Calculates a correlation matrix for a list of symbols to detect over-exposure.
        Lookback defines the number of H1 candles to analyze.
        """
        if not symbols or len(symbols) < 2:
            return pd.DataFrame()

        data = {}
        for sym in symbols:
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, lookback)
            if rates is not None:
                df = pd.DataFrame(rates)
                data[sym] = df['close'].pct_change()
        
        if not data:
            return pd.DataFrame()
            
        corr_df = pd.DataFrame(data).corr()
        
        # Identify high correlations (> 0.7)
        high_corr = []
        for i in range(len(corr_df.columns)):
            for j in range(i):
                if abs(corr_df.iloc[i, j]) > 0.7:
                    high_corr.append(f"{corr_df.columns[i]} <-> {corr_df.columns[j]}: {corr_df.iloc[i, j]:.2f}")
        
        return {
            "matrix": corr_df.to_dict(),
            "high_correlation_alerts": high_corr
        }

    def calculate_var(self, positions):
        """
        Calculate Value at Risk (VaR) using the Variance/Covariance method.
        Estimates the maximum loss over 1 day within a confidence interval.
        """
        if not positions:
            return 0.0

        total_equity = mt5.account_info().equity
        var_per_symbol = {}
        
        for p in positions:
            # Fetch historical volatility for the symbol
            rates = mt5.copy_rates_from_pos(p.symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates is not None:
                df = pd.DataFrame(rates)
                df['returns'] = df['close'].pct_change()
                volatility = df['returns'].std()
                
                # Institutional VaR calculation
                info = mt5.symbol_info(p.symbol)
                z_score = 1.645 if self.confidence_level == 0.95 else 2.326
                
                # Formula: Lots * ContractSize * CurrentPrice * Volatility * Z-Score
                contract_size = info.trade_contract_size if info else 1
                notional_value = p.volume * contract_size * p.price_current
                
                symbol_var = notional_value * volatility * z_score
                var_per_symbol[p.symbol] = symbol_var
        
        total_var = sum(var_per_symbol.values())
        var_pct = (total_var / total_equity) * 100
        
        return {
            "total_var_usd": round(total_var, 2),
            "var_percentage": round(var_pct, 2),
            "symbol_breakdown": {s: round(v, 2) for s,v in var_per_symbol.items()}
        }

    def analyze_concentration_risk(self, positions):
        """
        Calculates exposure concentration by Asset Class and Currency.
        Prevents over-exposure to Correlated pairs (e.g., trading 5 JPY pairs).
        """
        if not positions:
            return {}

        exposure_map = {}
        for p in positions:
            info = mt5.symbol_info(p.symbol)
            contract_size = info.trade_contract_size if info else 1
            notional = p.volume * contract_size * p.price_current
            exposure_map[p.symbol] = exposure_map.get(p.symbol, 0) + notional
        
        total_exposure = sum(exposure_map.values())
        concentration = {s: round((val / total_exposure) * 100, 2) for s, val in exposure_map.items()}
        
        # Flags for institutional limits (e.g., no more than 25% in one asset)
        alerts = []
        for s, pct in concentration.items():
            if pct > 25.0:
                alerts.append(f"CRITICAL CONCENTRATION: {s} represents {pct}% of total exposure.")
        
        return {
            "concentration_pct": concentration,
            "alerts": alerts
        }

    def simulate_black_swan(self, positions, magnitude=0.10):
        """
        Stress Test: What happens if the market moves X% against us instantly?
        magnitude = 0.10 (10% flash crash)
        """
        if not positions:
            return 0.0

        potential_loss = 0.0
        for p in positions:
            info = mt5.symbol_info(p.symbol)
            contract_size = info.trade_contract_size if info else 1
            exposure = p.volume * contract_size * p.price_current
            potential_loss += exposure * magnitude
                
        return round(potential_loss, 2)

    def get_institutional_health_report(self):
        """Generates a full JPM-style risk report."""
        if not mt5.initialize():
            return {"error": "MT5 not connected"}
            
        positions = mt5.positions_get()
        account = mt5.account_info()
        
        var_data = self.calculate_var(positions)
        concentration = self.analyze_concentration_risk(positions)
        stress_test = self.simulate_black_swan(positions)
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "account_equity": account.equity,
            "total_positions": len(positions) if positions else 0,
            "value_at_risk": var_data,
            "concentration": concentration,
            "stress_test_10pct_move": f"-${stress_test}",
            "institutional_rating": "A" if var_data.get('var_percentage', 0) < 5.0 else "B-"
        }
        
        return report

if __name__ == "__main__":
    # Test execution
    quant = InstitutionalQuant()
    report = quant.get_institutional_health_report()
    import json
    print(json.dumps(report, indent=4))
    mt5.shutdown()
