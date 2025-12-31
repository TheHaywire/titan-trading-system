"""
Memory System
=============
QuantAI Architecture - Three-Tier Memory

Implements intelligent memory for learning from historical performance:

1. ShortTermMemory: Runtime state (current prices, recent signals, active positions)
2. LongTermMemory: Historical performance from SQLite (win rates, setup stats)
3. EntityMemory: Symbol-specific intelligence (profiles, session bias, correlations)

This enables data-driven decision making based on proven patterns.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import deque
import sqlite3
import pandas as pd
import os

logger = logging.getLogger("Titan.Memory")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class SymbolProfile:
    """Learned behavior profile for a symbol"""
    symbol: str
    avg_daily_range: float = 0.0
    best_session: str = ""
    best_hours: List[int] = field(default_factory=list)
    worst_hours: List[int] = field(default_factory=list)
    win_rate: float = 0.0
    avg_profit: float = 0.0
    total_trades: int = 0
    correlation_group: str = ""  # e.g., "USD_MAJORS", "COMMODITIES"
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SessionBias:
    """Session-specific bias for a symbol"""
    symbol: str
    asian_bias: str = "NEUTRAL"  # BULLISH, BEARISH, NEUTRAL
    london_bias: str = "NEUTRAL"
    newyork_bias: str = "NEUTRAL"
    asian_win_rate: float = 0.5
    london_win_rate: float = 0.5
    newyork_win_rate: float = 0.5


@dataclass
class SetupStats:
    """Historical statistics for a setup type"""
    setup_type: str
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    avg_r_multiple: float = 0.0
    best_symbol: str = ""
    worst_symbol: str = ""


@dataclass
class HourlyStats:
    """Trading statistics for a specific hour"""
    hour: int  # 0-23 UTC
    total_trades: int = 0
    wins: int = 0
    win_rate: float = 0.0
    avg_profit: float = 0.0
    is_power_hour: bool = False
    is_death_zone: bool = False


# =============================================================================
# SHORT-TERM MEMORY
# =============================================================================

class ShortTermMemory:
    """
    Runtime state - fast, in-memory storage.
    
    Stores:
    - Current prices for all symbols
    - Recent signals (last N)
    - Active positions
    - Session state
    """
    
    def __init__(self, max_signals: int = 100):
        self.current_prices: Dict[str, float] = {}
        self.recent_signals: deque = deque(maxlen=max_signals)
        self.active_positions: Dict[int, Dict] = {}  # ticket -> position info
        self.current_session: str = "UNKNOWN"
        self.session_start_equity: float = 0.0
        self.current_equity: float = 0.0
        self.day_high_equity: float = 0.0
        self.day_low_equity: float = 0.0
        self._last_update: datetime = datetime.now(timezone.utc)
        
    def update_price(self, symbol: str, price: float):
        """Update current price for a symbol"""
        self.current_prices[symbol] = price
        self._last_update = datetime.now(timezone.utc)
        
    def get_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        return self.current_prices.get(symbol)
        
    def add_signal(self, signal: Dict):
        """Add a signal to recent history"""
        signal['timestamp'] = datetime.now(timezone.utc)
        self.recent_signals.append(signal)
        
    def get_recent_signals(self, count: int = 10, symbol: str = None) -> List[Dict]:
        """Get recent signals, optionally filtered by symbol"""
        signals = list(self.recent_signals)
        if symbol:
            signals = [s for s in signals if s.get('symbol') == symbol]
        return signals[-count:]
    
    def update_position(self, ticket: int, position_data: Dict):
        """Update or add position"""
        self.active_positions[ticket] = {
            **position_data,
            'last_update': datetime.now(timezone.utc)
        }
        
    def remove_position(self, ticket: int):
        """Remove closed position"""
        if ticket in self.active_positions:
            del self.active_positions[ticket]
            
    def get_open_exposure(self) -> Dict[str, float]:
        """Get current exposure by symbol"""
        exposure = {}
        for ticket, pos in self.active_positions.items():
            symbol = pos.get('symbol', 'UNKNOWN')
            volume = pos.get('volume', 0.0)
            direction = 1 if pos.get('type') == 'BUY' else -1
            exposure[symbol] = exposure.get(symbol, 0.0) + (volume * direction)
        return exposure
    
    def update_equity(self, equity: float, balance: float):
        """Update equity tracking"""
        self.current_equity = equity
        if self.session_start_equity == 0:
            self.session_start_equity = equity
        self.day_high_equity = max(self.day_high_equity, equity)
        if self.day_low_equity == 0:
            self.day_low_equity = equity
        else:
            self.day_low_equity = min(self.day_low_equity, equity)
            
    def get_drawdown(self) -> float:
        """Get current drawdown from session start"""
        if self.session_start_equity == 0:
            return 0.0
        return (self.session_start_equity - self.current_equity) / self.session_start_equity
    
    def reset_session(self, starting_equity: float):
        """Reset for new session"""
        self.session_start_equity = starting_equity
        self.day_high_equity = starting_equity
        self.day_low_equity = starting_equity
        
    def get_state(self) -> Dict[str, Any]:
        """Get current memory state"""
        return {
            "prices_tracked": len(self.current_prices),
            "signals_cached": len(self.recent_signals),
            "open_positions": len(self.active_positions),
            "current_session": self.current_session,
            "current_equity": self.current_equity,
            "current_drawdown": f"{self.get_drawdown():.2%}",
            "last_update": self._last_update
        }


# =============================================================================
# LONG-TERM MEMORY
# =============================================================================

class LongTermMemory:
    """
    Historical performance from SQLite database.
    
    Provides:
    - Symbol performance lookup
    - Setup type win rates
    - Hourly performance analysis
    - Trade history queries
    """
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Default to titan.db in titan_system folder
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_path, "titan.db")
        self.db_path = db_path
        self._ensure_tables()
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _ensure_tables(self):
        """Ensure required tables exist"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Performance summary table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS symbol_performance (
                        symbol TEXT PRIMARY KEY,
                        total_trades INTEGER DEFAULT 0,
                        wins INTEGER DEFAULT 0,
                        losses INTEGER DEFAULT 0,
                        total_profit REAL DEFAULT 0,
                        avg_profit REAL DEFAULT 0,
                        win_rate REAL DEFAULT 0,
                        best_hour INTEGER,
                        worst_hour INTEGER,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Setup performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS setup_performance (
                        setup_type TEXT PRIMARY KEY,
                        total_trades INTEGER DEFAULT 0,
                        wins INTEGER DEFAULT 0,
                        avg_profit REAL DEFAULT 0,
                        avg_r_multiple REAL DEFAULT 0,
                        best_symbol TEXT,
                        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Hourly performance table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hourly_performance (
                        hour INTEGER PRIMARY KEY,
                        total_trades INTEGER DEFAULT 0,
                        wins INTEGER DEFAULT 0,
                        total_profit REAL DEFAULT 0,
                        is_power_hour INTEGER DEFAULT 0,
                        is_death_zone INTEGER DEFAULT 0
                    )
                """)
                
                conn.commit()
                logger.debug("LongTermMemory tables ensured")
        except Exception as e:
            logger.error(f"Failed to ensure LongTermMemory tables: {e}")
    
    def get_symbol_performance(self, symbol: str) -> Optional[Dict]:
        """Get historical performance for a symbol"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT total_trades, wins, losses, total_profit, avg_profit, 
                           win_rate, best_hour, worst_hour
                    FROM symbol_performance WHERE symbol = ?
                """, (symbol,))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "symbol": symbol,
                        "total_trades": row[0],
                        "wins": row[1],
                        "losses": row[2],
                        "total_profit": row[3],
                        "avg_profit": row[4],
                        "win_rate": row[5],
                        "best_hour": row[6],
                        "worst_hour": row[7]
                    }
        except Exception as e:
            logger.error(f"Failed to get symbol performance: {e}")
        return None
    
    def get_setup_win_rate(self, setup_type: str) -> float:
        """Get historical win rate for a setup type"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT wins, total_trades FROM setup_performance WHERE setup_type = ?
                """, (setup_type,))
                row = cursor.fetchone()
                
                if row and row[1] > 0:
                    return row[0] / row[1]
        except Exception as e:
            logger.error(f"Failed to get setup win rate: {e}")
        return 0.5  # Default 50% if no data
    
    def get_hourly_performance(self, hour: int) -> HourlyStats:
        """Get trading statistics for a specific hour"""
        stats = HourlyStats(hour=hour)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT total_trades, wins, total_profit, is_power_hour, is_death_zone
                    FROM hourly_performance WHERE hour = ?
                """, (hour,))
                row = cursor.fetchone()
                
                if row:
                    stats.total_trades = row[0]
                    stats.wins = row[1]
                    stats.win_rate = row[1] / row[0] if row[0] > 0 else 0.5
                    stats.avg_profit = row[2] / row[0] if row[0] > 0 else 0.0
                    stats.is_power_hour = bool(row[3])
                    stats.is_death_zone = bool(row[4])
        except Exception as e:
            logger.error(f"Failed to get hourly performance: {e}")
        return stats
    
    def get_best_hours(self, min_trades: int = 10) -> List[int]:
        """Get hours with best performance"""
        best_hours = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT hour FROM hourly_performance 
                    WHERE total_trades >= ? AND is_power_hour = 1
                    ORDER BY (wins * 1.0 / total_trades) DESC
                """, (min_trades,))
                best_hours = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get best hours: {e}")
        return best_hours or [8, 9, 10, 13, 14, 15]  # Default London/NY overlap
    
    def get_death_zones(self, min_trades: int = 5) -> List[int]:
        """Get hours with worst performance (to avoid)"""
        death_zones = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT hour FROM hourly_performance 
                    WHERE total_trades >= ? AND is_death_zone = 1
                """, (min_trades,))
                death_zones = [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get death zones: {e}")
        return death_zones
    
    def update_from_trade(self, trade_data: Dict):
        """Update performance stats from a closed trade"""
        try:
            symbol = trade_data.get('symbol', '')
            setup_type = trade_data.get('setup_type', 'UNKNOWN')
            profit = trade_data.get('profit', 0.0)
            is_win = profit > 0
            hour = trade_data.get('entry_hour', 12)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Update symbol performance
                cursor.execute("""
                    INSERT INTO symbol_performance (symbol, total_trades, wins, losses, total_profit)
                    VALUES (?, 1, ?, ?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        total_trades = total_trades + 1,
                        wins = wins + ?,
                        losses = losses + ?,
                        total_profit = total_profit + ?,
                        avg_profit = (total_profit + ?) / (total_trades + 1),
                        win_rate = (wins + ?) * 1.0 / (total_trades + 1),
                        last_updated = CURRENT_TIMESTAMP
                """, (
                    symbol, 
                    1 if is_win else 0, 
                    0 if is_win else 1, 
                    profit,
                    1 if is_win else 0,
                    0 if is_win else 1,
                    profit,
                    profit,
                    1 if is_win else 0
                ))
                
                # Update hourly performance
                cursor.execute("""
                    INSERT INTO hourly_performance (hour, total_trades, wins, total_profit)
                    VALUES (?, 1, ?, ?)
                    ON CONFLICT(hour) DO UPDATE SET
                        total_trades = total_trades + 1,
                        wins = wins + ?,
                        total_profit = total_profit + ?
                """, (hour, 1 if is_win else 0, profit, 1 if is_win else 0, profit))
                
                conn.commit()
                logger.debug(f"Updated LongTermMemory from trade: {symbol} ${profit:.2f}")
                
        except Exception as e:
            logger.error(f"Failed to update from trade: {e}")


# =============================================================================
# ENTITY MEMORY
# =============================================================================

class EntityMemory:
    """
    Symbol-specific intelligence and learned behaviors.
    
    Stores:
    - Symbol profiles (avg range, best session, etc.)
    - Session bias per symbol
    - Correlation groups
    """
    
    # Predefined correlation groups
    CORRELATION_GROUPS = {
        "USD_MAJORS": ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD"],
        "EUR_CROSSES": ["EURJPY", "EURGBP", "EURAUD", "EURCAD"],
        "RISK_ON": ["AUDUSD", "NZDUSD", "AUDJPY"],
        "SAFE_HAVEN": ["USDJPY", "USDCHF", "GOLD"],
        "COMMODITIES": ["GOLD", "SILVER", "WTI", "BRENT"],
        "CRYPTO": ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"],
        "INDICES": ["US500", "US30", "USTEC", "GER40", "UK100"]
    }
    
    def __init__(self, long_term_memory: LongTermMemory = None):
        self.ltm = long_term_memory or LongTermMemory()
        self.symbol_profiles: Dict[str, SymbolProfile] = {}
        self.session_biases: Dict[str, SessionBias] = {}
        self._correlation_cache: Dict[str, List[str]] = {}
        
    def get_symbol_profile(self, symbol: str) -> SymbolProfile:
        """Get or create profile for a symbol"""
        if symbol not in self.symbol_profiles:
            # Load from LTM or create new
            perf = self.ltm.get_symbol_performance(symbol)
            profile = SymbolProfile(symbol=symbol)
            
            if perf:
                profile.win_rate = perf.get('win_rate', 0.0)
                profile.total_trades = perf.get('total_trades', 0)
                profile.avg_profit = perf.get('avg_profit', 0.0)
                profile.best_hours = [perf['best_hour']] if perf.get('best_hour') else []
                profile.worst_hours = [perf['worst_hour']] if perf.get('worst_hour') else []
            
            # Assign correlation group
            for group_name, symbols in self.CORRELATION_GROUPS.items():
                if symbol in symbols:
                    profile.correlation_group = group_name
                    break
                    
            self.symbol_profiles[symbol] = profile
            
        return self.symbol_profiles[symbol]
    
    def get_correlated_symbols(self, symbol: str) -> List[str]:
        """Get symbols correlated with this one"""
        if symbol in self._correlation_cache:
            return self._correlation_cache[symbol]
            
        correlated = []
        for group_name, symbols in self.CORRELATION_GROUPS.items():
            if symbol in symbols:
                correlated = [s for s in symbols if s != symbol]
                break
                
        self._correlation_cache[symbol] = correlated
        return correlated
    
    def get_session_bias(self, symbol: str) -> SessionBias:
        """Get session-specific bias for a symbol"""
        if symbol not in self.session_biases:
            self.session_biases[symbol] = SessionBias(symbol=symbol)
        return self.session_biases[symbol]
    
    def should_trade_symbol_now(self, symbol: str) -> Tuple[bool, str]:
        """
        Determine if this symbol should be traded in current conditions.
        Returns (should_trade, reason)
        """
        profile = self.get_symbol_profile(symbol)
        current_hour = datetime.now(timezone.utc).hour
        
        # Check death zones
        if current_hour in profile.worst_hours:
            return False, f"Death zone hour ({current_hour}:00 UTC)"
            
        # Check if symbol has proven track record
        if profile.total_trades >= 10 and profile.win_rate < 0.35:
            return False, f"Poor historical win rate ({profile.win_rate:.0%})"
            
        # Power hour bonus (allow)
        if current_hour in profile.best_hours:
            return True, f"Power hour ({current_hour}:00 UTC)"
            
        return True, "No restrictions"
    
    def get_exposure_warning(self, symbol: str, current_exposure: Dict[str, float]) -> Optional[str]:
        """Check if adding to this symbol would create dangerous correlation exposure"""
        correlated = self.get_correlated_symbols(symbol)
        
        # Count same-direction exposure in correlated symbols
        same_direction_count = 0
        for corr_symbol in correlated:
            if corr_symbol in current_exposure and current_exposure[corr_symbol] != 0:
                same_direction_count += 1
                
        if same_direction_count >= 2:
            return f"High correlation risk: Already exposed to {same_direction_count} correlated pairs"
            
        return None


# =============================================================================
# UNIFIED MEMORY SYSTEM
# =============================================================================

class MemorySystem:
    """
    Unified memory interface combining all three tiers.
    """
    
    def __init__(self, db_path: str = None):
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory(db_path)
        self.entity = EntityMemory(self.long_term)
        
    def get_trading_context(self, symbol: str) -> Dict[str, Any]:
        """Get full context for trading decision"""
        return {
            "short_term": {
                "current_price": self.short_term.get_price(symbol),
                "recent_signals": self.short_term.get_recent_signals(5, symbol),
                "open_exposure": self.short_term.get_open_exposure(),
                "current_drawdown": self.short_term.get_drawdown()
            },
            "long_term": self.long_term.get_symbol_performance(symbol),
            "entity": {
                "profile": self.entity.get_symbol_profile(symbol),
                "session_bias": self.entity.get_session_bias(symbol),
                "correlated": self.entity.get_correlated_symbols(symbol)
            }
        }
    
    def record_trade(self, trade_data: Dict):
        """Record a trade across all memory tiers"""
        # Update long-term memory
        self.long_term.update_from_trade(trade_data)
        
        # Update entity memory
        symbol = trade_data.get('symbol', '')
        if symbol in self.entity.symbol_profiles:
            # Force refresh on next access
            del self.entity.symbol_profiles[symbol]
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all memory tiers"""
        return {
            "short_term": self.short_term.get_state(),
            "long_term": {
                "db_path": self.long_term.db_path,
                "connected": os.path.exists(self.long_term.db_path)
            },
            "entity": {
                "profiles_cached": len(self.entity.symbol_profiles),
                "biases_cached": len(self.entity.session_biases)
            }
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create memory system
    memory = MemorySystem()
    
    # Short-term operations
    memory.short_term.update_price("EURUSD", 1.0850)
    memory.short_term.add_signal({
        "symbol": "EURUSD",
        "direction": "BUY",
        "score": 85
    })
    
    # Get trading context
    context = memory.get_trading_context("EURUSD")
    print("\n=== Trading Context for EURUSD ===")
    print(f"Current Price: {context['short_term']['current_price']}")
    print(f"Recent Signals: {len(context['short_term']['recent_signals'])}")
    
    # Entity checks
    should_trade, reason = memory.entity.should_trade_symbol_now("EURUSD")
    print(f"\nShould Trade: {should_trade} - {reason}")
    
    correlated = memory.entity.get_correlated_symbols("EURUSD")
    print(f"Correlated Pairs: {correlated}")
    
    # Print status
    print("\n=== Memory Status ===")
    status = memory.get_status()
    for tier, data in status.items():
        print(f"\n{tier.upper()}:")
        for key, value in data.items():
            print(f"  {key}: {value}")
