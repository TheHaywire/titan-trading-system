"""
CORRELATION ANALYZER - Portfolio Diversification Analysis
=========================================================
Analyzes correlation between strategies to ensure portfolio diversification.
Prevents deploying too many similar strategies.

Key Metrics:
- Trade-by-Trade Correlation: Pearson correlation of daily PnL
- Symbol Overlap: How many common symbols
- Type Similarity: Same strategy type (MeanRev vs Trend)
- Timeframe Overlap: Trading on same timeframes
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
import logging

logger = logging.getLogger("Factory.Correlation")


class CorrelationAnalyzer:
    """
    Analyzes strategy correlation for portfolio construction.
    """
    
    def __init__(self, max_correlation: float = 0.70):
        """
        Initialize analyzer.
        
        Args:
            max_correlation: Maximum allowed correlation (default 0.70)
        """
        self.max_correlation = max_correlation
    
    def calculate_trade_correlation(self,
                                   strategy_a_trades: pd.DataFrame,
                                   strategy_b_trades: pd.DataFrame) -> float:
        """
        Calculate correlation between two strategies based on daily PnL.
        
        Args:
            strategy_a_trades: DataFrame with columns ['exit_time', 'pnl']
            strategy_b_trades: DataFrame with columns ['exit_time', 'pnl']
        
        Returns:
            Correlation coefficient (-1 to 1)
        """
        if len(strategy_a_trades) == 0 or len(strategy_b_trades) == 0:
            return 0.0  # No data = uncorrelated
        
        # Create daily PnL series
        a_daily = self._to_daily_pnl(strategy_a_trades)
        b_daily = self._to_daily_pnl(strategy_b_trades)
        
        # Align on common dates
        common_dates = a_daily.index.intersection(b_daily.index)
        
        if len(common_dates) < 10:
            return 0.0  # Insufficient overlap
        
        a_aligned = a_daily.loc[common_dates]
        b_aligned = b_daily.loc[common_dates]
        
        # Calculate Pearson correlation
        correlation = np.corrcoef(a_aligned.values, b_aligned.values)[0, 1]
        
        return correlation if not np.isnan(correlation) else 0.0
    
    def _to_daily_pnl(self, trades: pd.DataFrame) -> pd.Series:
        """
        Convert trade-level PnL to daily PnL series.
        
        Args:
            trades: DataFrame with 'exit_time' and 'pnl' columns
        
        Returns:
            Series indexed by date with daily PnL
        """
        if 'exit_time' not in trades.columns or 'pnl' not in trades.columns:
            return pd.Series(dtype=float)
        
        df = trades.copy()
        
        # Ensure exit_time is datetime
        if not pd.api.types.is_datetime64_any_dtype(df['exit_time']):
            df['exit_time'] = pd.to_datetime(df['exit_time'])
        
        # Extract date
        df['date'] = df['exit_time'].dt.date
        
        # Sum PnL by date
        daily_pnl = df.groupby('date')['pnl'].sum()
        
        return daily_pnl
    
    def calculate_similarity_score(self,
                                   strategy_a: Dict,
                                   strategy_b: Dict) -> float:
        """
        Calculate similarity between strategies based on multiple factors.
        
        Args:
            strategy_a/b: Strategy genome dicts with:
                {
                    'type': 'MeanReversion',
                    'symbols': ['GOLD'],
                    'timeframe': 'H1',
                    'indicators': {'RSI': {...}}
                }
        
        Returns:
            Similarity score 0.0-1.0 (higher = more similar)
        """
        similarity = 0
        factors = 0
        
        # 1. Strategy Type (30% weight)
        if strategy_a.get('type') == strategy_b.get('type'):
            similarity += 0.30
        factors += 1
        
        # 2. Symbol Overlap (30% weight)
        symbols_a = set(strategy_a.get('symbols', []))
        symbols_b = set(strategy_b.get('symbols', []))
        
        if symbols_a and symbols_b:
            overlap = len(symbols_a & symbols_b) / len(symbols_a | symbols_b)
            similarity += overlap * 0.30
        factors += 1
        
        # 3. Timeframe Match (20% weight)
        if strategy_a.get('timeframe') == strategy_b.get('timeframe'):
            similarity += 0.20
        factors += 1
        
        # 4. Indicator Overlap (20% weight)
        indicators_a = set(strategy_a.get('indicators', {}).keys())
        indicators_b = set(strategy_b.get('indicators', {}).keys())
        
        if indicators_a and indicators_b:
            ind_overlap = len(indicators_a & indicators_b) / len(indicators_a | indicators_b)
            similarity += ind_overlap * 0.20
        factors += 1
        
        return similarity
    
    def check_portfolio_diversification(self,
                                       new_strategy: Dict,
                                       deployed_strategies: List[Dict]) -> Tuple[bool, str]:
        """
        Check if adding new strategy would maintain portfolio diversification.
        
        Args:
            new_strategy: Strategy to potentially add
            deployed_strategies: Currently deployed strategies (with genomes and trades)
        
        Returns:
            (allow: bool, reason: str)
        """
        if not deployed_strategies or len(deployed_strategies) == 0:
            return (True, "First strategy - no correlation concerns")
        
        logger.info(f"Checking diversification for new strategy...")
        
        max_similarity = 0
        max_correlation = 0
        
        for deployed in deployed_strategies:
            # Similarity check (based on genome)
            similarity = self.calculate_similarity_score(
                new_strategy.get('genome', {}),
                deployed.get('genome', {})
            )
            
            max_similarity = max(max_similarity, similarity)
            
            # Trade correlation check (if trade data available)
            if 'trades' in new_strategy and 'trades' in deployed:
                try:
                    correlation = self.calculate_trade_correlation(
                        new_strategy['trades'],
                        deployed['trades']
                    )
                    max_correlation = max(max_correlation, abs(correlation))
                except:
                    pass
        
        logger.info(f"  Max Similarity: {max_similarity:.2f}")
        logger.info(f"  Max Correlation: {max_correlation:.2f}")
        
        # Decision logic
        if max_similarity > 0.80:
            return (False, f"Too similar to existing strategy (similarity: {max_similarity:.2f})")
        
        if max_correlation > self.max_correlation:
            return (False, f"Too correlated with existing strategy (correlation: {max_correlation:.2f})")
        
        return (True, "Diversification acceptable")
    
    def calculate_portfolio_correlation(self,
                                        strategies: List[Dict]) -> Dict:
        """
        Calculate average correlation across all strategy pairs in portfolio.
        
        Args:
            strategies: List of strategies with trade data
        
        Returns:
            {
                'avg_correlation': float,
                'max_correlation': float,
                'correlation_matrix': pd.DataFrame,
                'diversified': bool
            }
        """
        if len(strategies) < 2:
            return {
                'avg_correlation': 0,
                'max_correlation': 0,
                'correlation_matrix': None,
                'diversified': True
            }
        
        logger.info(f"Calculating portfolio correlation for {len(strategies)} strategies...")
        
        # Build correlation matrix
        n = len(strategies)
        corr_matrix = np.eye(n)  # Diagonal = 1.0 (self-correlation)
        
        for i in range(n):
            for j in range(i+1, n):
                try:
                    corr = self.calculate_trade_correlation(
                        strategies[i].get('trades', pd.DataFrame()),
                        strategies[j].get('trades', pd.DataFrame())
                    )
                    corr_matrix[i, j] = corr
                    corr_matrix[j, i] = corr
                except:
                    corr_matrix[i, j] = 0
                    corr_matrix[j, i] = 0
        
        # Extract upper triangle (excluding diagonal)
        upper_triangle = corr_matrix[np.triu_indices(n, k=1)]
        
        avg_corr = np.mean(np.abs(upper_triangle)) if len(upper_triangle) > 0 else 0
        max_corr = np.max(np.abs(upper_triangle)) if len(upper_triangle) > 0 else 0
        
        # Portfolio is diversified if avg correlation < 0.5
        diversified = avg_corr < 0.50
        
        logger.info(f"  Avg Correlation: {avg_corr:.2f}")
        logger.info(f"  Max Correlation: {max_corr:.2f}")
        logger.info(f"  Diversified: {'✅ Yes' if diversified else '⚠️ No'}")
        
        # Create labeled matrix
        strategy_names = [s.get('name', f'Strategy_{i}') for i, s in enumerate(strategies)]
        corr_df = pd.DataFrame(corr_matrix, columns=strategy_names, index=strategy_names)
        
        return {
            'avg_correlation': avg_corr,
            'max_correlation': max_corr,
            'correlation_matrix': corr_df,
            'diversified': diversified
        }


if __name__ == "__main__":
    print("=" * 60)
    print("CORRELATION ANALYZER - Demo")
    print("=" * 60)
    
    analyzer = CorrelationAnalyzer(max_correlation=0.70)
    
    # Create dummy trade data
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    
    # Strategy A: Random returns with positive drift
    trades_a = pd.DataFrame({
        'exit_time': dates[:200],
        'pnl': np.random.normal(50, 100, 200)
    })
    
    # Strategy B: Highly correlated with A
    trades_b = pd.DataFrame({
        'exit_time': dates[:200],
        'pnl': trades_a['pnl'] * 0.8 + np.random.normal(0, 20, 200)
    })
    
    # Strategy C: Uncorrelated
    trades_c = pd.DataFrame({
        'exit_time': dates[100:250],
        'pnl': np.random.normal(30, 80, 150)
    })
    
    # Test 1: Calculate correlation
    print("\n1. Trade Correlation:")
    corr_ab = analyzer.calculate_trade_correlation(trades_a, trades_b)
    corr_ac = analyzer.calculate_trade_correlation(trades_a, trades_c)
    print(f"   A vs B: {corr_ab:.2f} (highly correlated)")
    print(f"   A vs C: {corr_ac:.2f} (uncorrelated)")
    
    # Test 2: Similarity score
    print("\n2. Strategy Similarity:")
    genome_a = {
        'type': 'MeanReversion',
        'symbols': ['GOLD', 'SILVER'],
        'timeframe': 'H1',
        'indicators': {'RSI': {}, 'BB': {}}
    }
    
    genome_b = {
        'type': 'MeanReversion',
        'symbols': ['GOLD'],
        'timeframe': 'H1',
        'indicators': {'RSI': {}}
    }
    
    genome_c = {
        'type': 'TrendFollowing',
        'symbols': ['EURUSD'],
        'timeframe': 'M15',
        'indicators': {'EMA_fast': {}, 'EMA_slow': {}}
    }
    
    sim_ab = analyzer.calculate_similarity_score(genome_a, genome_b)
    sim_ac = analyzer.calculate_similarity_score(genome_a, genome_c)
    print(f"   A vs B: {sim_ab:.2f} (similar)")
    print(f"   A vs C: {sim_ac:.2f} (different)")
    
    # Test 3: Portfolio correlation
    print("\n3. Portfolio Correlation:")
    strategies = [
        {'name': 'Strategy A', 'trades': trades_a},
        {'name': 'Strategy B', 'trades': trades_b},
        {'name': 'Strategy C', 'trades': trades_c}
    ]
    
    portfolio_corr = analyzer.calculate_portfolio_correlation(strategies)
    print(f"   Avg Correlation: {portfolio_corr['avg_correlation']:.2f}")
    print(f"   Max Correlation: {portfolio_corr['max_correlation']:.2f}")
    print(f"   Diversified: {portfolio_corr['diversified']}")
    
    print("\n" + "=" * 60)
    print("✅ Correlation analyzer demo complete")
