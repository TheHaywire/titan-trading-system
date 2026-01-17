"""
INSTITUTIONAL BACKTESTING ENGINE
=================================
Tests all strategies across all symbols and timeframes with rigorous metrics.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from datetime import datetime
import json

# Import strategy library
from strategy_library import get_all_strategies

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InstitutionalBacktester:
    def __init__(self, data_dir="data/institutional"):
        self.data_dir = Path(data_dir)
        self.results = []
        
    def load_dataset(self, filepath):
        """Load a single CSV dataset."""
        df = pd.read_csv(filepath)
        df['time'] = pd.to_datetime(df['time'])
        return df
    
    def run_strategy(self, strategy, df, symbol, timeframe):
        """
        Run a single strategy on a dataset and return metrics.
        """
        # Generate signals
        df_signals = strategy.generate_signals(df)
        
        # Simulate trades
        trades = self.simulate_trades(df_signals, strategy)
        
        if len(trades) == 0:
            return None
        
        # Calculate metrics
        metrics = self.calculate_metrics(trades, df_signals)
        metrics['strategy'] = strategy.get_name()
        metrics['symbol'] = symbol
        metrics['timeframe'] = timeframe
        metrics['total_trades'] = len(trades)
        
        return metrics
    
    def simulate_trades(self, df, strategy):
        """Simulate trade execution with ATR-based stops."""
        trades = []
        in_position = False
        entry_idx = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Skip if no ATR data
            if pd.isna(row.get('ATR')):
                continue
            
            # Entry logic
            if not in_position and row['signal'] == 1:
                entry_price = row['close']
                atr = row['ATR']
                
                # ATR-based stops
                stop_loss = entry_price - (strategy.stop_loss_atr * atr)
                take_profit = entry_price + (strategy.take_profit_atr * atr)
                
                in_position = True
                entry_idx = i
                entry_time = row['time']
                continue
            
            # Exit logic (if in position)
            if in_position:
                # Check stop loss
                if row['low'] <= stop_loss:
                    pnl_pct = ((stop_loss - entry_price) / entry_price) * 100
                    trades.append({
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_price': stop_loss,
                        'exit_time': row['time'],
                        'pnl_pct': pnl_pct,
                        'outcome': 'loss',
                        'bars_held': i - entry_idx
                    })
                    in_position = False
                    continue
                
                # Check take profit
                if row['high'] >= take_profit:
                    pnl_pct = ((take_profit - entry_price) / entry_price) * 100
                    trades.append({
                        'entry_time': entry_time,
                        'entry_price': entry_price,
                        'exit_price': take_profit,
                        'exit_time': row['time'],
                        'pnl_pct': pnl_pct,
                        'outcome': 'win',
                        'bars_held': i - entry_idx
                    })
                    in_position = False
                    continue
        
        return trades
    
    def calculate_metrics(self, trades, df):
        """Calculate comprehensive performance metrics."""
        trades_df = pd.DataFrame(trades)
        
        # Basic metrics
        wins = trades_df[trades_df['outcome'] == 'win']
        losses = trades_df[trades_df['outcome'] == 'loss']
        
        win_rate = (len(wins) / len(trades_df)) * 100 if len(trades_df) > 0 else 0
        avg_win = wins['pnl_pct'].mean() if len(wins) > 0 else 0
        avg_loss = losses['pnl_pct'].mean() if len(losses) > 0 else 0
        
        # Profit factor
        gross_profit = wins['pnl_pct'].sum() if len(wins) > 0 else 0
        gross_loss = abs(losses['pnl_pct'].sum()) if len(losses) > 0 else 0.001
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Expectancy
        expectancy = (win_rate/100 * avg_win) + ((100-win_rate)/100 * avg_loss)
        
        # Returns for risk-adjusted metrics
        returns = trades_df['pnl_pct'].values
        
        # Sharpe Ratio (annualized)
        if len(returns) > 1 and returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)  # Assumes daily
        else:
            sharpe = 0
        
        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 1 and downside_returns.std() > 0:
            sortino = (returns.mean() / downside_returns.std()) * np.sqrt(252)
        else:
            sortino = 0
        
        # Max Drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_dd = drawdown.min() if len(drawdown) > 0 else 0
        
        # Calmar Ratio
        total_return = returns.sum()
        calmar = total_return / abs(max_dd) if max_dd != 0 else 0
        
        return {
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'expectancy': round(expectancy, 3),
            'sharpe_ratio': round(sharpe, 2),
            'sortino_ratio': round(sortino, 2),
            'max_drawdown': round(max_dd, 2),
            'calmar_ratio': round(calmar, 2),
            'total_return': round(total_return, 2)
        }
    
    def run_comprehensive_backtest(self):
        """Run all strategies on all datasets."""
        # Get all CSV files
        csv_files = list(self.data_dir.glob("*.csv"))
        logger.info(f"Found {len(csv_files)} datasets")
        
        # Get all strategies
        strategies = get_all_strategies()
        logger.info(f"Testing {len(strategies)} strategies")
        
        total_tests = len(csv_files) * len(strategies)
        logger.info(f"\n{'='*60}")
        logger.info(f"RUNNING {total_tests} BACKTEST COMBINATIONS")
        logger.info(f"{'='*60}\n")
        
        completed = 0
        
        for csv_file in csv_files:
            # Parse symbol and timeframe from filename
            parts = csv_file.stem.split('_')
            symbol = '_'.join(parts[:-1])
            timeframe = parts[-1]
            
            logger.info(f"\n[{symbol} - {timeframe}]")
            
            # Load data
            df = self.load_dataset(csv_file)
            logger.info(f"  Data: {len(df)} bars from {df['time'].min()} to {df['time'].max()}")
            
            # Test each strategy
            for strategy in strategies:
                completed += 1
                progress = (completed / total_tests) * 100
                
                try:
                    metrics = self.run_strategy(strategy, df, symbol, timeframe)
                    
                    if metrics:
                        self.results.append(metrics)
                        logger.info(f"  [{progress:5.1f}%] {strategy.get_name():25} | "
                                  f"Trades: {metrics['total_trades']:3} | "
                                  f"Win%: {metrics['win_rate']:5.1f} | "
                                  f"Sharpe: {metrics['sharpe_ratio']:5.2f}")
                    else:
                        logger.warning(f"  [{progress:5.1f}%] {strategy.get_name():25} | No trades")
                        
                except Exception as e:
                    logger.error(f"  [{progress:5.1f}%] {strategy.get_name():25} | ERROR: {e}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ BACKTEST COMPLETE: {len(self.results)} valid results")
        logger.info(f"{'='*60}\n")
    
    def save_results(self, filename="institutional_backtest_results.csv"):
        """Save all results to CSV."""
        if not self.results:
            logger.warning("No results to save")
            return
        
        df = pd.DataFrame(self.results)
        output_path = self.data_dir / filename
        df.to_csv(output_path, index=False)
        logger.info(f"Results saved to: {output_path}")
        return output_path
    
    def get_top_strategies(self, n=10, metric='sharpe_ratio'):
        """Get top N strategies by specified metric."""
        if not self.results:
            return None
        
        df = pd.DataFrame(self.results)
        top = df.nlargest(n, metric)
        return top

if __name__ == "__main__":
    logger.info("🏦 INSTITUTIONAL BACKTESTING ENGINE")
    logger.info(f"Started at: {datetime.now()}\n")
    
    # Initialize backtester
    backtester = InstitutionalBacktester()
    
    # Run comprehensive backtest
    backtester.run_comprehensive_backtest()
    
    # Save results
    results_file = backtester.save_results()
    
    # Show top performers
    logger.info("\n🏆 TOP 10 STRATEGIES (by Sharpe Ratio):")
    logger.info("="*100)
    top = backtester.get_top_strategies(10, 'sharpe_ratio')
    
    if top is not None:
        print(top[['strategy', 'symbol', 'timeframe', 'total_trades', 
                   'win_rate', 'sharpe_ratio', 'profit_factor']].to_string(index=False))
    
    logger.info(f"\n✅ Complete at: {datetime.now()}")
