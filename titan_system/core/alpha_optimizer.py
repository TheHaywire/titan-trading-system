"""
Institutional Alpha Optimizer
Ensures the system is aligned with the most profitable logic for 
each market regime (Trend, Range, Volatility).
"""

import logging

logger = logging.getLogger("Titan.AlphaOptimizer")

class AlphaOptimizer:
    def __init__(self):
        # Explicit Regime-to-Strategy Mapping
        self.regime_map = {
            "TREND_STRONG": ["InstitutionalGold", "BookTechnical", "TrendSurfer"],
            "MEAN_REVERSION": ["MeanReversionStrategy", "MomentumScalper"],
            "HIGH_VOLATILITY": ["LiquidityHunter", "RegressionSurfer"],
            "LOW_VOLATILITY": ["HOLD"] # Conservation of capital
        }

    def determine_best_strategy(self, symbol, market_state):
        """
        Consults the 'Brain' output and selects the optimal logic.
        """
        categories = market_state.get('categories', {})
        regime = "NEUTRAL"
        
        # 1. Identify Primary Regime
        trend_data = categories.get('Trend Following', {})
        mr_data = categories.get('Mean Reversion', {})
        vol_data = categories.get('Volatility', {})
        
        if trend_data.get('score', 0) > 70:
            regime = "TREND_STRONG"
        elif mr_data.get('score', 0) > 70:
            regime = "MEAN_REVERSION"
        elif vol_data.get('label') == "HIGH":
            regime = "HIGH_VOLATILITY"
        else:
            regime = "LOW_VOLATILITY"
            
        # 2. Assign Strategy based on Regime and Symbol traits
        recommended = self.regime_map.get(regime, ["HOLD"])
        
        # Log the decision for "Glass Box" transparency
        logger.info(f"🔮 Alpha Optimizer [{symbol}]: Regime={regime} -> Recommendation={recommended[0]}")
        
        # Symbol-specific overrides (Institutional Bias)
        if symbol in ["GOLD", "XAUUSD"]:
            return "InstitutionalGold" if regime != "LOW_VOLATILITY" else "HOLD"
            
        if symbol in ["BTCUSD", "ETHUSD", "US500", "NAS100"]:
            # Fat Tails respond best to Trend Following or Volatility logic
            return recommended[0] if regime in ["TREND_STRONG", "HIGH_VOLATILITY"] else "HOLD"

        return recommended[0]

    def get_scaling_multiplier(self, symbol, performance_metrics):
        """
        Growth logic: Scales winners aggressively, caps losers.
        """
        # Logic: If expectancy > $200 and win rate > 60%, scale 1.5x
        if performance_metrics.get('expectancy', 0) > 200:
            return 1.5
        return 1.0
