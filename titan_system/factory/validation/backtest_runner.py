"""
STRATEGY BACKTEST RUNNER - Genome-Compatible Backtesting
========================================================
Bridges StrategyGenome format with backtesting engines.
Runs strategies through validation pipeline and updates registry.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from typing import Dict, Optional
from datetime import datetime
import logging

from titan_system.factory.strategy_genome import StrategyGenome
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.validation.robustness_tests import RobustnessTests
from titan_system.factory import factory_config as cfg

# Try to import TA-Lib
try:
    import talib
    TALIB_AVAILABLE = True
except ImportError:
    TALIB_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Factory.Backtest")


class StrategyBacktestRunner:
    """
    Runs backtests on StrategyGenome candidates and validates them.
    """
    
    def __init__(self, registry: StrategyRegistry = None):
        """
        Initialize backtest runner.
        
        Args:
            registry: StrategyRegistry instance (creates new if None)
        """
        self.registry = registry or StrategyRegistry()
        self.robustness_tester = RobustnessTests(min_trades=cfg.MIN_BACKTEST_TRADES)
        
        # TF mapping
        self.tf_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M5': mt5.TIMEFRAME_M5,
            'M15': mt5.TIMEFRAME_M15,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H4': mt5.TIMEFRAME_H4,
            'D1': mt5.TIMEFRAME_D1,
        }
    
    def backtest_genome(self, genome: StrategyGenome, 
                       validate: bool = True,
                       update_registry: bool = True) -> Dict:
        """
        Run full backtest on a strategy genome.
        
        Args:
            genome: StrategyGenome to test
            validate: Run robustness tests
            update_registry: Update registry with results
        
        Returns:
            Complete backtest results dict
        """
        logger.info("=" * 60)
        logger.info(f"BACKTESTING: {genome.name}")
        logger.info("=" * 60)
        
        # Step 1: Load historical data
        data = self._load_data(genome)
        if data is None or len(data) < cfg.MIN_BACKTEST_DAYS:
            logger.error(f"Insufficient data for {genome.symbols[0]}")
            return {'error': 'Insufficient data', 'passed': False}
        
        # Step 2: Run basic backtest
        logger.info(f"Running backtest on {len(data)} bars...")
        backtest_results = self._run_backtest(genome, data)
        
        if backtest_results.get('total_trades', 0) < cfg.MIN_BACKTEST_TRADES:
            logger.warning(f"Insufficient trades: {backtest_results.get('total_trades', 0)}")
            return {'error': 'Insufficient trades', 'passed': False}
        
        # Step 3: Extract trade-level data for MC
        trade_returns = backtest_results.get('trade_returns', [])
        
        # Step 4: Run robustness tests
        if validate:
            logger.info("Running robustness validation...")
            
            # Create backtest wrapper for robustness tests
            def backtest_wrapper(data_subset, params=None):
                return self._run_backtest(genome, data_subset)
            
            robustness_results = self.robustness_tester.run_full_validation(
                backtest_func=backtest_wrapper,
                data=data,
                trade_returns=trade_returns
            )
            
            backtest_results['robustness'] = robustness_results
            backtest_results['passed'] = robustness_results['overall_passed']
        else:
            backtest_results['passed'] = (
                backtest_results.get('sharpe', 0) >= cfg.MIN_STRATEGY_SHARPE and
                backtest_results.get('win_rate', 0) >= cfg.MIN_WIN_RATE
            )
        
        # Step 5: Update registry
        if update_registry:
            self._update_registry(genome.id, backtest_results)
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"BACKTEST COMPLETE")
        logger.info(f"Sharpe: {backtest_results.get('sharpe', 0):.2f}")
        logger.info(f"Win Rate: {backtest_results.get('win_rate', 0)*100:.1f}%")  
        logger.info(f"Total Trades: {backtest_results.get('total_trades', 0)}")
        logger.info(f"Result: {'✅ PASSED' if backtest_results['passed'] else '❌ FAILED'}")
        logger.info("=" * 60)
        
        return backtest_results
    
    def _load_data(self, genome: StrategyGenome) -> Optional[pd.DataFrame]:
        """Load historical data for backtesting."""
        symbol = genome.symbols[0] if genome.symbols else "GOLD"
        tf = self.tf_map.get(genome.timeframe, mt5.TIMEFRAME_H1)
        
        # Calculate bars needed (1 year minimum)
        bars_per_day = {
            'M1': 1440, 'M5': 288, 'M15': 96, 'M30': 48,
            'H1': 24, 'H4': 6, 'D1': 1
        }
        bars_needed = cfg.MIN_BACKTEST_DAYS * bars_per_day.get(genome.timeframe, 24)
        bars_needed = min(bars_needed, 50000)  # Cap at 50k bars
        
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return None
        
        # Check if symbol exists and is available
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.warning(f"Symbol {symbol} not found in MT5. Available symbols: GOLD, SILVER, EURUSD, GBPUSD, USDJPY, AUDUSD")
            mt5.shutdown()
            return None
        
        # Enable symbol if not already
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.warning(f"Failed to enable symbol {symbol}")
                mt5.shutdown()
                return None
        
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, int(bars_needed))
        mt5.shutdown()
        
        if rates is None or len(rates) == 0:
            logger.warning(f"No data available for {symbol} on {genome.timeframe}. Try GOLD, SILVER, EURUSD, or GBPUSD.")
            return None
        
        if len(rates) < bars_needed * 0.5:  # At least 50% of requested data
            logger.warning(f"Insufficient data for {symbol}: got {len(rates)} bars, need ~{int(bars_needed)}")
            logger.info(f"Tip: Use symbols with more historical data like GOLD or EURUSD")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        logger.info(f"Loaded {len(df)} bars ({df.index[0]} to {df.index[-1]})")
        
        return df
    
    def _run_backtest(self, genome: StrategyGenome, data: pd.DataFrame) -> Dict:
        """
        Execute backtest logic based on genome rules.
        
        This is a simplified vectorized backtest. For production, integrate
        with your existing backtest engine.
        """
        # Calculate indicators
        df = data.copy()
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # Add indicators based on genome
        for indicator_name, params in genome.indicators.items():
            if indicator_name == "RSI" and TALIB_AVAILABLE:
                period = params.get('period', 14)
                df['RSI'] = talib.RSI(close, timeperiod=period)
            
            elif indicator_name == "EMA_fast" and TALIB_AVAILABLE:
                period = params.get('period', 9)
                df['EMA_fast'] = talib.EMA(close, timeperiod=period)
            
            elif indicator_name == "EMA_slow" and TALIB_AVAILABLE:
                period = params.get('period', 21)
                df['EMA_slow'] = talib.EMA(close, timeperiod=period)
            
            elif indicator_name == "BB" and TALIB_AVAILABLE:
                period = params.get('period', 20)
                std = params.get('std', 2.0)
                upper, middle, lower = talib.BBANDS(close, timeperiod=period, 
                                                     nbdevup=std, nbdevdn=std)
                df['BB_upper'] = upper
                df['BB_middle'] = middle
                df['BB_lower'] = lower
            
            elif indicator_name == "ATR" and TALIB_AVAILABLE:
                period = params.get('period', 14)
                df['ATR'] = talib.ATR(high, low, close, timeperiod=period)

            elif indicator_name == "ADX" and TALIB_AVAILABLE:
                period = params.get('period', 14)
                df['ADX'] = talib.ADX(high, low, close, timeperiod=period)

            elif indicator_name == "MACD" and TALIB_AVAILABLE:
                fast = params.get('fast', 12)
                slow = params.get('slow', 26)
                signal = params.get('signal', 9)
                macd, macdsignal, macdhist = talib.MACD(close, fastperiod=fast, slowperiod=slow, signalperiod=signal)
                df['MACD'] = macd
                df['MACD_signal'] = macdsignal
                df['MACD_hist'] = macdhist
                df['MACD_hist_prev'] = df['MACD_hist'].shift(1)

            elif indicator_name == "Volume":
                ma_period = params.get('ma_period', 20)
                df['volume_ma'] = df['tick_volume'].rolling(window=ma_period).mean()

            elif indicator_name == "OBV" and TALIB_AVAILABLE:
                df['OBV'] = talib.OBV(close, df['tick_volume'].values.astype(float))

            elif indicator_name == "VWAP":
                v = df['tick_volume'].values.astype(float)
                p = (high + low + close) / 3
                df['VWAP'] = (p * v).cumsum() / v.cumsum()

            elif indicator_name == "KALMAN":
                pv = params.get('process_variance', 0.0001)
                mv = params.get('measurement_variance', 0.005)
                # Quick Kalman implementation
                posteri_estimate = close[0]
                posteri_error_estimate = 1.0
                kalman_values = []
                for z in close:
                    priori_estimate = posteri_estimate
                    priori_error_estimate = posteri_error_estimate + pv
                    gain = priori_error_estimate / (priori_error_estimate + mv)
                    posteri_estimate = priori_estimate + gain * (z - priori_estimate)
                    posteri_error_estimate = (1 - gain) * priori_error_estimate
                    kalman_values.append(posteri_estimate)
                df['KALMAN'] = kalman_values

            elif indicator_name == "Regime":
                # Simulated volatility regime
                period = params.get('period', 100)
                df['ATR_long'] = talib.ATR(high, low, close, timeperiod=period) if TALIB_AVAILABLE else df['close'].rolling(10).std()
                df['ATR_short'] = talib.ATR(high, low, close, timeperiod=14) if TALIB_AVAILABLE else df['close'].rolling(5).std()
                df['Regime_VolatilityRatio'] = df['ATR_short'] / df['ATR_long']
        
        # Generate signals based on entry rules
        # This is simplified - in production, parse genome.entry_rules properly
        signals = self._generate_signals(genome, df)
        
        # Simulate trades
        trades = self._simulate_trades(df, signals, genome)
        
        # Calculate metrics
        metrics = self._calculate_metrics(trades, df)
        
        return metrics
    
    def _generate_signals(self, genome: StrategyGenome, df: pd.DataFrame) -> pd.Series:
        """
        Generate buy signals based on genome rules.
        Simplified version - parse entry_rules for production.
        """
        # Default to 0 (No signal)
        signals = pd.Series(0, index=df.index)
        if genome.type == StrategyGenome.MEAN_REVERSION:
            if 'KALMAN' in df.columns and 'ATR' in df.columns:
                signals.loc[df['close'] < df['KALMAN'] - 2 * df['ATR']] = 1
                signals.loc[df['close'] > df['KALMAN'] + 2 * df['ATR']] = -1
            elif 'RSI' in df.columns:
                signals.loc[df['RSI'] < 30] = 1
                signals.loc[df['RSI'] > 70] = -1
            elif 'BB_lower' in df.columns:
                signals.loc[df['close'] < df['BB_lower']] = 1
                signals.loc[df['close'] > df['BB_upper']] = -1
        
        elif genome.type == StrategyGenome.TREND_FOLLOWING:
            if 'ADX' in df.columns:
                threshold = 25
                if 'EMA_fast' in df.columns and 'EMA_slow' in df.columns:
                    # In high ADX, follow trend
                    signals.loc[(df['ADX'] > threshold) & (df['EMA_fast'] > df['EMA_slow'])] = 1
                    signals.loc[(df['ADX'] > threshold) & (df['EMA_fast'] < df['EMA_slow'])] = -1
                    # In low ADX, maybe mean revert? (Simple addition)
                    if 'RSI' in df.columns:
                        signals.loc[(df['ADX'] <= threshold) & (df['RSI'] < 30)] = 1
                        signals.loc[(df['ADX'] <= threshold) & (df['RSI'] > 70)] = -1
            elif 'EMA_fast' in df.columns and 'EMA_slow' in df.columns:
                signals.loc[(df['EMA_fast'] > df['EMA_slow']) & (df['EMA_fast'].shift(1) <= df['EMA_slow'].shift(1))] = 1
                signals.loc[(df['EMA_fast'] < df['EMA_slow']) & (df['EMA_fast'].shift(1) >= df['EMA_slow'].shift(1))] = -1
        
        elif genome.type == StrategyGenome.BREAKOUT:
            if 'BB_upper' in df.columns:
                signals.loc[df['close'] > df['BB_upper']] = 1
                signals.loc[df['close'] < df['BB_lower']] = -1
            if 'volume_ma' in df.columns:
                signals = signals * (df['tick_volume'] > df['volume_ma'] * 1.5).astype(int)

        elif genome.type == StrategyGenome.SCALPING:
            if 'VWAP' in df.columns and 'tick_volume' in df.columns and 'volume_ma' in df.columns:
                # Order flow / VWAP imbalance
                signals.loc[(df['close'] < df['VWAP']) & (df['tick_volume'] > df['volume_ma'] * 2)] = 1
                signals.loc[(df['close'] > df['VWAP']) & (df['tick_volume'] > df['volume_ma'] * 2)] = -1
            elif 'MACD_hist' in df.columns:
                signals.loc[(df['MACD_hist'] > df['MACD_hist_prev']) & (df['MACD_hist_prev'] < 0)] = 1
                signals.loc[(df['MACD_hist'] < df['MACD_hist_prev']) & (df['MACD_hist_prev'] > 0)] = -1

        elif genome.type == StrategyGenome.MOMENTUM:
            mom = df['close'] - df['close'].shift(10)
            signals.loc[mom > 0] = 1
            signals.loc[mom < 0] = -1
        
        return signals
    
    def _simulate_trades(self, df: pd.DataFrame, signals: pd.Series, 
                        genome: StrategyGenome) -> pd.DataFrame:
        """
        Simulate trades based on bidirectional signals and realistic costs.
        """
        trades = []
        in_trade = False
        direction = 0 # 1 for Long, -1 for Short
        entry_price = 0
        entry_idx = 0
        
        symbol = genome.symbols[0] if genome.symbols else "DEFAULT"
        costs = cfg.TRANSACTION_COSTS.get(symbol, cfg.TRANSACTION_COSTS.get("EURUSD", {"spread": 0.0001}))
        spread = costs.get("spread", 0)
        
        # Get exit parameters
        tp_mult = genome.exit_rules.get('tp_mult', 2.0)
        sl_atr_mult = genome.exit_rules.get('sl_atr', 1.5)
        
        for i in range(1, len(df)):
            if in_trade:
                curr_price = df['close'].iloc[i]
                atr = df['ATR'].iloc[entry_idx] if 'ATR' in df.columns else (df['close'].iloc[i] * 0.001)
                
                # Dynamic SL/TP based on entry ATR
                sl_dist = sl_atr_mult * atr
                tp_dist = tp_mult * sl_dist
                
                if direction == 1: # LONG
                    sl = entry_price - sl_dist
                    tp = entry_price + tp_dist
                    
                    if df['low'].iloc[i] <= sl:
                        exit_price = sl
                        in_trade = False
                    elif df['high'].iloc[i] >= tp:
                        exit_price = tp
                        in_trade = False
                else: # SHORT
                    sl = entry_price + sl_dist
                    tp = entry_price - tp_dist
                    
                    if df['high'].iloc[i] >= sl:
                        exit_price = sl
                        in_trade = False
                    elif df['low'].iloc[i] <= tp:
                        exit_price = tp
                        in_trade = False
                
                if not in_trade:
                    # Apply costs on exit
                    pnl = (exit_price - entry_price) * direction
                    pnl -= spread # Cost of spread
                    pnl_pct = (pnl / entry_price) * 100
                    
                    trades.append({
                        'entry_time': df.index[entry_idx],
                        'entry_price': entry_price,
                        'exit_time': df.index[i],
                        'exit_price': exit_price,
                        'direction': "BUY" if direction == 1 else "SELL",
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'bars_held': i - entry_idx,
                        'hit_tp': (exit_price == tp)
                    })
            
            else:
                # Entry Signal
                if signals.iloc[i] != 0:
                    direction = signals.iloc[i]
                    entry_price = df['close'].iloc[i]
                    # Apply entry costs
                    entry_price += (spread / 2) * direction 
                    entry_idx = i
                    in_trade = True
        
        return pd.DataFrame(trades)
    
    def _calculate_metrics(self, trades: pd.DataFrame, data: pd.DataFrame) -> Dict:
        """Calculate performance metrics from trades."""
        if len(trades) == 0:
            return {
                'total_trades': 0,
                'sharpe': 0,
                'win_rate': 0,
                'total_return': 0,
                'max_drawdown': 0,
                'profit_factor': 0
            }
        
        # Basic stats
        total_trades = len(trades)
        wins = trades[trades['pnl'] > 0]
        losses = trades[trades['pnl'] <= 0]
        
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        # Returns
        total_return = trades['pnl'].sum()
        avg_trade = trades['pnl'].mean()
        
        # Calculate avg trade in pips (approximate)
        avg_pnl_pct = trades['pnl_pct'].mean()
        
        # Profit factor
        total_wins = wins['pnl'].sum() if len(wins) > 0 else 0
        total_losses = abs(losses['pnl'].sum()) if len(losses) > 0 else 1
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Sharpe (from trade returns)
        returns = trades['pnl_pct'].values
        sharpe = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Drawdown (original calculation)
        cumulative = trades['pnl'].cumsum()
        running_max = cumulative.expanding().max()
        drawdown = ((cumulative - running_max) / running_max.abs()).min() if len(running_max) > 0 else 0
        max_drawdown = abs(drawdown)
        
        return {
            'total_trades': int(total_trades),
            'sharpe': float(sharpe),
            'win_rate': float(win_rate),
            'total_return': float(total_return),
            'avg_trade_pct': float(avg_pnl_pct),
            'profit_factor': float(profit_factor),
            'max_drawdown': float(max_drawdown),
            'trade_returns': returns.tolist()
        }
    
    def _update_registry(self, strategy_id: str, results: Dict):
        """Update strategy registry with backtest results."""
        metrics = {
            'sharpe': results.get('sharpe', 0),
            'calmar': results.get('calmar', 0),
            'sortino': results.get('sortino', 0),
            'win_rate': results.get('win_rate', 0),
            'profit_factor': results.get('profit_factor', 0),
            'max_drawdown': results.get('max_drawdown', 0),
            'total_trades': results.get('total_trades', 0),
            'avg_trade': results.get('avg_trade', 0),
            'passed': results.get('passed', False)
        }
        
        # Add robustness flags if available
        if 'robustness' in results:
            rob = results['robustness']
            metrics['oos_sharpe'] = rob.get('oos', {}).get('out_sample', {}).get('sharpe', 0)
            metrics['monte_carlo_stable'] = rob.get('monte_carlo', {}).get('stable', False)
            metrics['walkforward_consistent'] = rob.get('walk_forward', {}).get('consistent', False)
        
        self.registry.update_backtest_results(strategy_id, metrics)
        logger.info(f"Updated registry for strategy {strategy_id[:8]}...")


if __name__ == "__main__":
    from titan_system.factory.strategy_genome import StrategyTemplates
    
    print("=" * 60)
    print("STRATEGY BACKTEST RUNNER - Demo")
    print("=" * 60)
    
    # Create test strategy
    genome = StrategyTemplates.rsi_mean_reversion("GOLD", "H1")
    print(f"\nTesting: {genome.name}")
    
    # Run backtest
    runner = StrategyBacktestRunner()
    results = runner.backtest_genome(genome, validate=False, update_registry=False)
    
    if 'error' not in results:
        print(f"\n✅ Backtest Complete:")
        print(f"   Sharpe: {results['sharpe']:.2f}")
        print(f"   Win Rate: {results['win_rate']*100:.1f}%")
        print(f"   Trades: {results['total_trades']}")
        print(f"   Passed: {results['passed']}")
    else:
        print(f"\n❌ Backtest Failed: {results['error']}")
