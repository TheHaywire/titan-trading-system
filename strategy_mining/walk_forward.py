"""
Walk-Forward Analysis (WFA) Module
Validates strategy robustness across multiple out-of-sample periods.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
import logging
from strategy_mining.strategies import AlphaArchetypes, calculate_performance_vectorized
import strategy_mining.mining_config as config

# Setup logging
logger = logging.getLogger(__name__)

class WalkForwardAnalyzer:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def run_wfa(self, symbol: str, timeframe: str, strategy_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run 5-window Walk-Forward Analysis for a specific strategy/param set.
        Returns: WFA metrics including number of profitable OOS windows.
        """
        try:
            subset = self.data.xs((symbol, timeframe), level=('symbol', 'timeframe'))
        except KeyError:
            return {'robust': False, 'oos_profitable_windows': 0}

        # Divide into 5 windows
        window_size = len(subset) // config.WFA_NUM_WINDOWS
        if window_size < 50: # Minimum size for valid window
            return {'robust': False, 'oos_profitable_windows': 0}

        oos_results = []
        oos_returns = []
        
        for i in range(config.WFA_NUM_WINDOWS):
            # Define window range
            start_idx = i * window_size
            end_idx = (i + 1) * window_size
            
            # Split window into In-Sample (70%) and Out-of-Sample (30%)
            split_idx = start_idx + int(window_size * config.WFA_IN_SAMPLE_PCT)
            
            oos_data = subset.iloc[split_idx:end_idx]
            
            if len(oos_data) < 10:
                continue
                
            # Generate signals on OOS data
            signals = self._generate_signals(oos_data, strategy_name, params)
            metrics = calculate_performance_vectorized(oos_data, signals)
            
            oos_results.append(metrics['profit_factor'] > 1.0) # Check if profitable in OOS
            oos_returns.append(metrics['total_return'])
            
        total_oos_return = sum(oos_returns)
        profitable_windows = sum(oos_results)
        
        # Robust if enough profitable windows AND positive total return
        is_robust = (profitable_windows >= config.WFA_MIN_OOS_PROFITABLE_WINDOWS and 
                     total_oos_return >= config.MIN_CUMULATIVE_RETURN)
        
        return {
            'robust': is_robust,
            'oos_profitable_windows': profitable_windows,
            'total_oos_return': total_oos_return,
            'total_windows': len(oos_results)
        }

    def _generate_signals(self, df: pd.DataFrame, name: str, params: Dict[str, Any]) -> pd.Series:
        """Helper to generate signals based on strategy name and parsed params."""
        if name == 'MeanReversion':
            # Params looks like "window=20,z=2.0"
            p = {k: float(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.mean_reversion_zscore_vwap(df, int(p['window']), p['z'])
            
        elif name == 'TrendFollowing':
            p = {k: int(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.trend_following_ema_cross(df, p['fast'], p['slow'])
            
        elif name == 'VolatilityExpansion':
            p = {k: float(v) for k, v in [item.split('=') for item in params.split(',')]}
            return AlphaArchetypes.volatility_expansion_keltner(df, int(p['ema']), 14, p['mult'])
            
        return pd.Series(0, index=df.index)

    def filter_robust_strategies(self, results_df: pd.DataFrame) -> pd.DataFrame:
        """Run WFA on top candidates and return only the robust ones."""
        if results_df.empty:
            return results_df
            
        robust_results = []
        logger.info(f"Running Walk-Forward Analysis on {len(results_df)} candidates...")
        
        for _, row in results_df.iterrows():
            wfa = self.run_wfa(row['symbol'], row['timeframe'], row['strategy'], row['params'])
            if wfa['robust']:
                robust_results.append({**row.to_dict(), **wfa})
                
        return pd.DataFrame(robust_results)
