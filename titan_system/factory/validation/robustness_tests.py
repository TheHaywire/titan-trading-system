"""
ROBUSTNESS TESTS - Statistical Validation Framework
===================================================
Advanced validation beyond simple backtests:
1. Out-of-Sample (OOS) Validation
2. Monte Carlo Simulation
3. Walk-Forward Analysis
4. Parameter Sensitivity Testing
5. Regime Breakdown Analysis
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable
from datetime import datetime
import logging

logger = logging.getLogger("Factory.Robustness")


class RobustnessTests:
    """
    Statistical rigor tests for strategy validation.
    Ensures strategies aren't overfit and will perform in live markets.
    """
    
    def __init__(self, min_trades: int = 30):
        """
        Initialize robustness tester.
        
        Args:
            min_trades: Minimum trades required for valid test
        """
        self.min_trades = min_trades
        self.results = {}
    
    # ==================== OUT-OF-SAMPLE VALIDATION ====================
    
    def out_of_sample_test(self,
                           backtest_func: Callable,
                           data: pd.DataFrame,
                           train_ratio: float = 0.70) -> Dict:
        """
        Split data into training/testing and validate performance consistency.
        
        Args:
            backtest_func: Function that takes data and returns metrics dict
            data: Full historical data
            train_ratio: Fraction of data for training (default 70%)
        
        Returns:
            {
                'in_sample': {...metrics},
                'out_sample': {...metrics},
                'oos_ratio': float,  # OOS Sharpe / IS Sharpe
                'passed': bool
            }
        """
        logger.info(f"[OOS] Running out-of-sample validation (train={train_ratio*100:.0f}%)")
        
        # Split data
        split_idx = int(len(data) * train_ratio)
        train_data = data.iloc[:split_idx]
        test_data = data.iloc[split_idx:]
        
        logger.info(f"  Train: {len(train_data)} bars, Test: {len(test_data)} bars")
        
        # Run backtest on both datasets
        try:
            is_metrics = backtest_func(train_data)
            oos_metrics = backtest_func(test_data)
        except Exception as e:
            logger.error(f"[OOS] Backtest failed: {e}")
            return {'passed': False, 'error': str(e)}
        
        # Check minimum trades
        if is_metrics.get('total_trades', 0) < self.min_trades:
            logger.warning(f"[OOS] Insufficient trades in training: {is_metrics.get('total_trades', 0)}")
            return {'passed': False, 'reason': 'Insufficient trades'}
        
        # Calculate OOS ratio
        is_sharpe = is_metrics.get('sharpe', 0)
        oos_sharpe = oos_metrics.get('sharpe', 0)
        
        if is_sharpe <= 0:
            oos_ratio = 0
        else:
            oos_ratio = oos_sharpe / is_sharpe
        
        # Test passed if OOS >= 70% of IS
        passed = oos_ratio >= 0.70
        
        logger.info(f"  IS Sharpe: {is_sharpe:.2f}, OOS Sharpe: {oos_sharpe:.2f}, Ratio: {oos_ratio:.2f}")
        logger.info(f"  Result: {'✅ PASSED' if passed else '❌ FAILED (likely overfit)'}")
        
        return {
            'in_sample': is_metrics,
            'out_sample': oos_metrics,
            'oos_ratio': oos_ratio,
            'passed': passed
        }
    
    # ==================== MONTE CARLO SIMULATION ====================
    
    def monte_carlo_simulation(self,
                               trade_returns: List[float],
                               iterations: int = 1000,
                               confidence: float = 0.95) -> Dict:
        """
        Shuffle trade order to test if results are robust or luck.
        
        Args:
            trade_returns: List of individual trade returns (in %)
            iterations: Number of random shuffles
            confidence: Confidence level for intervals
        
        Returns:
            {
                'original_sharpe': float,
                'mc_mean_sharpe': float,
                'mc_std_sharpe': float,
                'confidence_interval': (lower, upper),
                'stable': bool  # True if original within conf interval
            }
        """
        if len(trade_returns) < self.min_trades:
            return {'stable': False, 'reason': 'Insufficient trades'}
        
        logger.info(f"[MC] Running Monte Carlo with {iterations} iterations")
        
        # Calculate original metrics
        original_sharpe = self._calculate_sharpe(trade_returns)
        
        # Run simulations
        mc_sharpes = []
        trade_arr = np.array(trade_returns)
        
        for i in range(iterations):
            # Shuffle trades
            shuffled = np.random.permutation(trade_arr)
            sharpe = self._calculate_sharpe(shuffled.tolist())
            mc_sharpes.append(sharpe)
        
        # Calculate statistics
        mc_mean = np.mean(mc_sharpes)
        mc_std = np.std(mc_sharpes)
        
        # Confidence interval
        lower_pct = (1 - confidence) / 2
        upper_pct = 1 - lower_pct
        ci_lower = np.percentile(mc_sharpes, lower_pct * 100)
        ci_upper = np.percentile(mc_sharpes, upper_pct * 100)
        
        # Check stability: original should be within confidence interval
        stable = ci_lower <= original_sharpe <= ci_upper
        
        logger.info(f"  Original Sharpe: {original_sharpe:.2f}")
        logger.info(f"  MC Mean: {mc_mean:.2f}, Std: {mc_std:.2f}")
        logger.info(f"  {confidence*100:.0f}% CI: [{ci_lower:.2f}, {ci_upper:.2f}]")
        logger.info(f"  Result: {'✅ STABLE' if stable else '⚠️ UNSTABLE (high variance)'}")
        
        return {
            'original_sharpe': original_sharpe,
            'mc_mean_sharpe': mc_mean,
            'mc_std_sharpe': mc_std,
            'confidence_interval': (ci_lower, ci_upper),
            'stable': stable
        }
    
    # ==================== WALK-FORWARD ANALYSIS ====================
    
    def walk_forward_analysis(self,
                              backtest_func: Callable,
                              data: pd.DataFrame,
                              windows: int = 12,
                              train_months: int = 3,
                              test_months: int = 1) -> Dict:
        """
        Rolling window optimization and testing.
        
        Args:
            backtest_func: Function that takes data and returns metrics
            data: Full historical data with datetime index
            windows: Number of walk-forward windows
            train_months: Months of data to train on
            test_months: Months of data to test on
        
        Returns:
            {
                'results': List[Dict],  # Results for each window
                'avg_sharpe': float,
                'sharpe_std': float,
                'consistent': bool  # True if std/mean < 0.5
            }
        """
        logger.info(f"[WFA] Running walk-forward analysis: {windows} windows")
        
        results = []
        data = data.sort_index()
        
        # Calculate window size in bars (approximate)
        total_days = (data.index[-1] - data.index[0]).days
        bars_per_day = len(data) / total_days
        train_bars = int(train_months * 30 * bars_per_day)
        test_bars = int(test_months * 30 * bars_per_day)
        window_bars = train_bars + test_bars
        
        for i in range(windows):
            start_idx = i * test_bars
            train_end_idx = start_idx + train_bars
            test_end_idx = train_end_idx + test_bars
            
            if test_end_idx > len(data):
                break
            
            train_window = data.iloc[start_idx:train_end_idx]
            test_window = data.iloc[train_end_idx:test_end_idx]
            
            if len(test_window) == 0:
                continue
            
            try:
                # In real WFA, you'd optimize params on train_window
                # For now, just test on the test window
                metrics = backtest_func(test_window)
                
                results.append({
                    'window': i + 1,
                    'test_period': (test_window.index[0], test_window.index[-1]),
                    'sharpe': metrics.get('sharpe', 0),
                    'return': metrics.get('total_return', 0),
                    'trades': metrics.get('total_trades', 0)
                })
                
            except Exception as e:
                logger.warning(f"  Window {i+1} failed: {e}")
                continue
        
        if len(results) == 0:
            return {'consistent': False, 'reason': 'No valid windows'}
        
        # Calculate consistency
        sharpes = [r['sharpe'] for r in results]
        avg_sharpe = np.mean(sharpes)
        sharpe_std = np.std(sharpes)
        
        # Consistent if coefficient of variation < 0.5
        cv = sharpe_std / avg_sharpe if avg_sharpe != 0 else np.inf
        consistent = cv < 0.5
        
        logger.info(f"  Tested {len(results)} windows")
        logger.info(f"  Avg Sharpe: {avg_sharpe:.2f}, Std: {sharpe_std:.2f}, CV: {cv:.2f}")
        logger.info(f"  Result: {'✅ CONSISTENT' if consistent else '⚠️ INCONSISTENT'}")
        
        return {
            'results': results,
            'avg_sharpe': avg_sharpe,
            'sharpe_std': sharpe_std,
            'coefficient_of_variation': cv,
            'consistent': consistent
        }
    
    # ==================== PARAMETER SENSITIVITY ====================
    
    def parameter_sensitivity_test(self,
                                   backtest_func: Callable,
                                   data: pd.DataFrame,
                                   base_params: Dict,
                                   param_to_test: str,
                                   variation_pct: float = 0.20) -> Dict:
        """
        Test if performance degrades gracefully when parameters change.
        
        Args:
            backtest_func: Function(data, params) -> metrics
            data: Historical data
            base_params: Base parameter set
            param_to_test: Parameter name to vary
            variation_pct: How much to vary (±20% default)
        
        Returns:
            {
                'base_sharpe': float,
                'degradation': float,  # Max % drop in Sharpe
                'sensitive': bool  # True if degradation > 30%
            }
        """
        logger.info(f"[SENSITIVITY] Testing parameter: {param_to_test}")
        
        # Test base parameters
        base_metrics = backtest_func(data, base_params)
        base_sharpe = base_metrics.get('sharpe', 0)
        
        if base_sharpe <= 0:
            return {'sensitive': True, 'reason': 'Base Sharpe <= 0'}
        
        # Test variations
        base_value = base_params[param_to_test]
        variations = [
            base_value * (1 - variation_pct),
            base_value * (1 + variation_pct)
        ]
        
        sharpes = [base_sharpe]
        
        for var_value in variations:
            test_params = base_params.copy()
            test_params[param_to_test] = var_value
            
            try:
                metrics = backtest_func(data, test_params)
                sharpes.append(metrics.get('sharpe', 0))
            except:
                sharpes.append(0)
        
        # Calculate max degradation
        min_sharpe = min(sharpes)
        degradation = (base_sharpe - min_sharpe) / base_sharpe if base_sharpe > 0 else 1.0
        
        # Sensitive if performance drops >30%
        sensitive = degradation > 0.30
        
        logger.info(f"  Base Sharpe: {base_sharpe:.2f}")
        logger.info(f"  Min Sharpe: {min_sharpe:.2f}")
        logger.info(f"  Max Degradation: {degradation*100:.1f}%")
        logger.info(f"  Result: {'⚠️ SENSITIVE' if sensitive else '✅ ROBUST'}")
        
        return {
            'base_sharpe': base_sharpe,
            'min_sharpe': min_sharpe,
            'degradation': degradation,
            'sensitive': sensitive
        }
    
    # ==================== HELPER METHODS ====================
    
    def _calculate_sharpe(self, returns: List[float], risk_free: float = 0) -> float:
        """
        Calculate Sharpe Ratio from trade returns.
        
        Args:
            returns: List of trade returns (%)
            risk_free: Risk-free rate (annualized %)
        
        Returns:
            Sharpe Ratio
        """
        if len(returns) == 0:
            return 0
        
        returns_arr = np.array(returns)
        mean_return = np.mean(returns_arr)
        std_return = np.std(returns_arr)
        
        if std_return == 0:
            return 0
        
        # Annualize (assuming ~250 trading days)
        sharpe = (mean_return - risk_free) / std_return * np.sqrt(250)
        
        return sharpe
    
    def run_full_validation(self,
                           backtest_func: Callable,
                           data: pd.DataFrame,
                           trade_returns: List[float] = None) -> Dict:
        """
        Run all robustness tests and return comprehensive results.
        
        Args:
            backtest_func: Backtest function
            data: Historical data
            trade_returns: Individual trade returns (optional, for MC)
        
        Returns:
            Complete validation results with overall pass/fail
        """
        logger.info("=" * 60)
        logger.info("FULL ROBUSTNESS VALIDATION")
        logger.info("=" * 60)
        
        results = {}
        
        # 1. Out-of-Sample
        oos = self.out_of_sample_test(backtest_func, data)
        results['oos'] = oos
        
        # 2. Monte Carlo (if trade returns provided)
        if trade_returns and len(trade_returns) >= self.min_trades:
            mc = self.monte_carlo_simulation(trade_returns, iterations=1000)
            results['monte_carlo'] = mc
        else:
            results['monte_carlo'] = {'stable': False, 'reason': 'No trade data'}
        
        # 3. Walk-Forward
        wfa = self.walk_forward_analysis(backtest_func, data, windows=6)
        results['walk_forward'] = wfa
        
        # Overall pass/fail
        passed = (
            oos.get('passed', False) and
            results['monte_carlo'].get('stable', False) and
            wfa.get('consistent', False)
        )
        
        results['overall_passed'] = passed
        
        logger.info("=" * 60)
        logger.info(f"OVERALL RESULT: {'✅ PASSED' if passed else '❌ FAILED'}")
        logger.info("=" * 60)
        
        return results


# ==================== UTILITY FUNCTIONS ====================

def extract_trade_returns(trades_df: pd.DataFrame) -> List[float]:
    """
    Extract individual trade returns from backtest results.
    
    Args:
        trades_df: DataFrame with 'pnl' or 'return' column
    
    Returns:
        List of returns in %
    """
    if 'return' in trades_df.columns:
        return trades_df['return'].tolist()
    elif 'pnl_pct' in trades_df.columns:
        return trades_df['pnl_pct'].tolist()
    elif 'pnl' in trades_df.columns and 'entry_price' in trades_df.columns:
        returns = (trades_df['pnl'] / trades_df['entry_price']) * 100
        return returns.tolist()
    else:
        return []


if __name__ == "__main__":
    print("=" * 60)
    print("ROBUSTNESS TESTS - Demo")
    print("=" * 60)
    
    # Create dummy backtest function
    def dummy_backtest(data, params=None):
        """Simulate a backtest that returns random metrics."""
        np.random.seed(len(data))  # Deterministic but different per data size
        return {
            'sharpe': np.random.uniform(0.8, 1.5),
            'total_return': np.random.uniform(10, 50),
            'total_trades': int(len(data) / 50),
            'max_drawdown': np.random.uniform(0.05, 0.15)
        }
    
    # Create dummy data
    dates = pd.date_range('2020-01-01', '2024-01-01', freq='1H')
    data = pd.DataFrame({
        'close': np.random.randn(len(dates)).cumsum() + 1000,
        'high': np.random.randn(len(dates)).cumsum() + 1010,
        'low': np.random.randn(len(dates)).cumsum() + 990
    }, index=dates)
    
    # Dummy trade returns
    trade_returns = np.random.normal(0.5, 2.0, 100).tolist()
    
    # Run tests
    tester = RobustnessTests()
    
    print("\n1. Out-of-Sample Test:")
    oos_result = tester.out_of_sample_test(dummy_backtest, data)
    print(f"   Passed: {oos_result['passed']}")
    
    print("\n2. Monte Carlo Simulation:")
    mc_result = tester.monte_carlo_simulation(trade_returns)
    print(f"   Stable: {mc_result['stable']}")
    
    print("\n3. Walk-Forward Analysis:")
    wfa_result = tester.walk_forward_analysis(dummy_backtest, data, windows=6)
    print(f"   Consistent: {wfa_result['consistent']}")
    
    print("\n✅ Demo complete")
