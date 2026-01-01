"""
BACKTEST LOGGING & DOCUMENTATION SYSTEM
Tracks all backtests, parameters, results, and trades for future reference
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import json
import hashlib

class BacktestLogger:
    """
    Comprehensive backtest logging system
    
    Tracks:
    - Every backtest run with unique ID
    - Strategy parameters
    - Data range and quality
    - Performance metrics
    - Individual trades
    - Costs and slippage used
    - Statistical validation results
    """
    
    def __init__(self, db_path='data/backtest_history.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self._initialize_schema()
        
    def _initialize_schema(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Backtests table - main record of each test
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtests (
                backtest_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                strategy_name TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                style TEXT,
                
                -- Data info
                data_start TEXT,
                data_end TEXT,
                bars INTEGER,
                years REAL,
                
                -- Parameters (JSON)
                parameters TEXT,
                
                -- Costs
                commission REAL,
                slippage REAL,
                initial_capital REAL,
                
                -- Results
                total_return REAL,
                sharpe_ratio REAL,
                sortino_ratio REAL,
                max_drawdown REAL,
                win_rate REAL,
                total_trades INTEGER,
                avg_trade_return REAL,
                profit_factor REAL,
                expectancy REAL,
                calmar_ratio REAL,
                
                -- Benchmark comparison
                benchmark_return REAL,
                alpha REAL,
                
                -- Statistical validation
                p_value REAL,
                is_significant INTEGER,
                confidence_level REAL,
                
                -- Monte Carlo (JSON)
                monte_carlo TEXT,
                
                -- Assessment
                verdict TEXT,
                notes TEXT
            )
        ''')
        
        # Individual trades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backtest_trades (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                entry_time TEXT,
                exit_time TEXT,
                entry_price REAL,
                exit_price REAL,
                side TEXT,
                size REAL,
                pnl REAL,
                pnl_pct REAL,
                duration_hours REAL,
                FOREIGN KEY (backtest_id) REFERENCES backtests(backtest_id)
            )
        ''')
        
        # Daily equity curve
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS equity_curves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backtest_id TEXT NOT NULL,
                date TEXT,
                equity REAL,
                drawdown REAL,
                FOREIGN KEY (backtest_id) REFERENCES backtests(backtest_id)
            )
        ''')
        
        # Session runs - group backtests by session
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                description TEXT,
                total_backtests INTEGER,
                best_sharpe REAL,
                best_strategy TEXT
            )
        ''')
        
        self.conn.commit()
        
    def generate_backtest_id(self, strategy, symbol, timeframe, params):
        """Generate unique ID for backtest"""
        unique_string = f"{strategy}_{symbol}_{timeframe}_{json.dumps(params)}_{datetime.now().isoformat()}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:12]
    
    def log_backtest(self, 
                     strategy_name,
                     symbol,
                     timeframe,
                     style=None,
                     
                     # Data info
                     data_start=None,
                     data_end=None,
                     bars=None,
                     years=None,
                     
                     # Parameters
                     parameters=None,
                     
                     # Costs
                     commission=0.001,
                     slippage=0.001,
                     initial_capital=10000,
                     
                     # Results
                     total_return=None,
                     sharpe_ratio=None,
                     sortino_ratio=None,
                     max_drawdown=None,
                     win_rate=None,
                     total_trades=None,
                     avg_trade_return=None,
                     profit_factor=None,
                     expectancy=None,
                     calmar_ratio=None,
                     
                     # Benchmark
                     benchmark_return=None,
                     alpha=None,
                     
                     # Stats
                     p_value=None,
                     is_significant=None,
                     confidence_level=None,
                     monte_carlo=None,
                     
                     # Assessment
                     verdict=None,
                     notes=None):
        """Log a complete backtest result"""
        
        backtest_id = self.generate_backtest_id(strategy_name, symbol, timeframe, parameters or {})
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO backtests VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
        ''', (
            backtest_id,
            datetime.now().isoformat(),
            strategy_name,
            symbol,
            timeframe,
            style,
            str(data_start) if data_start else None,
            str(data_end) if data_end else None,
            bars,
            years,
            json.dumps(parameters) if parameters else None,
            commission,
            slippage,
            initial_capital,
            total_return,
            sharpe_ratio,
            sortino_ratio,
            max_drawdown,
            win_rate,
            total_trades,
            avg_trade_return,
            profit_factor,
            expectancy,
            calmar_ratio,
            benchmark_return,
            alpha,
            p_value,
            1 if is_significant else 0,
            confidence_level,
            json.dumps(monte_carlo) if monte_carlo else None,
            verdict,
            notes
        ))
        
        self.conn.commit()
        return backtest_id
    
    def log_trades(self, backtest_id, trades_df):
        """Log individual trades for a backtest"""
        cursor = self.conn.cursor()
        
        for _, trade in trades_df.iterrows():
            cursor.execute('''
                INSERT INTO backtest_trades 
                (backtest_id, entry_time, exit_time, entry_price, exit_price, side, size, pnl, pnl_pct, duration_hours)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                backtest_id,
                str(trade.get('entry_time')),
                str(trade.get('exit_time')),
                trade.get('entry_price'),
                trade.get('exit_price'),
                trade.get('side', 'LONG'),
                trade.get('size', 1),
                trade.get('pnl'),
                trade.get('pnl_pct'),
                trade.get('duration_hours')
            ))
        
        self.conn.commit()
    
    def log_equity_curve(self, backtest_id, equity_df):
        """Log daily equity curve"""
        cursor = self.conn.cursor()
        
        for date, row in equity_df.iterrows():
            cursor.execute('''
                INSERT INTO equity_curves (backtest_id, date, equity, drawdown)
                VALUES (?, ?, ?, ?)
            ''', (backtest_id, str(date), row.get('equity'), row.get('drawdown')))
        
        self.conn.commit()
    
    def get_all_backtests(self, limit=1000):
        """Get all backtest results"""
        return pd.read_sql_query(
            f'SELECT * FROM backtests ORDER BY timestamp DESC LIMIT {limit}',
            self.conn
        )
    
    def get_best_strategies(self, min_trades=10, min_sharpe=0.5):
        """Get strategies that passed thresholds"""
        return pd.read_sql_query('''
            SELECT strategy_name, symbol, timeframe, sharpe_ratio, total_return, 
                   win_rate, total_trades, max_drawdown, verdict
            FROM backtests 
            WHERE total_trades >= ? AND sharpe_ratio >= ?
            ORDER BY sharpe_ratio DESC
        ''', self.conn, params=(min_trades, min_sharpe))
    
    def get_backtest_summary(self):
        """Get summary statistics of all backtests"""
        cursor = self.conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM backtests')
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM backtests WHERE sharpe_ratio >= 1.0')
        strong_edge = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM backtests WHERE sharpe_ratio >= 0.5 AND sharpe_ratio < 1.0')
        weak_edge = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM backtests WHERE sharpe_ratio < 0.5')
        no_edge = cursor.fetchone()[0]
        
        cursor.execute('SELECT AVG(sharpe_ratio) FROM backtests')
        avg_sharpe = cursor.fetchone()[0]
        
        cursor.execute('SELECT strategy_name, symbol, timeframe, sharpe_ratio FROM backtests ORDER BY sharpe_ratio DESC LIMIT 1')
        best = cursor.fetchone()
        
        return {
            'total_backtests': total,
            'strong_edge': strong_edge,
            'weak_edge': weak_edge,
            'no_edge': no_edge,
            'avg_sharpe': round(avg_sharpe, 2) if avg_sharpe else 0,
            'best_strategy': best
        }
    
    def export_to_csv(self, filepath='data/backtest_history.csv'):
        """Export all backtests to CSV"""
        df = self.get_all_backtests(limit=10000)
        df.to_csv(filepath, index=False)
        return filepath
    
    def generate_report(self):
        """Generate markdown report of all backtests"""
        summary = self.get_backtest_summary()
        best = self.get_best_strategies(min_trades=5, min_sharpe=0.0)
        
        report = f"""# Backtest History Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| Total Backtests | {summary['total_backtests']} |
