"""
Combinatorial Backtesting Engine
Runs all strategy parameter combinations across symbols and timeframes.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from strategy_mining.strategies import AlphaArchetypes, calculate_performance_vectorized
import strategy_mining.mining_config as config

# Setup logging
logger = logging.getLogger(__name__)

class BacktestingEngine:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def run_all_combinations(self) -> pd.DataFrame:
        """
        Run all strategies across all symbols and timeframes in the data.
        Returns: Summary DataFrame with results for every combination.
        """
        results = []
        
        # Get levels from MultiIndex
        symbols = self.data.index.get_level_values('symbol').unique()
        timeframes = self.data.index.get_level_values('timeframe').unique()
        
        for symbol in symbols:
            for tf in timeframes:
                try:
                    # Slice data for this symbol/timeframe
                    subset = self.data.xs((symbol, tf), level=('symbol', 'timeframe'))
                    
                    if len(subset) < config.MIN_TRADES * 2:
                        continue
                        
                    # 1. Mean Reversion Testing
                    for z in config.MEAN_REVERSION_PARAMS['z_thresholds']:
                        for window in config.MEAN_REVERSION_PARAMS['vwap_window']:
                            signals = AlphaArchetypes.mean_reversion_zscore_vwap(subset, window, z)
                            metrics = calculate_performance_vectorized(subset, signals)
                            
                            if metrics['num_trades'] >= config.MIN_TRADES:
                                results.append({
                                    'symbol': symbol,
                                    'timeframe': tf,
                                    'strategy': 'MeanReversion',
                                    'params': f"window={window},z={z}",
                                    **metrics
                                })
                    
                    # 2. Trend Following Testing
                    for fast, slow in config.TREND_FOLLOWING_PARAMS['ema_combinations']:
                        signals = AlphaArchetypes.trend_following_ema_cross(subset, fast, slow)
                        metrics = calculate_performance_vectorized(subset, signals)
                        
                        if metrics['num_trades'] >= config.MIN_TRADES:
                            results.append({
                                'symbol': symbol,
                                'timeframe': tf,
                                'strategy': 'TrendFollowing',
                                'params': f"fast={fast},slow={slow}",
                                **metrics
                            })
                            
                    # 3. Volatility Expansion Testing
                    for mult in config.VOLATILITY_EXPANSION_PARAMS['keltner_multipliers']:
                        for ema in config.VOLATILITY_EXPANSION_PARAMS['ema_period']:
                            signals = AlphaArchetypes.volatility_expansion_keltner(subset, ema, 14, mult)
                            metrics = calculate_performance_vectorized(subset, signals)
                            
                            if metrics['num_trades'] >= config.MIN_TRADES:
                                results.append({
                                    'symbol': symbol,
                                    'timeframe': tf,
                                    'strategy': 'VolatilityExpansion',
                                    'params': f"ema={ema},mult={mult}",
                                    **metrics
                                })
                except Exception as e:
                    logger.error(f"Error backtesting {symbol} {tf}: {e}")
                    
        return pd.DataFrame(results)

    @staticmethod
    def filter_top_candidates(results_df: pd.DataFrame) -> pd.DataFrame:
        """Filter results based on performance criteria."""
        if results_df.empty:
            return results_df
            
        filtered = results_df[
            (results_df['profit_factor'] >= config.MIN_PROFIT_FACTOR) &
            (results_df['num_trades'] >= config.MIN_TRADES)
        ]
        
        # Sort by Profit Factor and Sharpe Ratio
        return filtered.sort_values(by=['profit_factor', 'sharpe_ratio'], ascending=False)
