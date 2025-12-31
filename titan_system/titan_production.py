"""
TITAN PRODUCTION BOT
====================
World-Class Trading System - Unified Architecture

Combines:
- Robust bot core (proven logic)
- Execution Decision Agent (smart decisions)
- Circuit Breaker (safety)
- SMC Analysis (institutional edge)
- SQLite logging (persistence)  
- Auto break-even (profit protection)

This is THE bot to run in production.

Usage:
    python -m titan_system.titan_production
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass

# Import our best components
from titan_system.agents.execution_decision_agent import ExecutionDecisionAgent, QuantSignal, Direction
from titan_system.core.circuit_breaker import CircuitBreaker
from titan_system.execution.mt5_executor import MT5Executor

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("titan_production.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TitanProduction")


@dataclass
class TradeRecord:
    """Record of a trade for logging"""
    timestamp: datetime
    symbol: str
    direction: str
    entry_price: float
    lot_size: float
    stop_loss: float
    take_profit: float
    score: float
    reason: str
    ticket: Optional[int] = None


class TitanProductionBot:
    """
    The Unified Production Trading Bot.
    
    Simplified QuantAI architecture with only what works.
    """
    
    VERSION = "1.0.0"
    
    # Curated symbols - only liquid, tested ones
    UNIVERSE = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "GOLD", "BTCUSD", "US500"
    ]
    
    # Correlation groups for exposure limits
    CORRELATION_GROUPS = {
        "USD": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"],
        "JPY": ["USDJPY", "EURJPY", "GBPJPY"],
        "GOLD": ["GOLD", "XAUUSD"],
        "CRYPTO": ["BTCUSD", "ETHUSD"]
    }
    
    def __init__(self):
        # Core components
        self.executor = MT5Executor()
        self.execution_agent = ExecutionDecisionAgent(trading_mode="LIVE")
        self.circuit_breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        
        # Configuration
        self.risk_per_trade = 0.5  # 0.5% per trade
        self.max_total_risk = 5.0  # 5% total
        self.max_positions = 8
        self.max_per_group = 2
        self.scan_interval = 120  # 2 minutes
        
        # State
        self.db_conn = None
        self.running = False
        self.cycle_count = 0
        self.session_start_equity = 0.0
        
        logger.info(f"🚀 Titan Production Bot v{self.VERSION}")
    
    def start(self):
        """Start the production bot"""
        logger.info("="*60)
        logger.info("TITAN PRODUCTION BOT - STARTING")
        logger.info("="*60)
        
        # Connect to MT5
        if not self.executor.connect():
            logger.critical("MT5 connection failed!")
            return
        
        # Initialize database
        self._init_database()
        
        # Get starting equity
        account = self.executor.get_account_info()
        self.session_start_equity = account.get('equity', 0)
        
        logger.info(f"Account: {account.get('login')}")
        logger.info(f"Equity: ${self.session_start_equity:,.2f}")
        logger.info(f"Universe: {len(self.UNIVERSE)} symbols")
        logger.info(f"Risk/Trade: {self.risk_per_trade}%")
        logger.info("="*60)
        
        self.running = True
        
        # Main loop
        while self.running:
            try:
                self._cycle()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                break
            except Exception as e:
                logger.error(f"Cycle error: {e}", exc_info=True)
                time.sleep(60)
        
        self._shutdown()
    
    def _cycle(self):
        """One complete cycle"""
        self.cycle_count += 1
        logger.info(f"--- CYCLE {self.cycle_count} ---")
        
        # 1. Check circuit breaker
        account = self.executor.get_account_info()
        safe, reason = self.circuit_breaker.check_safe_to_trade(account)
        
        if not safe:
            logger.warning(f"⛔ Trading halted: {reason}")
            self._manage_positions()  # Still manage existing
            return
        
        # 2. Manage existing positions (break-even, etc.)
        self._manage_positions()
        
        # 3. Check if we can open new positions
        positions = mt5.positions_get()
        current_count = len(positions) if positions else 0
        
        if current_count >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return
        
        # 4. Scan for opportunities
        for symbol in self.UNIVERSE:
            if current_count >= self.max_positions:
                break
            
            # Check correlation limits
            if not self._check_correlation_limit(symbol):
                continue
            
            # Check if already have position
            if self._has_position(symbol):
                continue
            
            # Analyze symbol
            signal = self._analyze(symbol)
            if signal and signal.score >= 85:
                if self._execute(signal):
                    current_count += 1
    
    def _is_power_hour(self) -> tuple[bool, str]:
        """Check if current time is in power trading hours (from daytrading book)"""
        utc_hour = datetime.now(timezone.utc).hour
        
        # London open (7-10 UTC) - High liquidity
        if 7 <= utc_hour < 10:
            return True, "LONDON_OPEN"
        
        # London/NY overlap (12-13 UTC) - Highest liquidity
        if 12 <= utc_hour < 13:
            return True, "OVERLAP"
        
        # NY open (13-16 UTC) - High volatility
        if 13 <= utc_hour < 16:
            return True, "NY_OPEN"
        
        # Death zones (from books)
        if 17 <= utc_hour < 20:
            return False, "LUNCH_DEAD"  # Low liquidity
        
        if 21 <= utc_hour or utc_hour < 5:
            return False, "AFTER_HOURS"  # Avoid
        
        return True, "OK"
    
    def _analyze(self, symbol: str) -> Optional[QuantSignal]:
        """
        Analyze symbol using simplified SMC approach.
        
        Focus on:
        - RSI extremes (proven)
        - EMA crossovers (proven)
        - Momentum breaks (proven)
        """
        try:
            # Session filter (from Complete Guide to Daytrading)
            is_good_time, session = self._is_power_hour()
            if not is_good_time:
                logger.debug(f"{symbol} - Skipping bad session: {session}")
                return None
            
            # Get data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
            if rates is None or len(rates) < 50:
                return None
            
            df = pd.DataFrame(rates)
            
            # Calculate indicators
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
            
            df['MOM'] = df['close'].pct_change(5) * 100
            
            # Volume analysis (from Technical Analysis books)
            df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
            df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Volume filter (from TA books - volume confirms price)
            if curr['VOL_RATIO'] < 0.8:
                logger.debug(f"{symbol} - Low volume: {curr['VOL_RATIO']:.2f}x")
                return None  # Skip low volume signals
            
            # Signal detection - STRICT
            direction = None
            score = 0
            reason = []
            
            # RSI extremes (highest confidence)
            # High volume boost (from TA books)
            volume_boost = 0
            if curr['VOL_RATIO'] > 1.5:
                volume_boost = 5
                reason.append(f"High volume ({curr['VOL_RATIO']:.1f}x)")
            
            if curr['RSI'] < 15:
                direction = Direction.BUY
                score = 95 + volume_boost
                reason.append(f"RSI extreme oversold ({curr['RSI']:.0f})")
                reason.append(f"Session: {session}")
            elif curr['RSI'] > 85:
                direction = Direction.SELL
                score = 95
                reason.append(f"RSI extreme overbought ({curr['RSI']:.0f})")
            elif curr['RSI'] < 25 and curr['MOM'] > 0.5:
                direction = Direction.BUY
                score = 90
                reason.append(f"RSI oversold + momentum")
            elif curr['RSI'] > 75 and curr['MOM'] < -0.5:
                direction = Direction.SELL
                score = 90
                reason.append(f"RSI overbought + momentum")
            # EMA crossover + momentum (good confidence)
            elif prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21'] and curr['MOM'] > 1.0:
                direction = Direction.BUY
                score = 88
                reason.append("EMA bullish cross + strong momentum")
            elif prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21'] and curr['MOM'] < -1.0:
                direction = Direction.SELL
                score = 88
                reason.append("EMA bearish cross + strong momentum")
            
            if not direction:
                return None
            
            # Create signal
            current_price = curr['close']
            
            # Calculate stops
            info = mt5.symbol_info(symbol)
            if "BTC" in symbol or "ETH" in symbol:
                sl_points = 50000
            elif "GOLD" in symbol:
                sl_points = 5000
            elif "US5" in symbol or "US3" in symbol:
                sl_points = 5000
            else:
                sl_points = 500
            
            point = info.point
            
            if direction == Direction.BUY:
                stop_loss = current_price - sl_points * point
                take_profit = current_price + (sl_points * 2) * point
            else:
                stop_loss = current_price + sl_points * point
                take_profit = current_price - (sl_points * 2) * point
            
            return QuantSignal(
                symbol=symbol,
                direction=direction,
                score=score,
                setup_type="PRODUCTION",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                expected_r=2.0,
                reasoning=reason
            )
            
        except Exception as e:
            logger.warning(f"Analysis error for {symbol}: {e}")
            return None
    
    def _execute(self, signal: QuantSignal) -> bool:
        """Execute a trade"""
        try:
            logger.info(f"SIGNAL: {signal.symbol} {signal.direction.value} | Score: {signal.score}")
            logger.info(f"Reason: {', '.join(signal.reasoning)}")
            
            # Calculate lot size
            account = self.executor.get_account_info()
            equity = account['equity']
            risk_amount = equity * (self.risk_per_trade / 100)
            
            info = mt5.symbol_info(signal.symbol)
            point = info.point
            tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 1.0
            
            sl_distance = abs(signal.entry_price - signal.stop_loss) / point
            lot = risk_amount / (sl_distance * tick_value)
            lot = max(info.volume_min, min(info.volume_max, round(lot, 2)))
            
            # Determine SL/TP points for executor
            sl_points = int(sl_distance)
            tp_points = sl_points * 2
            
            # Execute via our executor
            result = self.executor.execute_order(
                symbol=signal.symbol,
                order_type=signal.direction.value,
                lot=lot,
                sl_points=sl_points,
                tp_points=tp_points,
                comment=f"Titan: {signal.score:.0f}"
            )
            
            if result:
                # Log to database
                self._log_trade(TradeRecord(
                    timestamp=datetime.now(timezone.utc),
                    symbol=signal.symbol,
                    direction=signal.direction.value,
                    entry_price=signal.entry_price,
                    lot_size=lot,
                    stop_loss=signal.stop_loss,
                    take_profit=signal.take_profit,
                    score=signal.score,
                    reason=', '.join(signal.reasoning),
                    ticket=result.get('ticket')
                ))
                
                logger.info(f"✅ Executed: {signal.symbol} {signal.direction.value} {lot} lots")
                return True
            else:
                logger.error(f"❌ Execution failed: {signal.symbol}")
                return False
                
        except Exception as e:
            logger.error(f"Execute error: {e}", exc_info=True)
            return False
    
    def _manage_positions(self):
        """Auto break-even for profitable positions"""
        positions = mt5.positions_get()
        if not positions:
            return
        
        for pos in positions:
            # Only manage our trades
            if "Titan" not in pos.comment:
                continue
            
            # Move to break-even if profit > $100/lot
            profit_per_lot = pos.profit / pos.volume if pos.volume > 0 else 0
            
            if profit_per_lot > 100:
                entry = pos.price_open
                sl = pos.sl
                
                # Check if already at break-even
                if pos.type == 0:  # BUY
                    if sl < entry:
                        self._move_to_breakeven(pos)
                else:  # SELL
                    if sl > entry or sl == 0:
                        self._move_to_breakeven(pos)
    
    def _move_to_breakeven(self, pos):
        """Move SL to break-even"""
        entry = pos.price_open
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": pos.symbol,
            "position": pos.ticket,
            "sl": entry,
            "tp": pos.tp,
        }
        
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"🛡️  Break-even: {pos.symbol} @ {entry:.5f}")
    
    def _check_correlation_limit(self, symbol: str) -> bool:
        """Check correlation exposure limits"""
        positions = mt5.positions_get()
        if not positions:
            return True
        
        # Count positions per group
        group_counts = {}
        for pos in positions:
            for group, symbols in self.CORRELATION_GROUPS.items():
                if any(s in pos.symbol for s in symbols):
                    group_counts[group] = group_counts.get(group, 0) + 1
        
        # Check if symbol would exceed limit
        for group, symbols in self.CORRELATION_GROUPS.items():
            if any(s in symbol for s in symbols):
                current = group_counts.get(group, 0)
                if current >= self.max_per_group:
                    logger.debug(f"Correlation limit: {group} at {current}")
                    return False
        
        return True
    
    def _has_position(self, symbol: str) -> bool:
        """Check if already have position"""
        positions = mt5.positions_get(symbol=symbol)
        return positions is not None and len(positions) > 0
    
    def _init_database(self):
        """Initialize SQLite database for logging"""
        self.db_conn = sqlite3.connect("titan_production.db")
        cursor = self.db_conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                direction TEXT NOT NULL,
                entry_price REAL NOT NULL,
                lot_size REAL NOT NULL,
                stop_loss REAL NOT NULL,
                take_profit REAL NOT NULL,
                score REAL NOT NULL,
                reason TEXT,
                ticket INTEGER
            )
        """)
        
        self.db_conn.commit()
        logger.info("✅ Database initialized")
    
    def _log_trade(self, trade: TradeRecord):
        """Log trade to database"""
        cursor = self.db_conn.cursor()
        cursor.execute("""
            INSERT INTO trades (timestamp, symbol, direction, entry_price, lot_size,
                              stop_loss, take_profit, score, reason, ticket)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.timestamp.isoformat(),
            trade.symbol,
            trade.direction,
            trade.entry_price,
            trade.lot_size,
            trade.stop_loss,
            trade.take_profit,
            trade.score,
            trade.reason,
            trade.ticket
        ))
        self.db_conn.commit()
    
    def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down...")
        
        self.running = False
        
        if self.db_conn:
            self.db_conn.close()
        
        self.executor.shutdown()
        
        logger.info(f"📊 Total cycles: {self.cycle_count}")
        logger.info("Goodbye!")


if __name__ == "__main__":
    bot = TitanProductionBot()
    bot.start()