| Strong Edge (Sharpe >= 1.0) | {summary['strong_edge']} |
| Weak Edge (Sharpe 0.5-1.0) | {summary['weak_edge']} |
| No Edge (Sharpe < 0.5) | {summary['no_edge']} |
| Average Sharpe | {summary['avg_sharpe']} |

## Best Strategy
{summary['best_strategy'] if summary['best_strategy'] else 'No backtests yet'}

## All Results (Top 20)

| Strategy | Symbol | TF | Sharpe | Return | Win% | Trades | Verdict |
|----------|--------|-----|--------|--------|------|--------|---------|
"""
        for _, row in best.head(20).iterrows():
            report += f"| {row['strategy_name']} | {row['symbol']} | {row['timeframe']} | {row['sharpe_ratio']} | {row['total_return']}% | {row['win_rate']}% | {row['total_trades']} | {row['verdict']} |\n"
        
        return report
    
    def close(self):
        self.conn.close()


# Create global logger instance
logger = BacktestLogger()


def print_summary():
    """Print current backtest summary"""
    summary = logger.get_backtest_summary()
    
    print("\n=== BACKTEST DATABASE SUMMARY ===")
    print(f"Total Backtests Logged: {summary['total_backtests']}")
    print(f"Strong Edge (Sharpe >= 1.0): {summary['strong_edge']}")
    print(f"Weak Edge (Sharpe 0.5-1.0): {summary['weak_edge']}")
    print(f"No Edge (Sharpe < 0.5): {summary['no_edge']}")
    print(f"Average Sharpe: {summary['avg_sharpe']}")
    
    if summary['best_strategy']:
        print(f"\nBest Strategy: {summary['best_strategy']}")


if __name__ == "__main__":
    # Demo usage
    print("Backtest Logger initialized")
    print(f"Database: data/backtest_history.db")
    
    # Log a sample backtest
    backtest_id = logger.log_backtest(
        strategy_name="Demo Momentum",
        symbol="BTCUSD",
        timeframe="D1",
        style="Swing",
        data_start="2020-01-01",
        data_end="2024-12-31",
        bars=1000,
        years=5.0,
        parameters={'lookback': 252, 'threshold': 0.0},
        commission=0.001,
        slippage=0.001,
        initial_capital=10000,
        total_return=150.5,
        sharpe_ratio=1.12,
        max_drawdown=-32.5,
        win_rate=55.0,
        total_trades=25,
        verdict="DEPLOY",
        notes="Demo backtest entry"
    )
    
    print(f"\nLogged demo backtest: {backtest_id}")
    
    print_summary()
    
    # Export report
    report = logger.generate_report()
    with open('docs/BACKTEST_REPORT.md', 'w') as f:
        f.write(report)
    print("\nReport saved to: docs/BACKTEST_REPORT.md")
