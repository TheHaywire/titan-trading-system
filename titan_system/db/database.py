
import sqlite3
import datetime
import json
import threading
from typing import List, Dict, Any, Optional

class Database:
    """
    SQLite Database with SharedConnection pattern.
    Uses a persistent connection to reduce I/O overhead during high-frequency operations.
    Thread-safe via threading.Lock.
    """
    _instances = {}  # Singleton pattern per db_path
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str):
        """Singleton per database path to ensure single connection."""
        with cls._lock:
            if db_path not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                cls._instances[db_path] = instance
            return cls._instances[db_path]
    
    def __init__(self, db_path: str):
        if self._initialized:
            return
        self.db_path = db_path
        self._conn = None
        self._write_lock = threading.Lock()
        self._init_db()
        self._initialized = True

    def _get_conn(self):
        """Get the shared persistent connection, creating if needed."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path, 
                check_same_thread=False, 
                timeout=30.0,
                isolation_level='DEFERRED'  # Better for concurrent reads
            )
            # Enable WAL mode for better concurrency
            self._conn.execute('PRAGMA journal_mode=WAL;')
            self._conn.execute('PRAGMA synchronous=NORMAL;')  # Faster writes, still safe
            self._conn.execute('PRAGMA cache_size=-64000;')  # 64MB cache
        return self._conn

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 1. Trades Table (Persistent Record)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            ticket INTEGER,
            symbol TEXT,
            type TEXT,
            volume REAL,
            open_price REAL,
            sl REAL,
            tp REAL,
            open_time DATETIME,
            close_time DATETIME,
            close_price REAL,
            profit REAL,
            magic INTEGER,
            comment TEXT,
            strategy_name TEXT
        )
        ''')
        
        # 2. Daily Stats (Optimized for Dashboard)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_stats (
            date TEXT PRIMARY KEY,
            equity_start REAL,
            equity_end REAL,
            balance_start REAL,
            balance_end REAL,
            total_trades INTEGER,
            win_count INTEGER,
            loss_count INTEGER,
            net_profit REAL,
            max_drawdown_percent REAL
        )
        ''')

        # 3. System Logs (Audit Trail)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            level TEXT,
            component TEXT,
            message TEXT,
            metadata JSON
        )
        ''')

        # 4. Market Universe (Recon Data)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS market_universe (
            symbol TEXT PRIMARY KEY,
            path TEXT,
            category TEXT,
            digits INTEGER,
            tick_size REAL,
            contract_size REAL,
            min_lot REAL,
            max_lot REAL,
            swap_long REAL,
            swap_short REAL,
            spread REAL,
            volatility_score REAL,
            is_tradable BOOLEAN,
            active_strategy TEXT,
            backtest_score REAL,
            last_updated DATETIME
        )
        ''')

        conn.commit()
        print("Database: Storage Layer Initialized (SQLite + SharedConnection)")

    # --- Trade Methods ---
    def record_trade(self, trade_data: Dict[str, Any]):
        """Inserts or updates a trade record."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Determine if insert or update
        cursor.execute('''
        INSERT OR REPLACE INTO trades (
            id, ticket, symbol, type, volume, open_price, sl, tp, 
            open_time, close_time, close_price, profit, magic, comment, strategy_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data.get('id'), trade_data.get('ticket'), trade_data.get('symbol'),
            trade_data.get('type'), trade_data.get('volume'), trade_data.get('open_price'),
            trade_data.get('sl'), trade_data.get('tp'), trade_data.get('open_time'),
            trade_data.get('close_time'), trade_data.get('close_price'), trade_data.get('profit'),
            trade_data.get('magic'), trade_data.get('comment'), trade_data.get('strategy_name')
        ))
        
        conn.commit()

    def get_trades_today(self) -> List[Dict]:
        """Fetch all trades executed today."""
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM trades WHERE date(open_time) = ?", (today,))
        rows = cursor.fetchall()
        
        # Convert to dict
        columns = [description[0] for description in cursor.description]
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
            
        return results

    # --- Log Methods ---
    def log(self, level: str, component: str, message: str, metadata: Dict = None):
        """Write to audit log."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        meta_json = json.dumps(metadata) if metadata else None
        
        cursor.execute('''
        INSERT INTO logs (level, component, message, metadata)
        VALUES (?, ?, ?, ?)
        ''', (level, component, message, meta_json))
        
        conn.commit()

    def get_latest_logs(self, limit=50):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    # --- Universe Methods ---
    def save_universe_scan(self, symbol_data_list: List[Dict]):
        """Bulk upsert of symbol metadata."""
        if not symbol_data_list: return
        
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # We usage INSERT OR REPLACE
        cursor.executemany('''
        INSERT OR REPLACE INTO market_universe (
            symbol, path, category, digits, tick_size, contract_size,
            min_lot, max_lot, swap_long, swap_short, spread, 
            volatility_score, is_tradable, active_strategy, backtest_score, last_updated
        ) VALUES (
            :symbol, :path, :category, :digits, :tick_size, :contract_size,
            :min_lot, :max_lot, :swap_long, :swap_short, :spread,
            :volatility_score, :is_tradable, :active_strategy, :backtest_score, :last_updated
        )
        ''', symbol_data_list)
        
        conn.commit()

    def get_active_universe(self, limit=20) -> List[str]:
        """Returns the top tradable symbols."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol FROM market_universe 
            WHERE is_tradable = 1 
            ORDER BY volatility_score DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        return [r[0] for r in rows]

    def get_assigned_strategy(self, symbol: str) -> tuple[Optional[str], float]:
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT active_strategy, backtest_score FROM market_universe WHERE symbol=?", (symbol,))
        res = cursor.fetchone()
        return (res[0], res[1]) if res else (None, 0.0)

    def update_symbol_score(self, updates: List[Dict]):
        """
        Updates volatility_score and is_tradable for a list of symbols.
        updates expected to have keys: symbol, volatility_score, is_tradable
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.executemany('''
            UPDATE market_universe 
            SET volatility_score = :volatility_score, is_tradable = :is_tradable
            WHERE symbol = :symbol
        ''', updates)
        
        conn.commit()

    def get_symbol_performance(self, symbol: str) -> Dict[str, Any]:
        """Calculates historical expectancy and win rate for a symbol."""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), AVG(profit), SUM(profit)
            FROM trades
            WHERE symbol = ? AND profit IS NOT NULL
        ''', (symbol,))
        
        row = cursor.fetchone()
        
        if not row or row[0] == 0:
            conn.close()
            return {"trade_count": 0, "expectancy": 0.0, "total_pnl": 0.0, "win_rate": 0.0}
            
        count, expectancy, total_pnl = row
        
        # Calculate win rate
        cursor.execute('SELECT COUNT(*) FROM trades WHERE symbol = ? AND profit > 0', (symbol,))
        wins = cursor.fetchone()[0]
        
        return {
            "trade_count": count,
            "expectancy": expectancy if expectancy else 0.0,
            "total_pnl": total_pnl if total_pnl else 0.0,
            "win_rate": wins / count if count > 0 else 0.0
        }
    
    def close(self):
        """Explicitly close the connection (for cleanup)."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def __del__(self):
        """Destructor to ensure connection is closed."""
        self.close()
