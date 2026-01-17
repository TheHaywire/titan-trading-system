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

    def get_scaling_multiplier(self, symbol, performance_metrics, account_info=None, active_positions=None):
        """
        Institutional Scaling Engine (v2.0)
        Dynamic Phase-Scaling:
        1. Winning Streak Boost (Hot Hand)
        2. Drawdown Defense (Cool Down)
        3. Scale-In (Double Down on Winners)
        """
        multiplier = 1.0
        
        # 1. Performance-Based Scaling (Historical)
        expectancy = performance_metrics.get('expectancy', 0)
        win_rate = performance_metrics.get('win_rate', 0.5)
        
        if expectancy > 500 and win_rate > 0.65:
            multiplier += 0.5 # A+ Symbol
            logger.info(f"💎 {symbol} is a Tier-1 Asset. Scaling up +0.5x")

        # 2. Account Equity Scaling (Drawdown Defense)
        if account_info:
            equity = account_info.get('equity', 1)
            balance = account_info.get('balance', 1)
            # Drawdown Defense (2% threshold)
            if equity < balance * 0.98:
                multiplier *= 0.7
                logger.warning(f"🛡️ Drawdown Defense active. Scaling down to 0.7x")
            # Growth Phase (5% threshold)
            elif equity > balance * 1.05:
                multiplier *= 1.2
                logger.info(f"📈 Growth Phase active. Scaling up to 1.2x")

        # 3. Winning Streak (Hot Hand)
        streak = performance_metrics.get('streak', 0)
        if streak >= 3:
            multiplier += 0.2
            logger.info(f"🔥 {symbol} on a {streak}-win streak! Scaling up +0.2x")

        # 4. Scale-In (Double Down on Winners)
        if active_positions:
            for pos in active_positions:
                if pos.symbol == symbol:
                    # If existing position is profitable (Risk managed), scale up the next one
                    if pos.profit > 0:
                        multiplier += 0.3
                        logger.info(f"🚀 Scaling IN (Double Down) on profitable {symbol} position.")
                        break

        # Final Cap
        return max(0.2, min(2.5, multiplier))
