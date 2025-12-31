"""
Portfolio Manager - Position & Exposure Control
================================================
Enforces portfolio-level constraints to prevent over-leverage.

Features:
- Maximum 5 simultaneous open positions
- No duplicate symbol positions
- Real-time sync with MT5 positions
- Exposure tracking by category (forex, commodity, etc.)
"""

import MetaTrader5 as mt5
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("Titan.MultiSymbol.PortfolioManager")


@dataclass
class Position:
    """Represents an open trading position."""
    ticket: int
    symbol: str
    type: str  # 'BUY' or 'SELL'
    volume: float
    open_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    magic: int
    comment: str
    open_time: datetime
    
    @property
    def is_long(self) -> bool:
        return self.type == 'BUY'
    
    @property
    def is_short(self) -> bool:
        return self.type == 'SELL'


@dataclass
class PortfolioState:
    """Current state of the portfolio."""
    positions: List[Position] = field(default_factory=list)
    position_count: int = 0
    total_exposure: float = 0.0
    unrealized_pnl: float = 0.0
    symbols_long: Set[str] = field(default_factory=set)
    symbols_short: Set[str] = field(default_factory=set)
    last_sync: datetime = None


class PortfolioManager:
    """
    Portfolio-level risk management.
    
    Constraints:
    - MAX_OPEN_POSITIONS = 5 (prevents over-leverage on small accounts)
    - No duplicate symbols (one position per symbol)
    - Category exposure limits (optional)
    
    Usage:
        pm = PortfolioManager(max_positions=5)
        if pm.can_open_position("EURUSD"):
            # Execute trade
        else:
            # Skip - portfolio full or symbol already held
    """
    
    DEFAULT_MAGIC = 234001  # Titan System magic number
    
    def __init__(self, max_positions: int = 5, magic_filter: int = None):
        """
        Initialize Portfolio Manager.
        
        Args:
            max_positions: Maximum simultaneous open positions (default 5)
            magic_filter: Only track positions with this magic number (None = all)
        """
        self.max_positions = max_positions
        self.magic_filter = magic_filter or self.DEFAULT_MAGIC
        self._state = PortfolioState()
        
    def connect(self) -> bool:
        """Ensure MT5 connection is established."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        return True
    
    def sync_positions(self) -> PortfolioState:
        """
        Synchronize local state with MT5 positions.
        
        Returns:
            Updated PortfolioState
        """
        if not self.connect():
            return self._state
        
        positions = mt5.positions_get()
        
        if positions is None:
            positions = []
        
        # Filter by magic number if specified
        if self.magic_filter:
            positions = [p for p in positions if p.magic == self.magic_filter]
        
        # Build position list
        pos_list = []
        symbols_long = set()
        symbols_short = set()
        total_exposure = 0.0
        unrealized_pnl = 0.0
        
        for pos in positions:
            position = Position(
                ticket=pos.ticket,
                symbol=pos.symbol,
                type='BUY' if pos.type == mt5.ORDER_TYPE_BUY else 'SELL',
                volume=pos.volume,
                open_price=pos.price_open,
                current_price=pos.price_current,
                sl=pos.sl,
                tp=pos.tp,
                profit=pos.profit,
                magic=pos.magic,
                comment=pos.comment,
                open_time=datetime.fromtimestamp(pos.time)
            )
            
            pos_list.append(position)
            
            if position.is_long:
                symbols_long.add(pos.symbol)
            else:
                symbols_short.add(pos.symbol)
            
            # Approximate exposure (volume * price)
            total_exposure += pos.volume * pos.price_current
            unrealized_pnl += pos.profit
        
        self._state = PortfolioState(
            positions=pos_list,
            position_count=len(pos_list),
            total_exposure=total_exposure,
            unrealized_pnl=unrealized_pnl,
            symbols_long=symbols_long,
            symbols_short=symbols_short,
            last_sync=datetime.now()
        )
        
        logger.debug(f"Portfolio synced: {self._state.position_count} positions, "
                    f"PnL: ${self._state.unrealized_pnl:.2f}")
        
        return self._state
    
    def get_open_positions(self) -> List[Position]:
        """Get list of currently open positions."""
        self.sync_positions()
        return self._state.positions
    
    def get_position_count(self) -> int:
        """Get count of open positions."""
        self.sync_positions()
        return self._state.position_count
    
    def has_position(self, symbol: str) -> bool:
        """Check if we already have a position in this symbol."""
        self.sync_positions()
        return symbol in self._state.symbols_long or symbol in self._state.symbols_short
    
    def get_position_direction(self, symbol: str) -> Optional[str]:
        """
        Get direction of existing position for a symbol.
        
        Returns:
            'LONG', 'SHORT', or None if no position
        """
        self.sync_positions()
        
        if symbol in self._state.symbols_long:
            return 'LONG'
        elif symbol in self._state.symbols_short:
            return 'SHORT'
        return None
    
    def can_open_position(self, symbol: str, direction: str = None) -> bool:
        """
        Check if we can open a new position.
        
        Checks:
        1. Current positions < MAX_OPEN_POSITIONS
        2. Symbol not already in portfolio
        3. (Optional) Direction check for hedging prevention
        
        Args:
            symbol: Symbol to check
            direction: 'BUY' or 'SELL' (optional)
            
        Returns:
            True if position can be opened, False otherwise
        """
        self.sync_positions()
        
        # Check position limit
        if self._state.position_count >= self.max_positions:
            logger.warning(f"Cannot open {symbol}: Max positions reached "
                          f"({self._state.position_count}/{self.max_positions})")
            return False
        
        # Check duplicate symbol
        if self.has_position(symbol):
            existing = self.get_position_direction(symbol)
            logger.warning(f"Cannot open {symbol}: Already have {existing} position")
            return False
        
        return True
    
    def get_available_slots(self) -> int:
        """Get number of available position slots."""
        self.sync_positions()
        return max(0, self.max_positions - self._state.position_count)
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get comprehensive portfolio summary.
        
        Returns:
            Dictionary with portfolio statistics
        """
        self.sync_positions()
        
        # Categorize positions
        by_category = {}
        for pos in self._state.positions:
            category = self._categorize_symbol(pos.symbol)
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(pos)
        
        return {
            'position_count': self._state.position_count,
            'max_positions': self.max_positions,
            'available_slots': self.get_available_slots(),
            'unrealized_pnl': self._state.unrealized_pnl,
            'total_exposure': self._state.total_exposure,
            'positions_long': len(self._state.symbols_long),
            'positions_short': len(self._state.symbols_short),
            'by_category': {cat: len(positions) for cat, positions in by_category.items()},
            'symbols': list(self._state.symbols_long | self._state.symbols_short),
            'last_sync': self._state.last_sync.isoformat() if self._state.last_sync else None
        }
    
    def _categorize_symbol(self, symbol: str) -> str:
        """Categorize symbol type."""
        symbol_upper = symbol.upper()
        
        if any(c in symbol_upper for c in ['BTC', 'ETH', 'XRP', 'LTC', 'DOGE']):
            return 'crypto'
        if any(c in symbol_upper for c in ['XAU', 'GOLD', 'XAG', 'OIL', 'WTI']):
            return 'commodity'
        if any(c in symbol_upper for c in ['US30', 'US500', 'US100', 'DAX', 'FTSE']):
            return 'index'
        return 'forex'
    
    def validate_new_trade(self, symbol: str, direction: str, lot_size: float) -> Dict:
        """
        Comprehensive validation before opening a new trade.
        
        Args:
            symbol: Trading symbol
            direction: 'BUY' or 'SELL'
            lot_size: Proposed lot size
            
        Returns:
            Dict with 'allowed' (bool), 'reason' (str), 'warnings' (list)
        """
        self.sync_positions()
        
        result = {
            'allowed': True,
            'reason': 'OK',
            'warnings': []
        }
        
        # Check 1: Position limit
        if self._state.position_count >= self.max_positions:
            result['allowed'] = False
            result['reason'] = f"Max positions reached ({self.max_positions})"
            return result
        
        # Check 2: Duplicate symbol
        if self.has_position(symbol):
            existing_dir = self.get_position_direction(symbol)
            result['allowed'] = False
            result['reason'] = f"Already have {existing_dir} position in {symbol}"
            return result
        
        # Warning: Concentrated exposure
        category = self._categorize_symbol(symbol)
        category_count = sum(1 for p in self._state.positions 
                           if self._categorize_symbol(p.symbol) == category)
        
        if category_count >= 3:
            result['warnings'].append(
                f"High {category} exposure: {category_count} positions"
            )
        
        # Warning: Approaching limit
        if self._state.position_count >= self.max_positions - 1:
            result['warnings'].append(
                f"This will be the last available slot ({self._state.position_count + 1}/{self.max_positions})"
            )
        
        return result


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    pm = PortfolioManager(max_positions=5)
    
    print("="*60)
    print("PORTFOLIO MANAGER TEST")
    print("="*60)
    
    # Get current state
    summary = pm.get_portfolio_summary()
    
    print(f"\nCurrent Positions: {summary['position_count']}/{summary['max_positions']}")
    print(f"Available Slots: {summary['available_slots']}")
    print(f"Unrealized PnL: ${summary['unrealized_pnl']:.2f}")
    print(f"Symbols: {summary['symbols']}")
    
    # Test can_open_position
    test_symbols = ['EURUSD', 'XAUUSD', 'GBPUSD', 'USDJPY', 'BTCUSD']
    
    print("\n--- Position Availability Check ---")
    for sym in test_symbols:
        can_open = pm.can_open_position(sym)
        validation = pm.validate_new_trade(sym, 'BUY', 0.01)
        print(f"{sym}: {'✓' if can_open else '✗'} - {validation['reason']}")
        for warn in validation['warnings']:
            print(f"  ⚠ {warn}")
