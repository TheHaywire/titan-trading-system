"""
Import all existing backtest results into the logging database
"""

import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
from titan_system.analytics.backtest_logger import BacktestLogger

logger = BacktestLogger()

def import_vectorbt_results():
    """Import vectorbt daily backtest results"""
    try:
        df = pd.read_csv('data/vectorbt_backtest_results.csv')
        
        for _, row in df.iterrows():
            logger.log_backtest(
                strategy_name=row['strategy'],
                symbol=row['symbol'],
                timeframe='D1',
                style='Position',
                bars=2000,
                years=6.0,
                commission=0.001,
                slippage=0.001,
                initial_capital=10000,
                total_return=row['total_return'],
                sharpe_ratio=row['sharpe'],
                sortino_ratio=row.get('sortino', None),
                max_drawdown=row['max_dd'],
                win_rate=row['win_rate'],
                total_trades=row['trades'],
                benchmark_return=row['benchmark'],
                verdict='DEPLOY' if row['sharpe'] >= 1.0 else 'WEAK' if row['sharpe'] >= 0.5 else 'SKIP',
                notes='Imported from vectorbt daily backtest'
            )
        
        print(f"Imported {len(df)} vectorbt daily results")
    except Exception as e:
        print(f"Error importing vectorbt results: {e}")

def import_scalping_results():
    """Import scalping/intraday/swing results"""
    try:
        df = pd.read_csv('data/scalping_intraday_swing_results.csv')
        
        for _, row in df.iterrows():
            logger.log_backtest(
                strategy_name=row['strategy'],
                symbol=row['symbol'],
                timeframe=row['timeframe'],
                style=row['style'],
                commission=0.0005 if row['timeframe'] == 'M15' else 0.0003 if row['timeframe'] == 'H1' else 0.0002,
                slippage=0.0002 if row['timeframe'] == 'M15' else 0.0001,
                initial_capital=10000,
                total_return=row['total_return'],
                sharpe_ratio=row['sharpe'],
                max_drawdown=row['max_dd'],
                win_rate=row['win_rate'],
                total_trades=row['trades'],
                benchmark_return=row['benchmark'],
                verdict='DEPLOY' if row['sharpe'] >= 1.0 else 'WEAK' if row['sharpe'] >= 0.5 else 'SKIP',
                notes=f"Imported from {row['style']} backtest on {row['timeframe']}"
            )
        
        print(f"Imported {len(df)} scalping/intraday/swing results")
    except Exception as e:
        print(f"Error importing scalping results: {e}")

def import_quick_backtest_results():
    """Import quick backtest results (without costs)"""
    try:
        df = pd.read_csv('data/backtest_results.csv')
        
        for _, row in df.iterrows():
            logger.log_backtest(
                strategy_name=row['Strategy'],
                symbol=row['Symbol'],
                timeframe='D1',
                style='Research',
                commission=0,  # No costs in quick test
                slippage=0,
                initial_capital=10000,
                total_return=float(row['Total_Return'].replace('%', '')),
                sharpe_ratio=row['Sharpe'],
                win_rate=float(row['Win_Rate'].replace('%', '')),
                total_trades=row['Trades'],
                verdict=row['Status'],
                notes='Quick backtest WITHOUT transaction costs - results inflated'
            )
        
        print(f"Imported {len(df)} quick backtest results")
    except Exception as e:
        print(f"Error importing quick results: {e}")


if __name__ == "__main__":
    print("Importing all backtest results into database...\n")
    
    import_vectorbt_results()
    import_scalping_results()
    import_quick_backtest_results()
    
    print("\n=== IMPORT COMPLETE ===\n")
    
    # Print summary
    summary = logger.get_backtest_summary()
    print(f"Total Backtests in Database: {summary['total_backtests']}")
    print(f"Strong Edge (Sharpe >= 1.0): {summary['strong_edge']}")
    print(f"Weak Edge (Sharpe 0.5-1.0): {summary['weak_edge']}")
    print(f"No Edge (Sharpe < 0.5): {summary['no_edge']}")
    print(f"Average Sharpe: {summary['avg_sharpe']}")
    
    # Generate updated report
    report = logger.generate_report()
    with open('docs/BACKTEST_REPORT.md', 'w') as f:
        f.write(report)
    print("\nReport updated: docs/BACKTEST_REPORT.md")
    
    # Export to CSV
    logger.export_to_csv('data/all_backtests.csv')
    print("CSV exported: data/all_backtests.csv")
