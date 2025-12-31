"""
Event Bus & Trigger Detection System
=====================================
QuantAI Architecture - Core Infrastructure

Provides event-driven publish/subscribe system for the trading engine.
Enables decoupled, reactive architecture where agents respond to specific triggers.

Event Types:
- NEW_TICK: Price update received
- CANDLE_CLOSE: New candle formed on any timeframe
- SESSION_BOUNDARY: Market session change (Asian/London/NY)
- POSITION_UPDATE: Trade opened, closed, or modified
- RISK_EVENT: Drawdown threshold breached or risk state changed
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import MetaTrader5 as mt5

logger = logging.getLogger("Titan.EventBus")


# =============================================================================
# EVENT TYPES
# =============================================================================

class EventType(Enum):
    """All possible event types in the system"""
    NEW_TICK = "NEW_TICK"
    CANDLE_CLOSE = "CANDLE_CLOSE"
    SESSION_BOUNDARY = "SESSION_BOUNDARY"
    POSITION_UPDATE = "POSITION_UPDATE"
    RISK_EVENT = "RISK_EVENT"
    SIGNAL_GENERATED = "SIGNAL_GENERATED"
    TRADE_EXECUTED = "TRADE_EXECUTED"
    SYSTEM_HEARTBEAT = "SYSTEM_HEARTBEAT"


@dataclass
class Event:
    """Base event structure"""
    event_type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "system"
    priority: int = 5  # 1 = highest, 10 = lowest
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)


@dataclass
class CandleCloseEvent(Event):
    """Fired when a new candle closes on any timeframe"""
    symbol: str = ""
    timeframe: str = ""
    close_price: float = 0.0
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.CANDLE_CLOSE


@dataclass
class SessionBoundaryEvent(Event):
    """Fired when market session changes"""
    new_session: str = ""  # ASIAN, LONDON, NEW_YORK, OVERLAP
    previous_session: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.SESSION_BOUNDARY


@dataclass
class RiskEvent(Event):
    """Fired when risk state changes"""
    risk_level: str = ""  # NORMAL, ELEVATED, CRITICAL, HALTED
    drawdown_percent: float = 0.0
    reason: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = EventType.RISK_EVENT


# =============================================================================
# EVENT BUS
# =============================================================================

class EventBus:
    """
    Central event dispatcher using publish/subscribe pattern.
    
    Usage:
        bus = EventBus()
        bus.subscribe(EventType.CANDLE_CLOSE, my_handler)
        bus.publish(Event(EventType.CANDLE_CLOSE, ...))
        bus.process_pending()
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = defaultdict(list)
        self._event_queue: List[Event] = []
        self._processed_count = 0
        self._last_process_time: Optional[datetime] = None
        
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Register a handler for a specific event type"""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable) -> None:
        """Remove a handler from an event type"""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            
    def publish(self, event: Event) -> None:
        """Add an event to the queue for processing"""
        self._event_queue.append(event)
        logger.debug(f"Event queued: {event.event_type.value} from {event.source}")
        
    def publish_immediate(self, event: Event) -> None:
        """Process an event immediately, bypassing the queue"""
        self._dispatch(event)
        
    def process_pending(self) -> int:
        """
        Process all pending events in the queue.
        Returns the number of events processed.
        """
        # Sort by priority (lower = higher priority)
        self._event_queue.sort(key=lambda e: e.priority)
        
        processed = 0
        while self._event_queue:
            event = self._event_queue.pop(0)
            self._dispatch(event)
            processed += 1
            
        self._processed_count += processed
        self._last_process_time = datetime.now(timezone.utc)
        
        return processed
    
    def _dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribed handlers"""
        handlers = self._subscribers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Handler {handler.__name__} failed for {event.event_type.value}: {e}")
                
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics"""
        return {
            "total_processed": self._processed_count,
            "queue_size": len(self._event_queue),
            "subscribers": {et.value: len(handlers) for et, handlers in self._subscribers.items()},
            "last_process_time": self._last_process_time
        }
    
    def clear_queue(self) -> int:
        """Clear all pending events. Returns count of cleared events."""
        count = len(self._event_queue)
        self._event_queue.clear()
        return count


# =============================================================================
# TRIGGER DETECTOR
# =============================================================================

class TriggerDetector:
    """
    Detects trading triggers and generates events.
    
    Monitors:
    - Candle closes across multiple timeframes
    - Session boundaries (London Open, NY Open, etc.)
    - Position changes
    - Risk events
    """
    
    # Session definitions (UTC hours)
    SESSIONS = {
        "ASIAN": (0, 8),       # 00:00 - 08:00 UTC
        "LONDON": (8, 12),     # 08:00 - 12:00 UTC
        "OVERLAP": (12, 16),   # 12:00 - 16:00 UTC (London + NY)
        "NEW_YORK": (16, 21),  # 16:00 - 21:00 UTC
        "CLOSED": (21, 24),    # 21:00 - 00:00 UTC (low liquidity)
    }
    
    # MT5 timeframe mapping
    TIMEFRAMES = {
        "M1": (mt5.TIMEFRAME_M1, 60),
        "M5": (mt5.TIMEFRAME_M5, 300),
        "M15": (mt5.TIMEFRAME_M15, 900),
        "M30": (mt5.TIMEFRAME_M30, 1800),
        "H1": (mt5.TIMEFRAME_H1, 3600),
        "H4": (mt5.TIMEFRAME_H4, 14400),
        "D1": (mt5.TIMEFRAME_D1, 86400),
    }
    
    def __init__(self, monitored_timeframes: List[str] = None):
        self.monitored_timeframes = monitored_timeframes or ["M15", "H1", "H4"]
        self._last_candle_times: Dict[str, Dict[str, datetime]] = defaultdict(dict)
        self._last_session: str = ""
        self._last_positions: set = set()
        self._initialized = False
        
    def initialize(self, symbols: List[str]) -> None:
        """Initialize tracking for given symbols"""
        for symbol in symbols:
            for tf in self.monitored_timeframes:
                self._last_candle_times[symbol][tf] = self._get_last_candle_time(symbol, tf)
        self._last_session = self._get_current_session()
        self._last_positions = self._get_position_tickets()
        self._initialized = True
        logger.info(f"TriggerDetector initialized for {len(symbols)} symbols, TFs: {self.monitored_timeframes}")
        
    def scan(self, symbols: List[str]) -> List[Event]:
        """
        Scan for all triggers and return list of events.
        Call this every tick/second.
        """
        if not self._initialized:
            self.initialize(symbols)
            
        events = []
        
        # 1. Check for candle closes
        candle_events = self._detect_candle_closes(symbols)
        events.extend(candle_events)
        
        # 2. Check for session boundaries
        session_event = self._detect_session_boundary()
        if session_event:
            events.append(session_event)
            
        # 3. Check for position updates
        position_events = self._detect_position_updates()
        events.extend(position_events)
        
        return events
    
    def _detect_candle_closes(self, symbols: List[str]) -> List[CandleCloseEvent]:
        """Detect new candle closes across all monitored timeframes"""
        events = []
        
        for symbol in symbols:
            for tf in self.monitored_timeframes:
                current_time = self._get_last_candle_time(symbol, tf)
                last_time = self._last_candle_times[symbol].get(tf)
                
                if last_time and current_time and current_time > last_time:
                    # New candle closed!
                    close_price = self._get_close_price(symbol, tf)
                    
                    event = CandleCloseEvent(
                        event_type=EventType.CANDLE_CLOSE,
                        timestamp=datetime.now(timezone.utc),
                        data={
                            "symbol": symbol,
                            "timeframe": tf,
                            "close_price": close_price,
                            "candle_time": current_time
                        },
                        source="TriggerDetector",
                        priority=3 if tf in ["H1", "H4"] else 5,
                        symbol=symbol,
                        timeframe=tf,
                        close_price=close_price
                    )
                    events.append(event)
                    logger.info(f"🕯️ New {tf} candle closed: {symbol} @ {close_price}")
                    
                self._last_candle_times[symbol][tf] = current_time
                
        return events
    
    def _detect_session_boundary(self) -> Optional[SessionBoundaryEvent]:
        """Detect when market session changes"""
        current_session = self._get_current_session()
        
        if current_session != self._last_session and self._last_session:
            event = SessionBoundaryEvent(
                event_type=EventType.SESSION_BOUNDARY,
                timestamp=datetime.now(timezone.utc),
                data={
                    "new_session": current_session,
                    "previous_session": self._last_session
                },
                source="TriggerDetector",
                priority=2,  # High priority
                new_session=current_session,
                previous_session=self._last_session
            )
            logger.info(f"🌍 Session Change: {self._last_session} → {current_session}")
            self._last_session = current_session
            return event
            
        self._last_session = current_session
        return None
    
    def _detect_position_updates(self) -> List[Event]:
        """Detect when positions are opened or closed"""
        events = []
        current_positions = self._get_position_tickets()
        
        # New positions
        new_tickets = current_positions - self._last_positions
        for ticket in new_tickets:
            events.append(Event(
                event_type=EventType.POSITION_UPDATE,
                timestamp=datetime.now(timezone.utc),
                data={"ticket": ticket, "action": "OPENED"},
                source="TriggerDetector",
                priority=1  # Highest priority
            ))
            logger.info(f"📈 Position Opened: #{ticket}")
            
        # Closed positions
        closed_tickets = self._last_positions - current_positions
        for ticket in closed_tickets:
            events.append(Event(
                event_type=EventType.POSITION_UPDATE,
                timestamp=datetime.now(timezone.utc),
                data={"ticket": ticket, "action": "CLOSED"},
                source="TriggerDetector",
                priority=1
            ))
            logger.info(f"📉 Position Closed: #{ticket}")
            
        self._last_positions = current_positions
        return events
    
    def _get_last_candle_time(self, symbol: str, timeframe: str) -> Optional[datetime]:
        """Get the timestamp of the last closed candle"""
        try:
            tf_code = self.TIMEFRAMES.get(timeframe, (mt5.TIMEFRAME_H1, 3600))[0]
            rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, 1)
            if rates is not None and len(rates) > 0:
                return datetime.fromtimestamp(rates[0]['time'], tz=timezone.utc)
        except Exception as e:
            logger.debug(f"Could not get candle time for {symbol} {timeframe}: {e}")
        return None
    
    def _get_close_price(self, symbol: str, timeframe: str) -> float:
        """Get the close price of the last candle"""
        try:
            tf_code = self.TIMEFRAMES.get(timeframe, (mt5.TIMEFRAME_H1, 3600))[0]
            rates = mt5.copy_rates_from_pos(symbol, tf_code, 0, 1)
            if rates is not None and len(rates) > 0:
                return rates[0]['close']
        except Exception:
            pass
        return 0.0
    
    def _get_current_session(self) -> str:
        """Determine current market session based on UTC time"""
        now_utc = datetime.now(timezone.utc)
        hour = now_utc.hour
        
        for session_name, (start, end) in self.SESSIONS.items():
            if start <= hour < end:
                return session_name
        return "CLOSED"
    
    def _get_position_tickets(self) -> set:
        """Get all current position ticket numbers"""
        try:
            positions = mt5.positions_get()
            if positions:
                return {p.ticket for p in positions}
        except Exception:
            pass
        return set()


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_risk_event(level: str, drawdown: float, reason: str) -> RiskEvent:
    """Factory function to create risk events"""
    return RiskEvent(
        event_type=EventType.RISK_EVENT,
        timestamp=datetime.now(timezone.utc),
        data={
            "risk_level": level,
            "drawdown_percent": drawdown,
            "reason": reason
        },
        source="RiskManager",
        priority=1,  # Highest priority
        risk_level=level,
        drawdown_percent=drawdown,
        reason=reason
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Demo
    bus = EventBus()
    
    def on_candle_close(event: Event):
        print(f"Handler received: {event.data}")
    
    bus.subscribe(EventType.CANDLE_CLOSE, on_candle_close)
    
    # Simulate event
    test_event = CandleCloseEvent(
        event_type=EventType.CANDLE_CLOSE,
        timestamp=datetime.now(timezone.utc),
        data={"symbol": "EURUSD", "timeframe": "H1"},
        symbol="EURUSD",
        timeframe="H1",
        close_price=1.0850
    )
    
    bus.publish(test_event)
    bus.process_pending()
    
    print("\nStats:", bus.get_stats())
