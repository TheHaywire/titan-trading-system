"""
Monte Carlo Strategy Validator
==============================
Institutional-grade Monte Carlo simulation for strategy validation.
Auto-throttles strategies with high probability of ruin.
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional

logger = logging.getLogger("Titan.MonteCarlo")


@dataclass
class MonteCarloResult:
    """Results from a Monte Carlo simulation."""
    strategy_name: str
    simulations: int
    median_return: float
    mean_return: float
    std_return: float
    percentile_5: float   # Worst 5%
    percentile_95: float  # Best 5%
    probability_of_profit: float
    probability_of_ruin: float  # P(drawdown > threshold)
    max_drawdown_median: float
    recommendation: str  # DEPLOY, THROTTLE, REJECT
    throttle_factor: float  # 1.0 = full size, 0.5 = half size, etc.


class MonteCarloValidator:
    """
    Monte Carlo simulation engine for strategy validation.
    Implements institutional "Probability of Ruin" checks.
    """
    
    def __init__(self, 
                 n_simulations: int = 10000,
                 ruin_threshold: float = 0.20,  # 20% drawdown = ruin
                 max_ruin_probability: float = 0.02):  # 2% max acceptable
        """
        Args:
            n_simulations: Number of Monte Carlo trials
            ruin_threshold: Drawdown percentage that defines "ruin"
            max_ruin_probability: Maximum acceptable P(Ruin) for deployment
        """
        self.n_simulations = n_simulations
        self.ruin_threshold = ruin_threshold
        self.max_ruin_probability = max_ruin_probability
    
    def simulate_from_trades(self, 
                              trade_returns: List[float],
                              strategy_name: str = "Unknown") -> MonteCarloResult:
        """
        Run Monte Carlo simulation by resampling trade returns (R-multiples).
        
        Args:
            trade_returns: List of R-multiple returns (e.g., [2.0, -1.0, 1.5, -1.0, ...])
            strategy_name: Name for logging
            
        Returns:
            MonteCarloResult with recommendations
        """
        if len(trade_returns) < 5:
            logger.warning(f"[MC] {strategy_name}: Insufficient trades ({len(trade_returns)}) for simulation")
            return MonteCarloResult(
                strategy_name=strategy_name,
                simulations=0,
                median_return=0,
                mean_return=0,
                std_return=0,
                percentile_5=0,
                percentile_95=0,
                probability_of_profit=0,
                probability_of_ruin=1.0,
                max_drawdown_median=1.0,
                recommendation="REJECT",
                throttle_factor=0.0
            )
        
        returns = np.array(trade_returns)
        n_trades = len(returns)
        
        # Run simulations
        final_returns = []
        max_drawdowns = []
        
        for _ in range(self.n_simulations):
            # Bootstrap resample (with replacement)
            sample = np.random.choice(returns, size=n_trades, replace=True)
            
            # Calculate cumulative returns
            equity_curve = np.cumsum(sample)
            
            # Calculate max drawdown
            running_max = np.maximum.accumulate(equity_curve)
            drawdowns = (running_max - equity_curve)
            # Normalize by starting capital (assume 100 units of risk capital)
            max_dd = np.max(drawdowns) / 100.0  # As percentage
            
            final_returns.append(np.sum(sample))
            max_drawdowns.append(max_dd)
        
        final_returns = np.array(final_returns)
        max_drawdowns = np.array(max_drawdowns)
        
        # Calculate statistics
        median_return = float(np.median(final_returns))
        mean_return = float(np.mean(final_returns))
        std_return = float(np.std(final_returns))
        percentile_5 = float(np.percentile(final_returns, 5))
        percentile_95 = float(np.percentile(final_returns, 95))
        
        prob_profit = float(np.mean(final_returns > 0))
        prob_ruin = float(np.mean(max_drawdowns > self.ruin_threshold))
        max_dd_median = float(np.median(max_drawdowns))
        
        # Determine recommendation
        recommendation, throttle = self._get_recommendation(
            prob_ruin, prob_profit, median_return
        )
        
        result = MonteCarloResult(
            strategy_name=strategy_name,
            simulations=self.n_simulations,
            median_return=median_return,
            mean_return=mean_return,
            std_return=std_return,
            percentile_5=percentile_5,
            percentile_95=percentile_95,
            probability_of_profit=prob_profit,
            probability_of_ruin=prob_ruin,
            max_drawdown_median=max_dd_median,
            recommendation=recommendation,
            throttle_factor=throttle
        )
        
        logger.info(f"[MC] {strategy_name}: P(Profit)={prob_profit*100:.1f}%, "
                   f"P(Ruin)={prob_ruin*100:.2f}%, Median={median_return:.2f}R -> {recommendation}")
        
        return result
    
    def _get_recommendation(self, 
                            prob_ruin: float, 
                            prob_profit: float,
                            median_return: float) -> tuple:
        """
        Determine deployment recommendation based on simulation results.
        
        Returns:
            (recommendation: str, throttle_factor: float)
        """
        # REJECT: High probability of ruin
        if prob_ruin > self.max_ruin_probability * 5:  # 5x threshold
            return "REJECT", 0.0
        
        # REJECT: Negative median return
        if median_return < 0:
            return "REJECT", 0.0
        
        # REJECT: Low probability of profit
        if prob_profit < 0.50:
            return "REJECT", 0.0
        
        # THROTTLE: Moderate ruin risk
        if prob_ruin > self.max_ruin_probability:
            # Scale throttle: higher ruin = lower throttle
            throttle = 1.0 - (prob_ruin / (self.max_ruin_probability * 5))
            throttle = max(0.25, min(0.75, throttle))
            return "THROTTLE", throttle
        
        # DEPLOY: All checks passed
        if prob_profit > 0.60 and median_return > 0:
            return "DEPLOY", 1.0
        
        # CAUTIOUS DEPLOY
        return "DEPLOY", 0.8
    
    def validate_backtest_result(self, 
                                  trades: List[Dict],
                                  strategy_name: str = "Unknown") -> MonteCarloResult:
        """
        Convenience method to validate a backtest result.
        Expects trades with 'pnl_r' or 'profit' keys.
        """
        if not trades:
            return self.simulate_from_trades([], strategy_name)
        
        # Extract R-multiples (or raw profits if R not available)
        returns = []
        for t in trades:
            if 'pnl_r' in t:
                returns.append(t['pnl_r'])
            elif hasattr(t, 'pnl_r'):
                returns.append(t.pnl_r)
            elif 'profit' in t:
                # Normalize to R-multiple (assume 1R = average loss)
                returns.append(t['profit'])
            elif hasattr(t, 'profit'):
                returns.append(t.profit)
        
        return self.simulate_from_trades(returns, strategy_name)


# Convenience singleton for quick access
_default_validator = None

def get_validator() -> MonteCarloValidator:
    """Get default Monte Carlo validator instance."""
    global _default_validator
    if _default_validator is None:
        _default_validator = MonteCarloValidator()
    return _default_validator


def quick_validate(trade_returns: List[float], name: str = "Strategy") -> Dict:
    """
    Quick Monte Carlo validation for a list of trade returns.
    
    Returns:
        Dict with key metrics and recommendation
    """
    validator = get_validator()
    result = validator.simulate_from_trades(trade_returns, name)
    
    return {
        "strategy": result.strategy_name,
        "probability_of_profit": f"{result.probability_of_profit*100:.1f}%",
        "probability_of_ruin": f"{result.probability_of_ruin*100:.2f}%",
        "median_return": f"{result.median_return:.2f}R",
        "worst_5pct": f"{result.percentile_5:.2f}R",
        "best_5pct": f"{result.percentile_95:.2f}R",
        "recommendation": result.recommendation,
        "throttle_factor": result.throttle_factor
    }


if __name__ == "__main__":
    # Test with sample trades
    sample_trades = [
        2.0, -1.0, 1.5, -1.0, 3.0, -1.0, -1.0, 2.5, 1.0, -1.0,
        1.5, -1.0, 2.0, -1.0, 1.0, 2.0, -1.0, -1.0, 3.5, -1.0
    ]
    
    print("Monte Carlo Strategy Validator Test")
    print("=" * 50)
    
    result = quick_validate(sample_trades, "Test Strategy")
    
    for k, v in result.items():
        print(f"  {k}: {v}")
