"""
Orchestration Controller
========================
QuantAI Architecture - Central Command

The Orchestrator is the "brain" that coordinates all agents and routes events
to appropriate handlers. It ensures:

1. Events are routed to the correct agents
2. Signals are deduplicated (no duplicate trades on same symbol)
3. Over-evaluation is throttled
4. Agent execution follows proper dependency order

Pipeline Flow:
    Event → Orchestrator → [Agents] → Execution Decision → Trade Command
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

from titan_system.core.event_bus import Event, EventType, EventBus, TriggerDetector

logger = logging.getLogger("Titan.Orchestrator")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Signal:
    """Represents a trading signal from any agent"""
    symbol: str
    direction: str  # BUY, SELL, HOLD
    source: str     # Which agent generated this
    score: float    # 0-100
    timestamp: datetime
    setup_type: str = ""
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    confidence: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    invalidation: str = ""
    expected_r: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "source": self.source,
            "score": self.score,
            "setup_type": self.setup_type,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "confidence": self.confidence,
            "reasoning": self.reasoning
        }


class TradeState(Enum):
    """Trade quality classification"""
    EXCELLENT = "EXCELLENT"    # 90-100 score, all systems aligned
    ACCEPTABLE = "ACCEPTABLE"  # 70-89 score, minor concerns
    WARNING = "WARNING"        # 50-69 score, proceed with caution
    INVALID = "INVALID"        # <50 or blocked by risk


@dataclass
class ExecutionCommand:
    """Final trade command after all validation"""
    symbol: str
    action: str  # BUY, SELL, SKIP
    state: TradeState
    lot_size: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    final_score: float = 0.0
    reasoning: List[str] = field(default_factory=list)
    blocked_reason: str = ""


@dataclass
class ThrottleEntry:
    """Tracks throttle state for a symbol"""
    last_signal_time: datetime
    last_trade_time: Optional[datetime] = None
    signal_count_hour: int = 0
    trade_count_session: int = 0


# =============================================================================
# ORCHESTRATOR
# =============================================================================

class Orchestrator:
    """
    Central coordination hub for all agents.
    
    Responsibilities:
    1. Route events to appropriate agents
    2. Deduplicate signals
    3. Throttle over-evaluation
    4. Maintain execution pipeline
    """
    
    # Configuration
    SIGNAL_COOLDOWN_MINUTES = 60      # Min time between signals for same symbol
    MAX_SIGNALS_PER_HOUR = 5          # Max signals per hour per symbol
    MAX_TRADES_PER_SESSION = 3        # Max trades per session per symbol
    
    # Score thresholds
    EXCELLENT_THRESHOLD = 90
    ACCEPTABLE_THRESHOLD = 70
    WARNING_THRESHOLD = 50
    
    def __init__(self, event_bus: EventBus = None):
        self.event_bus = event_bus or EventBus()
        
        # Signal management
        self._signal_cache: Dict[str, Signal] = {}  # symbol -> last signal
        self._signal_history: List[Signal] = []     # Recent signals for analysis
        self._throttle_tracker: Dict[str, ThrottleEntry] = defaultdict(
            lambda: ThrottleEntry(last_signal_time=datetime.min.replace(tzinfo=timezone.utc))
        )
        
        # Execution tracking
        self._pending_commands: List[ExecutionCommand] = []
        self._executed_today: Set[str] = set()  # symbol+direction combos executed today
        
        # Stats
        self._stats = {
            "signals_received": 0,
            "signals_deduplicated": 0,
            "signals_throttled": 0,
            "commands_generated": 0,
            "trades_executed": 0
        }
        
        # Register event handlers
        self._register_handlers()
        
    def _register_handlers(self):
        """Register handlers for different event types"""
        self.event_bus.subscribe(EventType.CANDLE_CLOSE, self._on_candle_close)
        self.event_bus.subscribe(EventType.SESSION_BOUNDARY, self._on_session_boundary)
        self.event_bus.subscribe(EventType.POSITION_UPDATE, self._on_position_update)
        self.event_bus.subscribe(EventType.RISK_EVENT, self._on_risk_event)
        
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_candle_close(self, event: Event):
        """Handle candle close events - main analysis trigger"""
        symbol = event.data.get("symbol")
        timeframe = event.data.get("timeframe")
        
        logger.info(f"[ORCHESTRATOR] Candle close received: {symbol} {timeframe}")
        
        # Higher timeframes trigger full analysis
        if timeframe in ["H1", "H4"]:
            # This would trigger the analysis pipeline
            # Actual agent calls would be added here
            pass
            
    def _on_session_boundary(self, event: Event):
        """Handle session changes"""
        new_session = event.data.get("new_session")
        prev_session = event.data.get("previous_session")
        
        logger.info(f"[ORCHESTRATOR] Session change: {prev_session} → {new_session}")
        
        # Reset session-based counters
        for symbol in self._throttle_tracker:
            self._throttle_tracker[symbol].trade_count_session = 0
            
    def _on_position_update(self, event: Event):
        """Handle position changes"""
        ticket = event.data.get("ticket")
        action = event.data.get("action")
        
        logger.info(f"[ORCHESTRATOR] Position update: #{ticket} {action}")
        
        if action == "CLOSED":
            # Update stats, trigger learning agent, etc.
            self._stats["trades_executed"] += 1
            
    def _on_risk_event(self, event: Event):
        """Handle risk state changes"""
        risk_level = event.data.get("risk_level")
        reason = event.data.get("reason")
        
        logger.warning(f"[ORCHESTRATOR] Risk event: {risk_level} - {reason}")
        
        if risk_level in ["CRITICAL", "HALTED"]:
            # Clear pending commands
            self._pending_commands.clear()
            logger.critical(f"All pending commands cleared due to risk event: {reason}")
    
    # =========================================================================
    # SIGNAL MANAGEMENT
    # =========================================================================
    
    def receive_signal(self, signal: Signal) -> Optional[Signal]:
        """
        Process an incoming signal from any agent.
        Applies deduplication and throttling.
        
        Returns the signal if it should be processed, None if filtered.
        """
        self._stats["signals_received"] += 1
        symbol = signal.symbol
        
        # 1. Deduplication Check
        if self._is_duplicate(signal):
            self._stats["signals_deduplicated"] += 1
            logger.debug(f"Signal deduplicated: {symbol} {signal.direction}")
            return None
            
        # 2. Throttle Check
        if self._is_throttled(symbol):
            self._stats["signals_throttled"] += 1
            logger.debug(f"Signal throttled: {symbol}")
            return None
            
        # 3. Update tracking
        self._signal_cache[symbol] = signal
        self._signal_history.append(signal)
        if len(self._signal_history) > 100:
            self._signal_history = self._signal_history[-100:]
            
        # Update throttle tracker
        entry = self._throttle_tracker[symbol]
        entry.last_signal_time = signal.timestamp
        entry.signal_count_hour += 1
        
        logger.info(f"✅ Signal accepted: {symbol} {signal.direction} (Score: {signal.score})")
        return signal
    
    def _is_duplicate(self, signal: Signal) -> bool:
        """
        Check if this signal is a duplicate of a recent one.
        Duplicate = same symbol + direction within cooldown period.
        """
        cached = self._signal_cache.get(signal.symbol)
        if not cached:
            return False
            
        # Same direction?
        if cached.direction != signal.direction:
            return False  # Different direction, not a duplicate
            
        # Within cooldown?
        time_diff = (signal.timestamp - cached.timestamp).total_seconds() / 60
        if time_diff < self.SIGNAL_COOLDOWN_MINUTES:
            return True
            
        return False
    
    def _is_throttled(self, symbol: str) -> bool:
        """Check if signal processing is throttled for this symbol"""
        entry = self._throttle_tracker[symbol]
        
        # Check hourly limit
        # Reset counter if it's been over an hour
        now = datetime.now(timezone.utc)
        if (now - entry.last_signal_time).total_seconds() > 3600:
            entry.signal_count_hour = 0
            
        if entry.signal_count_hour >= self.MAX_SIGNALS_PER_HOUR:
            return True
            
        # Check session trade limit
        if entry.trade_count_session >= self.MAX_TRADES_PER_SESSION:
            return True
            
        return False
    
    # =========================================================================
    # EXECUTION PIPELINE
    # =========================================================================
    
    def classify_trade_state(self, score: float, risk_blocked: bool = False) -> TradeState:
        """Classify signal into trade state category"""
        if risk_blocked or score < self.WARNING_THRESHOLD:
            return TradeState.INVALID
        elif score >= self.EXCELLENT_THRESHOLD:
            return TradeState.EXCELLENT
        elif score >= self.ACCEPTABLE_THRESHOLD:
            return TradeState.ACCEPTABLE
        else:
            return TradeState.WARNING
    
    def generate_execution_command(
        self,
        signal: Signal,
        risk_approved: bool = True,
        adjusted_lot: float = 0.01
    ) -> ExecutionCommand:
        """
        Generate final execution command from validated signal.
        This is called after all agents have contributed.
        """
        # Classify trade state
        state = self.classify_trade_state(signal.score, not risk_approved)
        
        # Determine action
        if state == TradeState.INVALID:
            action = "SKIP"
            blocked_reason = "Score below threshold" if signal.score < self.WARNING_THRESHOLD else "Risk blocked"
        elif state == TradeState.WARNING:
            action = "SKIP"  # Could also be "ALERT" for monitoring
            blocked_reason = "Score in warning zone"
        else:
            action = signal.direction
            blocked_reason = ""
        
        command = ExecutionCommand(
            symbol=signal.symbol,
            action=action,
            state=state,
            lot_size=adjusted_lot if action in ["BUY", "SELL"] else 0.0,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
            final_score=signal.score,
            reasoning=signal.reasoning.copy(),
            blocked_reason=blocked_reason
        )
        
        self._stats["commands_generated"] += 1
        
        # Log decision
        state_emoji = {
            TradeState.EXCELLENT: "🌟",
            TradeState.ACCEPTABLE: "✅",
            TradeState.WARNING: "⚠️",
            TradeState.INVALID: "❌"
        }
        logger.info(
            f"{state_emoji.get(state, '❓')} [{state.value}] {signal.symbol} {action} "
            f"(Score: {signal.score:.1f})"
        )
        
        return command
    
    def record_trade_execution(self, symbol: str, direction: str):
        """Record that a trade was executed (for throttle tracking)"""
        entry = self._throttle_tracker[symbol]
        entry.last_trade_time = datetime.now(timezone.utc)
        entry.trade_count_session += 1
        self._executed_today.add(f"{symbol}_{direction}")
        self._stats["trades_executed"] += 1
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def get_signal_for_symbol(self, symbol: str) -> Optional[Signal]:
        """Get the most recent signal for a symbol"""
        return self._signal_cache.get(symbol)
    
    def get_recent_signals(self, count: int = 10) -> List[Signal]:
        """Get recent signals"""
        return self._signal_history[-count:]
    
    def reset_daily(self):
        """Reset daily counters (call at market open)"""
        self._executed_today.clear()
        for entry in self._throttle_tracker.values():
            entry.signal_count_hour = 0
            entry.trade_count_session = 0
        logger.info("[ORCHESTRATOR] Daily counters reset")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get orchestrator statistics"""
        return {
            **self._stats,
            "cached_signals": len(self._signal_cache),
            "history_size": len(self._signal_history),
            "tracked_symbols": len(self._throttle_tracker),
            "executed_today": len(self._executed_today)
        }
    
    def print_status(self):
        """Print current orchestrator status"""
        stats = self.get_stats()
        print("\n" + "=" * 50)
        print("🎯 ORCHESTRATOR STATUS")
        print("=" * 50)
        print(f"  Signals Received:     {stats['signals_received']}")
        print(f"  Signals Deduplicated: {stats['signals_deduplicated']}")
        print(f"  Signals Throttled:    {stats['signals_throttled']}")
        print(f"  Commands Generated:   {stats['commands_generated']}")
        print(f"  Trades Executed:      {stats['trades_executed']}")
        print(f"  Cached Signals:       {stats['cached_signals']}")
        print("=" * 50 + "\n")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create orchestrator
    bus = EventBus()
    orchestrator = Orchestrator(event_bus=bus)
    
    # Simulate a signal
    signal = Signal(
        symbol="EURUSD",
        direction="BUY",
        source="TrendSurfer",
        score=85.0,
        timestamp=datetime.now(timezone.utc),
        setup_type="TCB_BULLISH",
        reasoning=["H4 trend up", "H1 pullback to EMA", "RSI > 50"]
    )
    
    # Process signal
    accepted = orchestrator.receive_signal(signal)
    
    if accepted:
        # Generate execution command
        command = orchestrator.generate_execution_command(
            signal=accepted,
            risk_approved=True,
            adjusted_lot=0.05
        )
        
        print(f"\nExecution Command:")
        print(f"  Action: {command.action}")
        print(f"  State: {command.state.value}")
        print(f"  Lot: {command.lot_size}")
        print(f"  Score: {command.final_score}")
    
    # Try duplicate signal
    print("\n--- Testing Deduplication ---")
    dup_signal = Signal(
        symbol="EURUSD",
        direction="BUY",
        source="TrendSurfer",
        score=87.0,
        timestamp=datetime.now(timezone.utc)
    )
    accepted_dup = orchestrator.receive_signal(dup_signal)
    print(f"Duplicate accepted: {accepted_dup is not None}")
    
    # Print stats
    orchestrator.print_status()
