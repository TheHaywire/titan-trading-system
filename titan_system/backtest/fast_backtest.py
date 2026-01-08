"""
TITAN FAST BACKTESTER (VectorBT Powered)
=========================================
Ultra-fast vectorized backtesting using VectorBT.
Test 1000s of parameter combinations in seconds.

Usage:
    from titan_system.backtest.fast_backtest import FastBacktester
    
    fb = FastBacktester(symbol='GOLD', timeframe='H1')
    
    # Test RSI strategy with multiple parameters
    results = fb.test_rsi_strategy(
        rsi_periods=[7, 14, 21],
        oversold_levels=[20, 25, 30],
        overbought_levels=[70, 75, 80]
    )
    
    # Get best parameters
    best = fb.get_best_params()
"""

import numpy as np
import pandas as pd
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

# Import VectorBT
try:
    import vectorbt as vbt
    VECTORBT_AVAILABLE = True
except ImportError:
    VECTORBT_AVAILABLE = False

# Import TA-Lib
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

import MetaTrader5 as mt5

logger = logging.getLogger("Titan.FastBacktest")


class FastBacktester:
    """
    VectorBT-powered fast backtester for parameter optimization.
    """
    
    def __init__(self, symbol: str = "GOLD", timeframe: str = "H1", bars: int = 5000):
        """
        Initialize fast backtester.
        
        Args:
            symbol: Symbol to backtest
            timeframe: Timeframe string (M15, H1, H4, D1)
            bars: Number of historical bars to use
        """
        if not VECTORBT_AVAILABLE:
            raise ImportError("VectorBT not available. Install with: pip install vectorbt")
        
        self.symbol = symbol
        self.timeframe = timeframe
        self.bars = bars
        self.df = None
        self.results = {}
        
        # Timeframe mapping
        self.tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
        
        self._load_data()
    
    def _load_data(self):
        """Load historical data from MT5"""
        if not mt5.initialize():
            raise ConnectionError("MT5 connection failed")
        
        tf = self.tf_map.get(self.timeframe, mt5.TIMEFRAME_H1)
        rates = mt5.copy_rates_from_pos(self.symbol, tf, 0, self.bars)
        
        if rates is None or len(rates) == 0:
            mt5.shutdown()
            raise ValueError(f"No data for {self.symbol}")
        
        self.df = pd.DataFrame(rates)
        self.df['time'] = pd.to_datetime(self.df['time'], unit='s')
        self.df.set_index('time', inplace=True)
        
        logger.info(f"[VBT] Loaded {len(self.df)} bars for {self.symbol} {self.timeframe}")
        mt5.shutdown()
    
    def test_rsi_strategy(self, 
                         rsi_periods: List[int] = [7, 14, 21],
                         oversold_levels: List[int] = [20, 25, 30],
                         overbought_levels: List[int] = [70, 75, 80]) -> pd.DataFrame:
        """
        Test RSI mean-reversion strategy with multiple parameters.
        
        Returns:
            DataFrame with results for each parameter combination
        """
        logger.info(f"[VBT] Testing RSI strategy: {len(rsi_periods) * len(oversold_levels) * len(overbought_levels)} combinations")
        
        close = self.df['close'].values
        results = []
        
        for period in rsi_periods:
            # Calculate RSI
            if TALIB_AVAILABLE:
                rsi = talib.RSI(close, timeperiod=period)
            else:
                delta = pd.Series(close).diff()
                gain = delta.where(delta > 0, 0).rolling(period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
                rsi = (100 - (100 / (1 + gain/loss))).values
            
            for oversold in oversold_levels:
                for overbought in overbought_levels:
                    # Generate signals
                    entries = rsi < oversold
                    exits = rsi > overbought
                    
                    # Run vectorized backtest
                    pf = vbt.Portfolio.from_signals(
                        close=self.df['close'],
                        entries=entries,
                        exits=exits,
                        init_cash=10000,
                        freq='1H' if 'H' in self.timeframe else '1D',
                        fees=0.0001  # 0.01% commission
                    )
                    
                    # Extract metrics
                    stats = pf.stats()
                    results.append({
                        'rsi_period': period,
                        'oversold': oversold,
                        'overbought': overbought,
                        'total_return': stats.get('Total Return [%]', 0),
                        'sharpe_ratio': stats.get('Sharpe Ratio', 0),
                        'max_drawdown': stats.get('Max Drawdown [%]', 0),
                        'win_rate': stats.get('Win Rate [%]', 0),
                        'num_trades': stats.get('Total Trades', 0),
                        'profit_factor': stats.get('Profit Factor', 0),
                    })
        
        self.results['rsi'] = pd.DataFrame(results)
        return self.results['rsi']
    
    def test_ema_crossover(self,
                          fast_periods: List[int] = [9, 12, 20],
                          slow_periods: List[int] = [21, 26, 50]) -> pd.DataFrame:
        """
        Test EMA crossover trend-following strategy.
        
        Returns:
            DataFrame with results for each parameter combination
        """
        logger.info(f"[VBT] Testing EMA crossover: {len(fast_periods) * len(slow_periods)} combinations")
        
        close = self.df['close'].values
        results = []
        
        for fast in fast_periods:
            for slow in slow_periods:
                if fast >= slow:
                    continue  # Skip invalid combinations
                
                # Calculate EMAs
                if TALIB_AVAILABLE:
                    ema_fast = talib.EMA(close, timeperiod=fast)
                    ema_slow = talib.EMA(close, timeperiod=slow)
                else:
                    ema_fast = pd.Series(close).ewm(span=fast).mean().values
                    ema_slow = pd.Series(close).ewm(span=slow).mean().values
                
                # Generate signals (crossovers)
                entries = (ema_fast[1:] > ema_slow[1:]) & (ema_fast[:-1] <= ema_slow[:-1])
                exits = (ema_fast[1:] < ema_slow[1:]) & (ema_fast[:-1] >= ema_slow[:-1])
                
                # Pad arrays
                entries = np.concatenate([[False], entries])
                exits = np.concatenate([[False], exits])
                
                # Run backtest
                pf = vbt.Portfolio.from_signals(
                    close=self.df['close'],
                    entries=entries,
                    exits=exits,
                    init_cash=10000,
                    freq='1H' if 'H' in self.timeframe else '1D',
                    fees=0.0001
                )
                
                stats = pf.stats()
                results.append({
                    'fast_period': fast,
                    'slow_period': slow,
                    'total_return': stats.get('Total Return [%]', 0),
                    'sharpe_ratio': stats.get('Sharpe Ratio', 0),
                    'max_drawdown': stats.get('Max Drawdown [%]', 0),
                    'win_rate': stats.get('Win Rate [%]', 0),
                    'num_trades': stats.get('Total Trades', 0),
                    'profit_factor': stats.get('Profit Factor', 0),
                })
        
        self.results['ema'] = pd.DataFrame(results)
        return self.results['ema']
    
    def test_bollinger_bands(self,
                            periods: List[int] = [10, 20, 30],
                            std_devs: List[float] = [1.5, 2.0, 2.5]) -> pd.DataFrame:
        """
        Test Bollinger Bands mean-reversion strategy.
        
        Returns:
            DataFrame with results for each parameter combination
        """
        logger.info(f"[VBT] Testing Bollinger Bands: {len(periods) * len(std_devs)} combinations")
        
        close = self.df['close']
        results = []
        
        for period in periods:
            for std in std_devs:
                # Calculate Bollinger Bands
                if TALIB_AVAILABLE:
                    upper, middle, lower = talib.BBANDS(
                        close.values, timeperiod=period, nbdevup=std, nbdevdn=std
                    )
                else:
                    middle = close.rolling(period).mean()
                    std_val = close.rolling(period).std()
                    upper = middle + (std * std_val)
                    lower = middle - (std * std_val)
                    upper, middle, lower = upper.values, middle.values, lower.values
                
                # Signals: Buy at lower band, Sell at upper band
                entries = close.values < lower
                exits = close.values > upper
                
                pf = vbt.Portfolio.from_signals(
                    close=close,
                    entries=entries,
                    exits=exits,
                    init_cash=10000,
                    freq='1H' if 'H' in self.timeframe else '1D',
                    fees=0.0001
                )
                
                stats = pf.stats()
                results.append({
                    'bb_period': period,
                    'std_dev': std,
                    'total_return': stats.get('Total Return [%]', 0),
                    'sharpe_ratio': stats.get('Sharpe Ratio', 0),
                    'max_drawdown': stats.get('Max Drawdown [%]', 0),
                    'win_rate': stats.get('Win Rate [%]', 0),
                    'num_trades': stats.get('Total Trades', 0),
                    'profit_factor': stats.get('Profit Factor', 0),
                })
        
        self.results['bollinger'] = pd.DataFrame(results)
        return self.results['bollinger']
    
    def get_best_params(self, strategy: str = None, metric: str = 'sharpe_ratio') -> Dict:
        """
        Get best parameters based on a metric.
        
        Args:
            strategy: Strategy name (rsi, ema, bollinger) or None for all
            metric: Metric to optimize (sharpe_ratio, total_return, win_rate)
            
        Returns:
            Dict with best parameters
        """
        if strategy and strategy in self.results:
            df = self.results[strategy]
            best_idx = df[metric].idxmax()
            return df.loc[best_idx].to_dict()
        
        # Find best across all strategies
        best_overall = None
        best_value = -np.inf
        
        for strat_name, df in self.results.items():
            if len(df) == 0:
                continue
            best_idx = df[metric].idxmax()
            value = df.loc[best_idx, metric]
            if value > best_value:
                best_value = value
                best_overall = {
                    'strategy': strat_name,
                    **df.loc[best_idx].to_dict()
                }
        
        return best_overall
    
    def summary(self) -> pd.DataFrame:
        """Get summary of all tested strategies"""
        summary_data = []
        
        for strat_name, df in self.results.items():
            if len(df) == 0:
                continue
            
            best = df.loc[df['sharpe_ratio'].idxmax()]
            summary_data.append({
                'strategy': strat_name,
                'best_sharpe': best['sharpe_ratio'],
                'best_return': best['total_return'],
                'best_win_rate': best['win_rate'],
                'params_tested': len(df)
            })
        
        return pd.DataFrame(summary_data)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TITAN FAST BACKTESTER - VectorBT Test")
    print("=" * 60)
    
    if not VECTORBT_AVAILABLE:
        print("[X] VectorBT not installed!")
        exit(1)
    
    print(f"[OK] VectorBT: {vbt.__version__}")
    print()
    
    # Run fast backtest
    print("Testing on GOLD H1...")
    fb = FastBacktester(symbol='GOLD', timeframe='H1', bars=2000)
    
    # Test RSI
    print("\n1. Testing RSI strategy...")
    rsi_results = fb.test_rsi_strategy()
    print(f"   Tested {len(rsi_results)} combinations")
    
    # Test EMA
    print("\n2. Testing EMA crossover...")
    ema_results = fb.test_ema_crossover()
    print(f"   Tested {len(ema_results)} combinations")
    
    # Get best parameters
    print("\n" + "=" * 60)
    print("BEST PARAMETERS:")
    print("=" * 60)
    
    best_rsi = fb.get_best_params('rsi')
    print(f"\nBest RSI:")
    print(f"  Period: {best_rsi['rsi_period']}, Oversold: {best_rsi['oversold']}, Overbought: {best_rsi['overbought']}")
    print(f"  Sharpe: {best_rsi['sharpe_ratio']:.2f}, Return: {best_rsi['total_return']:.1f}%")
    
    best_ema = fb.get_best_params('ema')
    print(f"\nBest EMA Crossover:")
    print(f"  Fast: {best_ema['fast_period']}, Slow: {best_ema['slow_period']}")
    print(f"  Sharpe: {best_ema['sharpe_ratio']:.2f}, Return: {best_ema['total_return']:.1f}%")
    
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print(fb.summary())
    print("\nSUCCESS: Fast backtester working!")
