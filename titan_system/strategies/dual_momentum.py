"""
Dual Momentum Strategy Implementation
Based on Gary Antonacci's research (2014)

Hypothesis: Assets with strong 12-month momentum continue outperforming
Edge: Behavioral bias (underreaction) + momentum cascades
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("Titan.DualMomentum")

class DualMomentumStrategy:
    """
    Dual Momentum: Combines Absolute + Relative Momentum
    
    Absolute Momentum: Asset 12-month return > 0
    Relative Momentum: Asset outperforms benchmark
    
    Entry: Both conditions met
    Exit: 12-month return turns negative
    Rebalance: Monthly
    """
    
    def __init__(self, lookback_days=252, benchmark_symbol="US500Cash"):
        """
        Args:
            lookback_days: 252 trading days = ~12 months
            benchmark_symbol: Comparison asset (default: S&P 500 Cash)
        """
        self.name = "DualMomentum"
        self.lookback_days = lookback_days
        self.benchmark_symbol = benchmark_symbol
        self.magic_number = 100001
        
    def calculate_momentum(self, prices):
        """
        Calculate 12-month momentum (CAGR)
        
        Formula: (Current_Price / Price_12mo_ago) - 1
        
        Returns:
            float: Momentum score (e.g., 0.15 = 15% gain over 12 months)
        """
        if len(prices) < self.lookback_days:
            logger.warning(f"Not enough data: {len(prices)} < {self.lookback_days}")
            return None
            
        current_price = prices[-1]
        past_price = prices[-self.lookback_days]
        
        if past_price == 0:
            return None
            
        momentum = (current_price / past_price) - 1
        return momentum
    
    def get_absolute_momentum_signal(self, asset_momentum):
        """
        Absolute Momentum: Is asset trending up?
        
        Args:
            asset_momentum: 12-month return
            
        Returns:
            bool: True if momentum > 0 (uptrend)
        """
        if asset_momentum is None:
            return False
            
        return asset_momentum > 0
    
    def get_relative_momentum_signal(self, asset_momentum, benchmark_momentum):
        """
        Relative Momentum: Does asset outperform benchmark?
        
        Args:
            asset_momentum: Asset's 12-month return
            benchmark_momentum: Benchmark's 12-month return
            
        Returns:
            bool: True if asset > benchmark
        """
        if asset_momentum is None or benchmark_momentum is None:
            return False
            
        return asset_momentum > benchmark_momentum
    
    def analyze(self, symbol, df):
        """
        Main analysis function called by TitanEngine
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD")
            df: DataFrame with OHLCV data
            
        Returns:
            dict: {
                'signal': 'BUY' | 'SELL' | 'HOLD',
                'confidence': float (0-1),
                'setup': str,
                'metadata': dict,
                'metrics': dict
            }
        """
        # Default response
        result = {
            'signal': 'HOLD',
            'confidence': 0.0,
            'setup': 'Dual Momentum',
            'metadata': {},
            'metrics': {}
        }
        
        # Need enough data
        if len(df) < self.lookback_days + 10:
            logger.debug(f"{symbol}: Insufficient data ({len(df)} bars)")
            return result
        
        # Calculate asset momentum
        asset_prices = df['close'].values
        asset_momentum = self.calculate_momentum(asset_prices)
        
        if asset_momentum is None:
            return result
        
        # Get benchmark data
        benchmark_rates = mt5.copy_rates_from_pos(
            self.benchmark_symbol,
            mt5.TIMEFRAME_D1,
            0,
            self.lookback_days + 10
        )
        
        if benchmark_rates is None or len(benchmark_rates) < self.lookback_days:
            logger.warning(f"Could not fetch {self.benchmark_symbol} data")
            # Fall back to absolute momentum only
            if self.get_absolute_momentum_signal(asset_momentum):
                result['signal'] = 'BUY'
                result['confidence'] = min(0.75, 0.5 + abs(asset_momentum))
                result['setup'] = 'Absolute Momentum Only'
                result['metadata'] = {
                    'asset_momentum': asset_momentum,
                    'benchmark_momentum': None,
                    'signal_type': 'absolute_only'
                }
            return result
        
        # Calculate benchmark momentum
        benchmark_df = pd.DataFrame(benchmark_rates)
        benchmark_prices = benchmark_df['close'].values
        benchmark_momentum = self.calculate_momentum(benchmark_prices)
        
        # Dual Momentum Logic
        absolute_signal = self.get_absolute_momentum_signal(asset_momentum)
        relative_signal = self.get_relative_momentum_signal(asset_momentum, benchmark_momentum)
        
        # BUY if both absolute AND relative momentum
        if absolute_signal and relative_signal:
            result['signal'] = 'BUY'
            # Confidence increases with strength of momentum
            confidence_boost = min(0.3, abs(asset_momentum - benchmark_momentum))
            result['confidence'] = 0.70 + confidence_boost
            result['setup'] = 'Dual Momentum (Absolute + Relative)'
            result['metadata'] = {
                'asset_momentum': asset_momentum,
                'benchmark_momentum': benchmark_momentum,
                'momentum_spread': asset_momentum - benchmark_momentum,
                'signal_type': 'dual_momentum'
            }
            
        # SELL/EXIT if absolute momentum turns negative
        elif not absolute_signal:
            result['signal'] = 'SELL'
            result['confidence'] = 0.60
            result['setup'] = 'Negative Momentum - Exit'
            result['metadata'] = {
                'asset_momentum': asset_momentum,
                'benchmark_momentum': benchmark_momentum,
                'signal_type': 'momentum_exit'
            }
        
        # Metrics for stop-loss calculation
        result['metrics'] = {
            'atr': df['high'].rolling(20).mean().iloc[-1] - df['low'].rolling(20).mean().iloc[-1],
            'std_dev': df['close'].rolling(20).std().iloc[-1],
            'volatility': df['close'].pct_change().std() * np.sqrt(252)  # Annualized
        }
        
        # Log the decision
        logger.info(
            f"📊 {symbol} Dual Momentum: "
            f"Asset={asset_momentum:.2%}, Bench={benchmark_momentum:.2%}, "
            f"Signal={result['signal']}, Conf={result['confidence']:.2f}"
        )
        
        return result
    
    def should_rebalance(self):
        """
        Check if it's time to rebalance (monthly)
        
        Returns:
            bool: True if last trading day of month
        """
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        
        # If tomorrow is a new month, rebalance today
        return tomorrow.month != today.month
    
    def get_portfolio_allocation(self, symbols):
        """
        For multi-asset Dual Momentum, rank and allocate
        
        Args:
            symbols: List of symbols to analyze
            
        Returns:
            dict: {symbol: allocation_weight}
        """
        momentum_scores = {}
        
        for symbol in symbols:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, self.lookback_days + 10)
            if rates is None:
                continue
                
            df = pd.DataFrame(rates)
            prices = df['close'].values
            momentum = self.calculate_momentum(prices)
            
            if momentum is not None and momentum > 0:
                momentum_scores[symbol] = momentum
        
        # Sort by momentum (highest first)
        sorted_symbols = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Allocate to top 3 (equal weight)
        allocation = {}
        top_n = min(3, len(sorted_symbols))
        
        for i in range(top_n):
            symbol, score = sorted_symbols[i]
            allocation[symbol] = 1.0 / top_n  # Equal weight
            
        logger.info(f"🎯 Portfolio Allocation: {allocation}")
        return allocation

if __name__ == "__main__":
    # Test the strategy
    if not mt5.initialize():
        print("MT5 initialization failed")
        exit()
    
    strategy = DualMomentumStrategy()
    
    # Test on Gold
    symbol = "XAUUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 300)
    
    if rates is not None:
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        result = strategy.analyze(symbol, df)
        
        print(f"\n{'='*60}")
        print(f"DUAL MOMENTUM TEST: {symbol}")
        print(f"{'='*60}")
        print(f"Signal: {result['signal']}")
        print(f"Confidence: {result['confidence']:.2%}")
        print(f"Setup: {result['setup']}")
        print(f"\nMetadata:")
        for key, value in result['metadata'].items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2%}")
            else:
                print(f"  {key}: {value}")
    
    mt5.shutdown()
