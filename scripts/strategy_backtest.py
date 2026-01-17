"""
MT5 STRATEGY BACKTEST ENGINE
============================= 
Tests Finviz-style trading filters against historical MT5 data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StrategyBacktester:
    def __init__(self, csv_path):
        self.df = pd.read_csv(csv_path)
        self.df['time'] = pd.to_datetime(self.df['time'])
        self.trades = []
        
    def test_baseline_strategy(self):
        """
        Baseline: Simple breakout strategy WITHOUT Finviz filters.
        Entry: Price breaks 52-bar high
        Exit: ATR-based stop/target
        """
        logger.info("Testing BASELINE strategy (No Finviz filters)...")
        
        for i in range(100, len(self.df) - 10):
            row = self.df.iloc[i]
            
            # Entry Signal: New high
            if row['Near_52W_High'] == 1 and pd.notna(row['ATR']):
                entry_price = row['close']
                atr = row['ATR']
                
                # ATR-based stops
                sl = entry_price - (2 * atr)  # 2 ATR stop
                tp = entry_price + (3 * atr)  # 3 ATR target (1.5:1 R/R)
                
                outcome = self.simulate_trade(i, entry_price, sl, tp)
                outcome['strategy'] = 'Baseline'
                outcome['entry_condition'] = 'New_High'
                self.trades.append(outcome)
        
        return self.calculate_metrics('Baseline')
    
    def test_adrenaline_strategy(self):
        """
        Adrenaline Filter: Breakout + High Relative Volume
        Entry: Price breaks high AND Rel Vol > 1.5
        """
        logger.info("Testing ADRENALINE strategy (Rel Vol > 1.5)...")
        
        for i in range(100, len(self.df) - 10):
            row = self.df.iloc[i]
            
            # Entry Signal: New high + Volume confirmation
            if row['Near_52W_High'] == 1 and row['Rel_Volume'] > 1.5 and pd.notna(row['ATR']):
                entry_price = row['close']
                atr = row['ATR']
                
                sl = entry_price - (2 * atr)
                tp = entry_price + (3 * atr)
                
                outcome = self.simulate_trade(i, entry_price, sl, tp)
                outcome['strategy'] = 'Adrenaline'
                outcome['entry_condition'] = f"New_High+RelVol({row['Rel_Volume']:.2f})"
                self.trades.append(outcome)
        
        return self.calculate_metrics('Adrenaline')
    
    def test_rsi_oversold_strategy(self):
        """
        RSI Oversold Bounce: Buy when RSI < 30 in uptrend
        Entry: RSI < 30 AND Price above SMA200
        """
        logger.info("Testing RSI OVERSOLD strategy...")
        
        for i in range(100, len(self.df) - 10):
            row = self.df.iloc[i]
            
            # Entry Signal: Oversold in uptrend
            if row['RSI'] < 30 and row['close'] > row['SMA_200'] and pd.notna(row['ATR']):
                entry_price = row['close']
                atr = row['ATR']
                
                # Tighter stops for mean reversion
                sl = entry_price - (1.5 * atr)
                tp = entry_price + (2.5 * atr)
                
                outcome = self.simulate_trade(i, entry_price, sl, tp)
                outcome['strategy'] = 'RSI_Oversold'
                outcome['entry_condition'] = f"RSI({row['RSI']:.1f})<30"
                self.trades.append(outcome)
        
        return self.calculate_metrics('RSI_Oversold')
    
    def simulate_trade(self, entry_idx, entry_price, sl, tp):
        """
        Simulate trade execution and outcome.
        Returns: dict with trade result
        """
        # Look ahead 10 bars for outcome
        for j in range(entry_idx + 1, min(entry_idx + 11, len(self.df))):
            bar = self.df.iloc[j]
            
            # Check if SL hit
            if bar['low'] <= sl:
                return {
                    'entry_time': self.df.iloc[entry_idx]['time'],
                    'entry_price': entry_price,
                    'exit_price': sl,
                    'exit_time': bar['time'],
                    'pnl_pct': ((sl - entry_price) / entry_price) * 100,
                    'outcome': 'loss',
                    'bars_held': j - entry_idx
                }
            
            # Check if TP hit
            if bar['high'] >= tp:
                return {
                    'entry_time': self.df.iloc[entry_idx]['time'],
                    'entry_price': entry_price,
                    'exit_price': tp,
                    'exit_time': bar['time'],
                    'pnl_pct': ((tp - entry_price) / entry_price) * 100,
                    'outcome': 'win',
                    'bars_held': j - entry_idx
                }
        
        # Neither hit - close at market after 10 bars
        final_bar = self.df.iloc[min(entry_idx + 10, len(self.df) - 1)]
        exit_price = final_bar['close']
        return {
            'entry_time': self.df.iloc[entry_idx]['time'],
            'entry_price': entry_price,
            'exit_price': exit_price,
            'exit_time': final_bar['time'],
            'pnl_pct': ((exit_price - entry_price) / entry_price) * 100,
            'outcome': 'timeout',
            'bars_held': 10
        }
    
    def calculate_metrics(self, strategy_name):
        """Calculate performance metrics for a strategy."""
        strategy_trades = [t for t in self.trades if t['strategy'] == strategy_name]
        
        if not strategy_trades:
            return {
                'strategy': strategy_name,
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'total_pnl': 0
            }
        
        wins = [t for t in strategy_trades if t['outcome'] == 'win']
        losses = [t for t in strategy_trades if t['outcome'] == 'loss']
        
        win_rate = (len(wins) / len(strategy_trades)) * 100 if strategy_trades else 0
        avg_win = np.mean([t['pnl_pct'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['pnl_pct'] for t in losses]) if losses else 0
        total_pnl = sum([t['pnl_pct'] for t in strategy_trades])
        
        gross_profit = sum([t['pnl_pct'] for t in wins]) if wins else 0
        gross_loss = abs(sum([t['pnl_pct'] for t in losses])) if losses else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        return {
            'strategy': strategy_name,
            'total_trades': len(strategy_trades),
            'win_rate': round(win_rate, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(profit_factor, 2),
            'total_pnl': round(total_pnl, 2)
        }

if __name__ == "__main__":
    # Find all backtest CSV files
    data_dir = Path("data")
    csv_files = list(data_dir.glob("backtest_*_H1.csv"))
    
    if not csv_files:
        logger.error("No backtest data files found. Run backtest_data_fetcher.py first.")
    else:
        logger.info(f"Found {len(csv_files)} backtest files")
        
        all_results = []
        
        for csv_file in csv_files[:3]:  # Test first 3 symbols
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing: {csv_file.name}")
            logger.info(f"{'='*60}")
            
            backtester = StrategyBacktester(csv_file)
            
            # Run all strategies
            baseline_metrics = backtester.test_baseline_strategy()
            adrenaline_metrics = backtester.test_adrenaline_strategy()
            rsi_metrics = backtester.test_rsi_oversold_strategy()
            
            # Print results
            print(f"\n📊 RESULTS FOR {csv_file.stem}")
            print("-" * 60)
            for metrics in [baseline_metrics, adrenaline_metrics, rsi_metrics]:
                print(f"{metrics['strategy']:15} | Trades: {metrics['total_trades']:3} | Win%: {metrics['win_rate']:5.1f}% | "
                      f"Avg Win: +{metrics['avg_win']:.2f}% | Avg Loss: {metrics['avg_loss']:.2f}% | PF: {metrics['profit_factor']:.2f}")
            
            all_results.extend([baseline_metrics, adrenaline_metrics, rsi_metrics])
        
        # Save aggregate results
        results_df = pd.DataFrame(all_results)
        results_df.to_csv("data/backtest_results.csv", index=False)
        logger.info("\n✅ Backtest complete. Results saved to data/backtest_results.csv")
