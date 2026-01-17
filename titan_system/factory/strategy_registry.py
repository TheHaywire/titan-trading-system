"""
STRATEGY REGISTRY - Strategy Lifecycle Database
===============================================
Tracks all strategies (candidates, backtested, paper, live, retired)
with performance metrics and lifecycle state.
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from .strategy_genome import StrategyGenome


class StrategyRegistry:
    """
    Central database for all strategies in the factory ecosystem.
    """
    
    # Strategy Status States
    STATUS_CANDIDATE = "candidate"      # Just generated, not yet tested
    STATUS_BACKTEST = "backtest"        # Currently being backtested
    STATUS_VALIDATED = "validated"      # Passed backtest, ready for paper
    STATUS_PAPER = "paper"              # Running in paper trading
    STATUS_LIVE = "live"                # Deployed to live trading
    STATUS_PAUSED = "paused"            # Temporarily disabled
    STATUS_RETIRED = "retired"          # Permanently shut down
    
    def __init__(self, db_path: str = "data/strategy_factory.db"):
        """
        Initialize registry database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create tables if not exist
        self._init_db()
    
    def _init_db(self):
        """Create database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main strategies table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategies (
            id TEXT PRIMARY KEY,
            genome JSON NOT NULL,
            status TEXT NOT NULL,
            magic_number INTEGER UNIQUE,
            created_at TIMESTAMP NOT NULL,
            deployed_at TIMESTAMP,
            retired_at TIMESTAMP,
            
            -- Backtest Metrics
            bt_sharpe REAL,
            bt_calmar REAL,
            bt_sortino REAL,
            bt_win_rate REAL,
            bt_profit_factor REAL,
            bt_max_drawdown REAL,
            bt_total_trades INTEGER,
            bt_avg_trade REAL,
            bt_oos_sharpe REAL,
            
            -- Robustness Scores
            monte_carlo_stable INTEGER DEFAULT 0,
            walkforward_consistent INTEGER DEFAULT 0,
            parameter_sensitive INTEGER DEFAULT 0,
            
            -- Live Performance
            live_pnl REAL DEFAULT 0,
            live_trades INTEGER DEFAULT 0,
            live_wins INTEGER DEFAULT 0,
            live_losses INTEGER DEFAULT 0,
            live_sharpe REAL,
            live_drawdown REAL DEFAULT 0,
            live_peak_equity REAL DEFAULT 0,
            consecutive_wins INTEGER DEFAULT 0,
            consecutive_losses INTEGER DEFAULT 0,
            last_trade_time TIMESTAMP,
            
            -- Lifecycle
            parent_id TEXT,
            generation INTEGER DEFAULT 0,
            retirement_reason TEXT,
            
            -- Metadata
            notes TEXT,
            tags TEXT,
            last_updated TIMESTAMP
        )
        """)
        
        # Performance history table (for tracking evolution)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            equity REAL,
            pnl_daily REAL,
            drawdown REAL,
            sharpe_30d REAL,
            trades_count INTEGER,
            FOREIGN KEY (strategy_id) REFERENCES strategies(id)
        )
        """)
        
        # Trade log (for correlation analysis)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id TEXT NOT NULL,
            symbol TEXT NOT NULL,
            direction TEXT NOT NULL,
            entry_time TIMESTAMP NOT NULL,
            exit_time TIMESTAMP,
            entry_price REAL,
            exit_price REAL,
            sl_price REAL,
            tp_price REAL,
            size REAL,
            pnl REAL,
            pnl_pct REAL,
            exit_reason TEXT,
            FOREIGN KEY (strategy_id) REFERENCES strategies(id)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON strategies(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_live_sharpe ON strategies(live_sharpe DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_bt_sharpe ON strategies(bt_sharpe DESC)")
        
        conn.commit()
        conn.close()
    
    # ==================== CREATE / UPDATE ====================
    
    def add_candidate(self, genome: StrategyGenome, notes: str = "") -> str:
        """
        Register a new strategy candidate.
        
        Args:
            genome: Strategy genome object
            notes: Optional notes about this strategy
        
        Returns:
            Strategy ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        INSERT INTO strategies (
            id, genome, status, created_at, parent_id, generation, notes, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            genome.id,
            genome.to_json(),
            self.STATUS_CANDIDATE,
            datetime.now().isoformat(),
            genome.genome.get("parent_id"),
            genome.genome.get("generation", 0),
            notes,
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return genome.id
    
    def update_backtest_results(self, strategy_id: str, metrics: Dict):
        """
        Update backtest metrics for a strategy.
        
        Args:
            strategy_id: Strategy ID
            metrics: Dictionary of backtest results
                {
                    'sharpe': 1.85,
                    'calmar': 2.1,
                    'win_rate': 0.58,
                    'profit_factor': 2.3,
                    'max_drawdown': 0.12,
                    'total_trades': 145,
                    'avg_trade': 23.50,
                    'oos_sharpe': 1.62,
                    'monte_carlo_stable': True,
                    'walkforward_consistent': True,
                    'parameter_sensitive': False
                }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        UPDATE strategies SET
            bt_sharpe = ?,
            bt_calmar = ?,
            bt_sortino = ?,
            bt_win_rate = ?,
            bt_profit_factor = ?,
            bt_max_drawdown = ?,
            bt_total_trades = ?,
            bt_avg_trade = ?,
            bt_oos_sharpe = ?,
            monte_carlo_stable = ?,
            walkforward_consistent = ?,
            parameter_sensitive = ?,
            status = ?,
            last_updated = ?
        WHERE id = ?
        """, (
            metrics.get('sharpe'),
            metrics.get('calmar'),
            metrics.get('sortino'),
            metrics.get('win_rate'),
            metrics.get('profit_factor'),
            metrics.get('max_drawdown'),
            metrics.get('total_trades'),
            metrics.get('avg_trade'),
            metrics.get('oos_sharpe'),
            1 if metrics.get('monte_carlo_stable') else 0,
            1 if metrics.get('walkforward_consistent') else 0,
            1 if metrics.get('parameter_sensitive') else 0,
            self.STATUS_VALIDATED if metrics.get('passed', False) else self.STATUS_CANDIDATE,
            datetime.now().isoformat(),
            strategy_id
        ))
        
        conn.commit()
        conn.close()
    
    def update_live_performance(self, strategy_id: str, 
                                pnl: float = None,
                                trade_result: Dict = None,
                                unrealized_pnl: float = None,
                                open_positions: int = None):
        """
        Update live trading metrics.
        
        Args:
            strategy_id: Strategy ID
            pnl: Current total realized PnL
            trade_result: Latest trade info (if a trade just closed)
                {
                    'symbol': 'GOLD',
                    'direction': 'BUY',
                    'pnl': 125.50,
                    'exit_reason': 'TP'
                }
            unrealized_pnl: Current unrealized PnL from open positions
            open_positions: Number of currently open positions
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get current stats
        cursor.execute("""
        SELECT live_pnl, live_trades, live_wins, live_losses, 
               consecutive_wins, consecutive_losses, live_peak_equity
        FROM strategies WHERE id = ?
        """, (strategy_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        
        current_pnl, trades, wins, losses, cons_wins, cons_losses, peak_equity = row
        
        # Update with new trade
        if trade_result:
            trades += 1
            trade_pnl = trade_result['pnl']
            
            if trade_pnl > 0:
                wins += 1
                cons_wins += 1
                cons_losses = 0
            else:
                losses += 1
                cons_losses += 1
                cons_wins = 0
            
            # Log the trade
            cursor.execute("""
            INSERT INTO strategy_trades (
                strategy_id, symbol, direction, entry_time, exit_time,
                pnl, exit_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                strategy_id,
                trade_result.get('symbol'),
                trade_result.get('direction'),
                trade_result.get('entry_time', datetime.now().isoformat()),
                datetime.now().isoformat(),
                trade_pnl,
                trade_result.get('exit_reason')
            ))
        
        # Update PnL if provided
        if pnl is not None:
            current_pnl = pnl
        
        # Add unrealized PnL to current PnL (for dashboard display)
        total_pnl_with_unrealized = current_pnl
        if unrealized_pnl is not None:
            total_pnl_with_unrealized += unrealized_pnl
        
        # Update peak equity and drawdown (use total including unrealized)
        if total_pnl_with_unrealized > (peak_equity or 0):
            peak_equity = total_pnl_with_unrealized
            drawdown = 0
        else:
            drawdown = (peak_equity - total_pnl_with_unrealized) / peak_equity if peak_equity > 0 else 0
        
        # Calculate live metrics
        win_rate = wins / trades if trades > 0 else 0
        
        # Update database
        cursor.execute("""
        UPDATE strategies SET
            live_pnl = ?,
            live_trades = ?,
            live_wins = ?,
            live_losses = ?,
            live_drawdown = ?,
            live_peak_equity = ?,
            consecutive_wins = ?,
            consecutive_losses = ?,
            last_trade_time = ?,
            last_updated = ?
        WHERE id = ?
        """, (
            total_pnl_with_unrealized, trades, wins, losses, drawdown, peak_equity,
            cons_wins, cons_losses,
            datetime.now().isoformat() if trade_result else None,
            datetime.now().isoformat(),
            strategy_id
        ))
        
        conn.commit()
        conn.close()
    
    def update_status(self, strategy_id: str, new_status: str, reason: str = None, updates: Dict = None):
        """
        Update strategy status.
        
        Args:
            strategy_id: Strategy ID
            new_status: New status (use STATUS_* constants)
            reason: Reason for status change (e.g., retirement reason)
            updates: Optional dictionary of extra fields to update
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        _updates_to_apply = {
            "status": new_status,
            "last_updated": datetime.now().isoformat()
        }
        
        if new_status == self.STATUS_LIVE:
            _updates_to_apply["deployed_at"] = datetime.now().isoformat()
        
        if new_status == self.STATUS_RETIRED:
            _updates_to_apply["retired_at"] = datetime.now().isoformat()
            _updates_to_apply["retirement_reason"] = reason
            
        if updates:
            _updates_to_apply.update(updates)
        
        set_clause = ", ".join([f"{k} = ?" for k in _updates_to_apply.keys()])
        values = list(_updates_to_apply.values()) + [strategy_id]
        
        cursor.execute(f"UPDATE strategies SET {set_clause} WHERE id = ?", values)
        
        conn.commit()
        conn.close()
    
    # ==================== QUERY ====================
    
    def get_strategy(self, strategy_id: str) -> Optional[Dict]:
        """Get full strategy record."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM strategies WHERE id = ?", (strategy_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_strategies_by_status(self, status: str) -> List[Dict]:
        """Get all strategies with given status."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM strategies WHERE status = ? ORDER BY last_updated DESC", (status,))
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_top_performers(self, n: int = 10, metric: str = "bt_sharpe") -> List[Dict]:
        """
        Get top N performing strategies.
        
        Args:
            n: Number of strategies to return
            metric: Metric to sort by ('bt_sharpe', 'live_sharpe', 'live_pnl', etc.)
        
        Returns:
            List of strategy records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(f"""
        SELECT * FROM strategies 
        WHERE {metric} IS NOT NULL 
        ORDER BY {metric} DESC 
        LIMIT ?
        """, (n,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_live_strategies(self) -> List[Dict]:
        """Get all currently live strategies."""
        return self.get_strategies_by_status(self.STATUS_LIVE)
    
    def get_paper_strategies(self) -> List[Dict]:
        """Get all paper trading strategies."""
        return self.get_strategies_by_status(self.STATUS_PAPER)
    
    def get_retired_strategies(self, limit: int = 20) -> List[Dict]:
        """Get recently retired strategies."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT * FROM strategies 
        WHERE status = ? 
        ORDER BY retired_at DESC 
        LIMIT ?
        """, (self.STATUS_RETIRED, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ==================== ANALYTICS ====================
    
    def get_portfolio_metrics(self) -> Dict:
        """Calculate portfolio-level statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Live strategies stats
        cursor.execute("""
        SELECT 
            COUNT(*) as count,
            SUM(live_pnl) as total_pnl,
            AVG(live_sharpe) as avg_sharpe,
            MAX(live_drawdown) as max_drawdown,
            SUM(live_trades) as total_trades
        FROM strategies WHERE status = ?
        """, (self.STATUS_LIVE,))
        
        live_stats = cursor.fetchone()
        
        # Paper strategies stats
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM strategies WHERE status = ?
        """, (self.STATUS_PAPER,))
        
        paper_count = cursor.fetchone()[0]
        
        # Retired count
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM strategies WHERE status = ?
        """, (self.STATUS_RETIRED,))
        
        retired_count = cursor.fetchone()[0]
        
        # Total strategies count
        cursor.execute("SELECT COUNT(*) FROM strategies")
        total_strategies = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_strategies": total_strategies,
            "live_count": live_stats[0] if live_stats else 0,
            "paper_count": paper_count,
            "retired_count": retired_count,
            "total_pnl": live_stats[1] if live_stats and live_stats[1] else 0,
            "avg_sharpe": live_stats[2] if live_stats and live_stats[2] else 0,
            "max_drawdown": live_stats[3] if live_stats and live_stats[3] else 0,
            "total_trades": live_stats[4] if live_stats and live_stats[4] else 0
        }
    
    def get_strategy_correlation(self, strategy_a_id: str, strategy_b_id: str) -> float:
        """
        Calculate correlation between two strategies based on daily PnL.
        
        Returns:
            Correlation coefficient (-1 to 1)
        """
        # TODO: Implement using performance_snapshots table
        # For now, return 0 (uncorrelated)
        return 0.0
    
    # ==================== CLEANUP ====================
    
    def archive_old_candidates(self, days: int = 30):
        """Delete candidate strategies older than N days that were never validated."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        DELETE FROM strategies 
        WHERE status = ? 
        AND datetime(created_at) < datetime('now', ? || ' days')
        """, (self.STATUS_CANDIDATE, -days))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted


if __name__ == "__main__":
    # Demo usage
    from strategy_genome import StrategyTemplates
    
    print("=" * 60)
    print("STRATEGY REGISTRY - Demo")
    print("=" * 60)
    
    # Initialize registry
    registry = StrategyRegistry("test_registry.db")
    
    # Create and register a strategy
    genome = StrategyTemplates.rsi_mean_reversion("GOLD", "M15")
    strategy_id = registry.add_candidate(genome, "Test RSI strategy")
    print(f"Registered strategy: {strategy_id}")
    
    # Simulate backtest results
    backtest_metrics = {
        'sharpe': 1.85,
        'calmar': 2.1,
        'win_rate': 0.58,
        'profit_factor': 2.3,
        'max_drawdown': 0.12,
        'total_trades': 145,
        'avg_trade': 23.50,
        'oos_sharpe': 1.62,
        'monte_carlo_stable': True,
        'walkforward_consistent': True,
        'parameter_sensitive': False,
        'passed': True
    }
    registry.update_backtest_results(strategy_id, backtest_metrics)
    print("Updated backtest results")
    
    # Promote to live
    registry.update_status(strategy_id, StrategyRegistry.STATUS_LIVE)
    print("Promoted to live trading")
    
    # Simulate some trades
    registry.update_live_performance(strategy_id, trade_result={
        'symbol': 'GOLD',
        'direction': 'BUY',
        'pnl': 125.50,
        'exit_reason': 'TP'
    })
    print("Logged trade")
    
    # Get portfolio metrics
    metrics = registry.get_portfolio_metrics()
    print(f"\nPortfolio Metrics: {metrics}")
    
    # Get top performers
    top = registry.get_top_performers(5)
    print(f"\nTop Performers: {len(top)} strategies")
    for s in top:
        print(f"  - {s['id'][:8]}... Sharpe: {s['bt_sharpe']}")
