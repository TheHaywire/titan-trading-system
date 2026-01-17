"""
STRATEGY SCORER - Multi-Dimensional Strategy Evaluation
=======================================================
Scores strategies across multiple dimensions to identify the best candidates
for deployment while ensuring portfolio diversification.

Scoring Dimensions:
1. Risk-Adjusted Returns (40 points): Sharpe, Calmar
2. Consistency (30 points): Win Rate, Profit Factor
3. Robustness (20 points): OOS, Monte Carlo, Walk-Forward
4. Trade Frequency (10 points): Not too many, not too few

Penalties:
- High correlation with existing strategies (-20 points)
- Insufficient trades (-10 points)
- Overtrading (-10 points)
"""

import numpy as np
from typing import Dict, List, Optional
import logging

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from titan_system.factory import factory_config as cfg

logger = logging.getLogger("Factory.Scorer")


class StrategyScorer:
    """
    Multi-dimensional strategy evaluation system.
    Produces a 0-100 score indicating deployment worthiness.
    """
    
    def __init__(self):
        """Initialize scorer with default weights."""
        self.weights = {
            'risk_adjusted': 0.40,
            'consistency': 0.30,
            'robustness': 0.20,
            'trade_frequency': 0.10
        }
    
    def score_strategy(self, 
                      backtest_metrics: Dict,
                      robustness_results: Dict = None,
                      deployed_strategies: List[Dict] = None) -> Dict:
        """
        Score a strategy across all dimensions.
        
        Args:
            backtest_metrics: Results from backtest
                {
                    'sharpe': 1.85,
                    'calmar': 2.1,
                    'win_rate': 0.58,
                    'profit_factor': 2.3,
                    'total_trades': 145,
                    'max_drawdown': 0.12
                }
            robustness_results: Optional robustness test results
            deployed_strategies: List of currently deployed strategies (for correlation check)
        
        Returns:
            {
                'total_score': 75.5,
                'breakdown': {...},
                'rank': 'A',  # A, B, C, D, F
                'recommendation': 'DEPLOY' | 'PAPER' | 'REJECT'
            }
        """
        logger.info("Scoring strategy...")
        
        score = 0
        breakdown = {}
        
        # 1. Risk-Adjusted Returns (40 points max)
        risk_score = self._score_risk_adjusted(backtest_metrics)
        score += risk_score * self.weights['risk_adjusted'] * 100
        breakdown['risk_adjusted'] = risk_score * 100
        
        # 2. Consistency (30 points max)
        consistency_score = self._score_consistency(backtest_metrics)
        score += consistency_score * self.weights['consistency'] * 100
        breakdown['consistency'] = consistency_score * 100
        
        # 3. Robustness (20 points max)
        robustness_score = self._score_robustness(robustness_results)
        score += robustness_score * self.weights['robustness'] * 100
        breakdown['robustness'] = robustness_score * 100
        
        # 4. Trade Frequency (10 points max)
        frequency_score = self._score_trade_frequency(backtest_metrics)
        score += frequency_score * self.weights['trade_frequency'] * 100
        breakdown['trade_frequency'] = frequency_score * 100
        
        # 5. Correlation Penalty
        correlation_penalty = 0
        if deployed_strategies:
            correlation_penalty = self._calculate_correlation_penalty(
                backtest_metrics, deployed_strategies
            )
            score -= correlation_penalty
            breakdown['correlation_penalty'] = -correlation_penalty
        
        # Cap score at 100
        total_score = min(max(score, 0), 100)
        
        # Determine rank and recommendation
        rank = self._get_rank(total_score)
        recommendation = self._get_recommendation(total_score, backtest_metrics)
        
        result = {
            'total_score': total_score,
            'breakdown': breakdown,
            'rank': rank,
            'recommendation': recommendation,
            'passed_threshold': total_score >= 75  # Need 75+ to deploy
        }
        
        logger.info(f"  Total Score: {total_score:.1f}/100 (Rank: {rank})")
        logger.info(f"  Recommendation: {recommendation}")
        
        return result
    
    # ==================== SCORING DIMENSIONS ====================
    
    def _score_risk_adjusted(self, metrics: Dict) -> float:
        """
        Score risk-adjusted returns (0.0-1.0).
        
        Breakdown:
        - Sharpe Ratio (50%)
        - Calmar Ratio (50%)
        """
        sharpe = metrics.get('sharpe', 0)
        calmar = metrics.get('calmar', 0)
        
        # Sharpe scoring (50% of risk score)
        if sharpe >= 2.0:
            sharpe_score = 1.0
        elif sharpe >= 1.5:
            sharpe_score = 0.8
        elif sharpe >= 1.0:
            sharpe_score = 0.5
        elif sharpe >= 0.5:
            sharpe_score = 0.2
        else:
            sharpe_score = 0
        
        # Calmar scoring (50% of risk score)
        if calmar >= 3.0:
            calmar_score = 1.0
        elif calmar >= 2.0:
            calmar_score = 0.8
        elif calmar >= 1.0:
            calmar_score = 0.5
        else:
            calmar_score = 0.2
        
        return (sharpe_score + calmar_score) / 2
    
    def _score_consistency(self, metrics: Dict) -> float:
        """
        Score consistency (0.0-1.0).
        
        Breakdown:
        - Win Rate (50%)
        - Profit Factor (50%)
        """
        win_rate = metrics.get('win_rate', 0)
        profit_factor = metrics.get('profit_factor', 0)
        
        # Win rate scoring
        if win_rate >= 0.60:
            wr_score = 1.0
        elif win_rate >= 0.55:
            wr_score = 0.8
        elif win_rate >= 0.50:
            wr_score = 0.6
        elif win_rate >= 0.45:
            wr_score = 0.3
        else:
            wr_score = 0
        
        # Profit factor scoring
        if profit_factor >= 2.5:
            pf_score = 1.0
        elif profit_factor >= 2.0:
            pf_score = 0.8
        elif profit_factor >= 1.5:
            pf_score = 0.5
        elif profit_factor >= 1.2:
            pf_score = 0.2
        else:
            pf_score = 0
        
        return (wr_score + pf_score) / 2
    
    def _score_robustness(self, robustness_results: Dict) -> float:
        """
        Score robustness tests (0.0-1.0).
        
        If robustness results not available, return 0.5 (neutral).
        """
        if not robustness_results:
            return 0.5  # Neutral if no robustness data
        
        score = 0
        count = 0
        
        # OOS test
        if 'oos' in robustness_results:
            oos = robustness_results['oos']
            if oos.get('passed', False):
                oos_ratio = oos.get('oos_ratio', 0)
                if oos_ratio >= 0.9:
                    score += 1.0
                elif oos_ratio >= 0.7:
                    score += 0.7
                else:
                    score += 0.4
            count += 1
        
        # Monte Carlo
        if 'monte_carlo' in robustness_results:
            mc = robustness_results['monte_carlo']
            if mc.get('stable', False):
                score += 1.0
            count += 1
        
        # Walk-Forward
        if 'walk_forward' in robustness_results:
            wfa = robustness_results['walk_forward']
            if wfa.get('consistent', False):
                score += 1.0
            count += 1
        
        # Average across available tests
        return score / count if count > 0 else 0.5
    
    def _score_trade_frequency(self, metrics: Dict) -> float:
        """
        Score trade frequency (0.0-1.0).
        
        Sweet spot: 10-50 trades per month
        Too few: < 5 (not enough data)
        Too many: > 100 (overtrading, high costs)
        """
        total_trades = metrics.get('total_trades', 0)
        
        # Estimate trades per month (assume 1 year backtest)
        trades_per_month = total_trades / 12
        
        if 10 <= trades_per_month <= 50:
            return 1.0  # Perfect
        elif 5 <= trades_per_month < 10:
            return 0.6  # Acceptable but sparse
        elif 50 < trades_per_month <= 100:
            return 0.8  # Active but not excessive
        elif trades_per_month < 5:
            return 0.2  # Too few trades
        else:
            return 0.3  # Overtrading
    
    def _calculate_correlation_penalty(self,
                                       new_strategy: Dict,
                                       deployed_strategies: List[Dict]) -> float:
        """
        Penalize strategies that are too correlated with existing ones.
        
        This is a simplified version. Full implementation would analyze
        actual trade-by-trade correlation.
        
        Returns penalty in points (0-20).
        """
        # For now, penalize similar strategy types
        # In production, calculate actual correlation from trade returns
        
        # Placeholder: assume no correlation if no deployed strategies
        if not deployed_strategies or len(deployed_strategies) == 0:
            return 0
        
        # Heavy penalty if we already have 3+ strategies
        if len(deployed_strategies) >= 3:
            return 15  # Encourage diversification
        
        return 0
    
    # ==================== RANKING & RECOMMENDATIONS ====================
    
    def _get_rank(self, score: float) -> str:
        """Convert score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_recommendation(self, score: float, metrics: Dict) -> str:
        """
        Determine deployment recommendation.
        
        Returns:
            'DEPLOY': Deploy directly to live (if score >= 90 and Sharpe >= 2.0)
            'PAPER': Paper trading first (if score >= 75)
            'REJECT': Not ready for deployment
        """
        sharpe = metrics.get('sharpe', 0)
        
        # Auto-deploy threshold (exceptional strategies)
        if score >= 90 and sharpe >= cfg.AUTO_APPROVE_SHARPE:
            return 'DEPLOY'
        
        # Paper trading threshold
        elif score >= 75:
            return 'PAPER'
        
        # Needs manual review
        elif score >= 60:
            return 'REVIEW'
        
        # Reject
        else:
            return 'REJECT'
    
    def rank_strategies(self, strategies: List[Dict]) -> List[Dict]:
        """
        Rank multiple strategies by score.
        
        Args:
            strategies: List of dicts with backtest_metrics and robustness_results
        
        Returns:
            Same list sorted by score (highest first) with scores added
        """
        scored_strategies = []
        
        for strategy in strategies:
            score_result = self.score_strategy(
                backtest_metrics=strategy.get('backtest_metrics', {}),
                robustness_results=strategy.get('robustness_results'),
                deployed_strategies=[]  # Pass current deployed if available
            )
            
            strategy['score'] = score_result['total_score']
            strategy['rank'] = score_result['rank']
            strategy['recommendation'] = score_result['recommendation']
            strategy['score_breakdown'] = score_result['breakdown']
            
            scored_strategies.append(strategy)
        
        # Sort by score descending
        scored_strategies.sort(key=lambda x: x['score'], reverse=True)
        
        return scored_strategies


if __name__ == "__main__":
    print("=" * 60)
    print("STRATEGY SCORER - Demo")
    print("=" * 60)
    
    scorer = StrategyScorer()
    
    # Test strategy 1: Excellent
    metrics_excellent = {
        'sharpe': 2.5,
        'calmar': 3.2,
        'win_rate': 0.62,
        'profit_factor': 2.8,
        'total_trades': 240,
        'max_drawdown': 0.08
    }
    
    robustness_excellent = {
        'oos': {'passed': True, 'oos_ratio': 0.92},
        'monte_carlo': {'stable': True},
        'walk_forward': {'consistent': True}
    }
    
    print("\n1. Excellent Strategy:")
    result = scorer.score_strategy(metrics_excellent, robustness_excellent)
    print(f"   Score: {result['total_score']:.1f}/100")
    print(f"   Rank: {result['rank']}")
    print(f"   Recommendation: {result['recommendation']}")
    print(f"   Breakdown: {result['breakdown']}")
    
    # Test strategy 2: Marginal
    metrics_marginal = {
        'sharpe': 0.8,
        'calmar': 0.9,
        'win_rate': 0.48,
        'profit_factor': 1.3,
        'total_trades': 45,
        'max_drawdown': 0.18
    }
    
    print("\n2. Marginal Strategy:")
    result = scorer.score_strategy(metrics_marginal, None)
    print(f"   Score: {result['total_score']:.1f}/100")
    print(f"   Rank: {result['rank']}")
    print(f"   Recommendation: {result['recommendation']}")
    
    # Test strategy 3: Poor
    metrics_poor = {
        'sharpe': 0.2,
        'calmar': 0.3,
        'win_rate': 0.35,
        'profit_factor': 0.9,
        'total_trades': 300,
        'max_drawdown': 0.35
    }
    
    print("\n3. Poor Strategy:")
    result = scorer.score_strategy(metrics_poor, None)
    print(f"   Score: {result['total_score']:.1f}/100")
    print(f"   Rank: {result['rank']}")
    print(f"   Recommendation: {result['recommendation']}")
    
    print("\n" + "=" * 60)
    print("✅ Scoring system demo complete")
