"""
Dual Momentum Strategy Backtest
Tests the strategy on historical data to validate profitability.

Symbols: Gold (XAUUSD), Bitcoin (BTCUSD), S&P 500 (US500)
Period: 2015-2024 (10 years)
Benchmark: Buy & Hold each asset
"""

import sys
import os
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from titan_system.strategies.dual_momentum import DualMomentumStrategy

class DualMomentumBacktest:
    """Backtesting engine for Dual Momentum strategy"""
    
    def __init__(self, initial_capital=10000, rebalance_frequency='monthly'):
        self.initial_capital = initial_capital
        self.rebalance_frequency = rebalance_frequency
        self.strategy = DualMomentumStrategy()
        
    def get_historical_data(self, symbol, start_date, end_date):
        """Fetch historical daily data from MT5"""
        
        rates = mt5.copy_rates_range(
            symbol,
            mt5.TIMEFRAME_D1,
            start_date,
            end_date
        )
        
        if rates is None or len(rates) == 0:
            print(f"❌ No data for {symbol}")
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    
    def backtest_symbol(self, symbol, start_date, end_date):
        """
        Backtest Dual Momentum on a single symbol
        
        Returns:
            dict: Performance metrics
        """
        print(f"\n{'='*60}")
        print(f"BACKTESTING: {symbol}")
        print(f"Period: {start_date.date()} to {end_date.date()}")
        print(f"{'='*60}")
        
        # Get data
        df = self.get_historical_data(symbol, start_date, end_date)
        if df is None:
            return None
        
        # Initialize tracking
        capital = self.initial_capital
        position = 0  # 0 = cash, 1 = long
        entry_price = 0
        trades = []
        equity_curve = []
        
        # Monthly rebalancing
        for month_start in pd.date_range(start_date, end_date, freq='MS'):
            # Need enough lookback data
            if (month_start - start_date).days < 260:
                equity_curve.append({'date': month_start, 'equity': capital})
                continue
            
            # Get data up to this month
            month_df = df[df.index < month_start].tail(300)
            
            if len(month_df) < 252:
                continue
            
            # Get signal
            result = self.strategy.analyze(symbol, month_df)
            signal = result['signal']
            
            current_price = month_df['close'].iloc[-1]
            
            # Execute logic
            if signal == 'BUY' and position == 0:
                # Enter long
                position = 1
                entry_price = current_price
                shares = capital / current_price
                print(f"  📈 BUY at {current_price:.2f} | Equity: ${capital:,.2f}")
                
            elif signal == 'SELL' and position == 1:
                # Exit long
                exit_price = current_price
                pnl = (exit_price - entry_price) * shares
                capital += pnl
                
                trade = {
                    'entry_date': entry_date,
                    'exit_date': month_start,
                    'entry_price': entry_price,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'return': (exit_price / entry_price) - 1
                }
                trades.append(trade)
                
                print(f"  📉 SELL at {exit_price:.2f} | P&L: ${pnl:,.2f} ({trade['return']:.2%})")
                
                position = 0
                entry_price = 0
            
            elif signal == 'BUY' and position == 1:
                # Hold
                entry_date = month_start  # Track latest signal
                
            # Track equity
            if position == 1:
                current_equity = capital + ((current_price - entry_price) * shares)
            else:
                current_equity = capital
                
            equity_curve.append({'date': month_start, 'equity': current_equity})
        
        # Close final position if still open
        if position == 1:
            final_price = df['close'].iloc[-1]
            pnl = (final_price - entry_price) * shares
            capital += pnl
            
            trades.append({
                'entry_date': entry_date,
                'exit_date': df.index[-1],
                'entry_price': entry_price,
                'exit_price': final_price,
                'pnl': pnl,
                'return': (final_price / entry_price) - 1
            })
        
        # Calculate metrics
        metrics = self.calculate_metrics(trades, equity_curve)
        
        # Buy & Hold comparison
        buy_hold_return = (df['close'].iloc[-1] / df['close'].iloc[252]) - 1  # Skip first year for fair comparison
        metrics['buy_hold_return'] = buy_hold_return
        
        return metrics
    
    def calculate_metrics(self, trades, equity_curve):
        """Calculate performance statistics"""
        
        if len(trades) == 0:
            return {
                'total_trades': 0,
                'total_return': 0,
                'cagr': 0,
                'sharpe': 0,
                'max_drawdown': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'expectancy': 0
            }
        
        df_trades = pd.DataFrame(trades)
        
        # Basic stats
        total_trades = len(trades)
        winners = df_trades[df_trades['pnl'] > 0]
        losers = df_trades[df_trades['pnl'] <= 0]
        
        win_rate = len(winners) / total_trades if total_trades > 0 else 0
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl'].mean() if len(losers) > 0 else 0
        
        total_pnl = df_trades['pnl'].sum()
        total_return = total_pnl / self.initial_capital
        
        # Profit factor
        gross_profit = winners['pnl'].sum() if len(winners) > 0 else 0
        gross_loss = abs(losers['pnl'].sum()) if len(losers) > 0 else 1
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Expectancy
        expectancy = df_trades['pnl'].mean()
        
        # Equity curve analysis
        df_equity = pd.DataFrame(equity_curve)
        df_equity.set_index('date', inplace=True)
        
        # CAGR
        years = (df_equity.index[-1] - df_equity.index[0]).days / 365.25
        cagr = ((df_equity['equity'].iloc[-1] / df_equity['equity'].iloc[0]) ** (1/years)) - 1 if years > 0 else 0
        
        # Sharpe Ratio
        returns = df_equity['equity'].pct_change().dropna()
        sharpe = (returns.mean() / returns.std()) * np.sqrt(12) if len(returns) > 0 else 0  # Annualized
        
        # Max Drawdown
        cummax = df_equity['equity'].cummax()
        drawdown = (df_equity['equity'] - cummax) / cummax
        max_drawdown = drawdown.min()
        
        return {
            'total_trades': total_trades,
            'total_return': total_return,
            'cagr': cagr,
            'sharpe': sharpe,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'expectancy': expectancy
        }
    
    def print_results(self, symbol, metrics):
        """Print formatted results"""
        
        if metrics is None:
            print(f"\n❌ {symbol}: No results")
            return
        
        print(f"\n{'='*60}")
        print(f"RESULTS: {symbol}")
        print(f"{'='*60}")
        print(f"Total Trades: {metrics['total_trades']}")
        print(f"Win Rate: {metrics['win_rate']:.1%}")
        print(f"\nReturns:")
        print(f"  Total Return: {metrics['total_return']:.1%}")
        print(f"  CAGR: {metrics['cagr']:.1%}")
        print(f"  Buy & Hold: {metrics.get('buy_hold_return', 0):.1%}")
        print(f"  Outperformance: {(metrics['total_return'] - metrics.get('buy_hold_return', 0)):.1%}")
        print(f"\nRisk Metrics:")
        print(f"  Sharpe Ratio: {metrics['sharpe']:.2f}")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.1%}")
        print(f"\nTrade Stats:")
        print(f"  Avg Win: ${metrics['avg_win']:,.2f}")
        print(f"  Avg Loss: ${metrics['avg_loss']:,.2f}")
        print(f"  Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"  Expectancy: ${metrics['expectancy']:,.2f}")
        
        # Assessment
        print(f"\n{'='*60}")
        if metrics['sharpe'] > 1.0 and metrics['expectancy'] > 50:
            print("✅ PROFITABLE - Strategy shows edge")
        elif metrics['sharpe'] > 0.5:
            print("⚠️  MARGINAL - Weak edge, needs optimization")
        else:
            print("❌ UNPROFITABLE - No statistical edge")
        print(f"{'='*60}\n")

def run_comprehensive_backtest():
    """Run backtest on multiple symbols"""
    
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return
    
    # Initialize backtest
    bt = DualMomentumBacktest(initial_capital=10000)
    
    # Test period
    start_date = datetime(2015, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    # Symbols to test
    symbols = [
        ("XAUUSD", "Gold"),
        ("BTCUSD", "Bitcoin"),
        ("US500", "S&P 500")
    ]
    
    results = {}
    
    for symbol, name in symbols:
        try:
            metrics = bt.backtest_symbol(symbol, start_date, end_date)
            if metrics:
                results[name] = metrics
                bt.print_results(name, metrics)
        except Exception as e:
            print(f"❌ Error testing {symbol}: {e}")
    
    # Summary comparison
    if results:
        print(f"\n{'='*60}")
        print("STRATEGY COMPARISON SUMMARY")
        print(f"{'='*60}")
        print(f"{'Symbol':<15} {'CAGR':<10} {'Sharpe':<10} {'Max DD':<10} {'Win Rate':<10}")
        print(f"{'-'*60}")
        
        for name, metrics in results.items():
            print(f"{name:<15} {metrics['cagr']:<10.1%} {metrics['sharpe']:<10.2f} "
                  f"{metrics['max_drawdown']:<10.1%} {metrics['win_rate']:<10.1%}")
        
        # Best performer
        best = max(results.items(), key=lambda x: x[1]['sharpe'])
        print(f"\n🏆 Best Performer: {best[0]} (Sharpe: {best[1]['sharpe']:.2f})")
    
    mt5.shutdown()
    
    return results

if __name__ == "__main__":
    print("="*60)
    print("DUAL MOMENTUM STRATEGY BACKTEST")
    print("Gary Antonacci's Research Implementation")
    print("="*60)
    print(f"Test Period: 2015-2024 (10 years)")
    print(f"Initial Capital: $10,000")
    print(f"Rebalance: Monthly")
    print("="*60)
    
    results = run_comprehensive_backtest()
    
    if results:
        print("\n✅ Backtest complete! Review results above.")
        print("\nNext Steps:")
        print("1. If Sharpe > 1.0 → Paper trade for 1 week")
        print("2. If Sharpe 0.5-1.0 → Optimize parameters")
        print("3. If Sharpe < 0.5 → Try different strategy")
    else:
        print("\n❌ Backtest failed. Check MT5 connection and symbol availability.")
