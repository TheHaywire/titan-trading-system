"""
Circuit Breaker for Trading System Safety.

The circuit breaker prevents trading when risk limits are exceeded,
protecting against:
- Excessive daily losses
- Too many consecutive losing trades
- System anomalies

Author: Titan Trading System
QuantAI Enhancement: Drawdown State Machine for nuanced risk response
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Titan.CircuitBreaker")


# =============================================================================
# DRAWDOWN STATE MACHINE (QuantAI Enhancement)
# =============================================================================

class DrawdownState(Enum):
    """Drawdown severity levels with different response actions"""
    NORMAL = "NORMAL"       # DD < 2% - Full trading
    ELEVATED = "ELEVATED"   # DD 2-4% - Reduced size, tighter filters
    CRITICAL = "CRITICAL"   # DD 4-5% - Minimal trading, best setups only
    HALTED = "HALTED"       # DD >= 5% - No new trades


@dataclass
class StateTransition:
    """Record of a state transition"""
    from_state: DrawdownState
    to_state: DrawdownState
    drawdown_percent: float
    timestamp: datetime
    reason: str


class DrawdownStateMachine:
    """
    Nuanced drawdown response instead of binary trip/reset.
    
    State Transitions:
    - NORMAL → ELEVATED: DD crosses 2%
    - ELEVATED → CRITICAL: DD crosses 4%
    - CRITICAL → HALTED: DD crosses 5%
    
    Recovery requires hysteresis (must improve by 0.5% to step down)
    """
    
    # Thresholds
    ELEVATED_THRESHOLD = 2.0   # 2%
    CRITICAL_THRESHOLD = 4.0   # 4%
    HALTED_THRESHOLD = 5.0     # 5%
    RECOVERY_HYSTERESIS = 0.5  # Must improve 0.5% to step down
    
    # Actions per state
    STATE_ACTIONS = {
        DrawdownState.NORMAL: {
            "lot_multiplier": 1.0,
            "min_score": 70,
            "allow_new_trades": True
        },
        DrawdownState.ELEVATED: {
            "lot_multiplier": 0.5,
            "min_score": 80,
            "allow_new_trades": True
        },
        DrawdownState.CRITICAL: {
            "lot_multiplier": 0.25,
            "min_score": 90,
            "allow_new_trades": True
        },
        DrawdownState.HALTED: {
            "lot_multiplier": 0.0,
            "min_score": 100,
            "allow_new_trades": False
        }
    }
    
    def __init__(self):
        self.current_state = DrawdownState.NORMAL
        self.transition_history: List[StateTransition] = []
        self.peak_equity: float = 0.0
        self._last_dd: float = 0.0
        
    def update(self, current_equity: float, starting_equity: float) -> Tuple[DrawdownState, Optional[str]]:
        """
        Update state based on current drawdown.
        
        Returns:
            Tuple of (current_state, transition_message if state changed else None)
        """
        if starting_equity <= 0:
            return self.current_state, None
            
        # Track peak for recovery
        self.peak_equity = max(self.peak_equity, current_equity)
        
        # Calculate current drawdown from starting equity
        dd_percent = ((starting_equity - current_equity) / starting_equity) * 100
        self._last_dd = dd_percent
        
        # Determine target state
        if dd_percent >= self.HALTED_THRESHOLD:
            target_state = DrawdownState.HALTED
        elif dd_percent >= self.CRITICAL_THRESHOLD:
            target_state = DrawdownState.CRITICAL
        elif dd_percent >= self.ELEVATED_THRESHOLD:
            target_state = DrawdownState.ELEVATED
        else:
            target_state = DrawdownState.NORMAL
        
        # Check for state change
        if target_state != self.current_state:
            # Worsening: immediate transition
            if self._is_worsening(target_state):
                return self._transition(target_state, dd_percent, "Drawdown increased")
            
            # Improving: require hysteresis
            recovery_threshold = self._get_recovery_threshold()
            if dd_percent <= recovery_threshold:
                return self._transition(target_state, dd_percent, "Drawdown recovered")
        
        return self.current_state, None
    
    def _is_worsening(self, target: DrawdownState) -> bool:
        """Check if target state is worse than current"""
        order = [DrawdownState.NORMAL, DrawdownState.ELEVATED, 
                 DrawdownState.CRITICAL, DrawdownState.HALTED]
        return order.index(target) > order.index(self.current_state)
    
    def _get_recovery_threshold(self) -> float:
        """Get drawdown threshold required to step down (with hysteresis)"""
        if self.current_state == DrawdownState.HALTED:
            return self.CRITICAL_THRESHOLD - self.RECOVERY_HYSTERESIS
        elif self.current_state == DrawdownState.CRITICAL:
            return self.ELEVATED_THRESHOLD - self.RECOVERY_HYSTERESIS
        elif self.current_state == DrawdownState.ELEVATED:
            return self.ELEVATED_THRESHOLD - self.RECOVERY_HYSTERESIS
        return 0.0
    
    def _transition(self, new_state: DrawdownState, dd: float, reason: str) -> Tuple[DrawdownState, str]:
        """Execute state transition"""
        old_state = self.current_state
        self.current_state = new_state
        
        transition = StateTransition(
            from_state=old_state,
            to_state=new_state,
            drawdown_percent=dd,
            timestamp=datetime.now(timezone.utc),
            reason=reason
        )
        self.transition_history.append(transition)
        
        # Keep only last 50 transitions
        if len(self.transition_history) > 50:
            self.transition_history = self.transition_history[-50:]
        
        message = f"Risk State: {old_state.value} → {new_state.value} (DD: {dd:.2f}%)"
        
        if new_state == DrawdownState.HALTED:
            logger.critical(f"🚨 {message}")
        elif new_state == DrawdownState.CRITICAL:
            logger.error(f"⚠️ {message}")
        elif new_state == DrawdownState.ELEVATED:
            logger.warning(f"📉 {message}")
        else:
            logger.info(f"✅ {message}")
        
        return new_state, message
    
    def get_actions(self) -> Dict:
        """Get current actions based on state"""
        return self.STATE_ACTIONS.get(self.current_state, self.STATE_ACTIONS[DrawdownState.HALTED])
    
    def get_status(self) -> Dict:
        """Get current state machine status"""
        actions = self.get_actions()
        return {
            "state": self.current_state.value,
            "current_drawdown": self._last_dd,
            "lot_multiplier": actions["lot_multiplier"],
            "min_score": actions["min_score"],
            "allow_new_trades": actions["allow_new_trades"],
            "transition_count": len(self.transition_history),
            "peak_equity": self.peak_equity
        }
    
    def reset(self):
        """Reset state machine"""
        self.current_state = DrawdownState.NORMAL
        self.peak_equity = 0.0
        self._last_dd = 0.0
        logger.info("Drawdown State Machine reset to NORMAL")


# =============================================================================
# CIRCUIT BREAKER STATS
# =============================================================================

@dataclass
class CircuitBreakerStats:
    """Statistics tracked by the circuit breaker."""
    consecutive_losses: int = 0
    daily_start_equity: Optional[float] = None
    last_reset_date: datetime = field(default_factory=lambda: datetime.now().date())
    trip_count_today: int = 0
    total_trips: int = 0
    last_trip_reason: str = ""
    last_trip_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit breaker to prevent trading when risk limits are exceeded.
    
    Monitors:
    - Daily equity drawdown percentage
    - Consecutive losing trades  
    - Maximum total exposure
    - Trading hours (optional)
    
    When triggered, the circuit breaker will:
    - Stop all new trade entries
    - Optionally close existing positions
    - Log critical alerts
    - Can only be reset manually or at daily reset
    
    Example:
        >>> breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        >>> safe, reason = breaker.check_safe_to_trade(account_info)
        >>> if not safe:
        ...     print(f"Trading stopped: {reason}")
    """
    
    def __init__(
        self,
        max_daily_loss_percent: float = 3.0,
        max_consecutive_losses: int = 5,
        max_total_exposure_percent: float = 10000.0, # EMERGENCY OVERRIDE
        auto_reset_daily: bool = True
    ):
        """
        Initialize the circuit breaker.
        
        Args:
            max_daily_loss_percent: Maximum daily loss % before tripping (default: 5%)
            max_consecutive_losses: Max consecutive losing trades (default: 5)
            max_total_exposure_percent: Max total position exposure % (default: 50%)
            auto_reset_daily: Automatically reset at midnight (default: True)
        """
        self.max_daily_loss = max_daily_loss_percent
        self.max_consecutive_losses = max_consecutive_losses
        self.max_exposure = max_total_exposure_percent
        self.auto_reset_daily = auto_reset_daily
        
        self.tripped = False
        self.trip_reason = ""
        self.stats = CircuitBreakerStats()
        
        logger.info(
            f"🛡️  Circuit Breaker initialized | "
            f"Max Daily Loss: {max_daily_loss_percent}% | "
            f"Max Consecutive Losses: {max_consecutive_losses}"
        )
    
    def check_safe_to_trade(self, account_info: Dict) -> Tuple[bool, str]:
        """
        Check if it's safe to continue trading.
        
        Args:
            account_info: Dictionary containing:
                - equity: Current account equity
                - balance: Account balance
                - margin: Used margin
                - free_margin: Available margin
                - positions: List of open positions (optional)
        
        Returns:
            Tuple of (is_safe, reason)
            - is_safe: True if trading is allowed
            - reason: Explanation of status
        """
        # Auto-reset at midnight if enabled
        if self.auto_reset_daily:
            today = datetime.now().date()
            if today > self.stats.last_reset_date:
                self._reset_daily()
        
        # If already tripped, stay tripped (manual reset required)
        if self.tripped:
            return False, f"🔴 CIRCUIT BREAKER ACTIVE: {self.trip_reason}"
        
        # Initialize daily starting equity on first check of the day
        if self.stats.daily_start_equity is None:
            self.stats.daily_start_equity = account_info.get('equity', 0)
            logger.info(f"📊 Daily start equity set: ${self.stats.daily_start_equity:,.2f}")
        
        # === CHECK 1: Daily Loss Limit ===
        current_equity = account_info.get('equity', 0)
        
        # SAFEGUARD: Ignore 0.0 equity (likely MT5 init error, not actual bankruptcy)
        if current_equity < 1.0:
             return True, "⚠️ Waiting for Account Data..."
             
        if self.stats.daily_start_equity > 0:
            daily_loss_pct = (
                (self.stats.daily_start_equity - current_equity) / 
                self.stats.daily_start_equity * 100
            )
            
            if daily_loss_pct > self.max_daily_loss:
                self._trip(
                    f"Daily loss limit exceeded: {daily_loss_pct:.2f}% "
                    f"(limit: {self.max_daily_loss}%)"
                )
                return False, self.trip_reason
            
            if daily_loss_pct > self.max_daily_loss * 0.75:
                logger.warning(
                    f"⚠️  Approaching daily loss limit: {daily_loss_pct:.2f}% "
                    f"of {self.max_daily_loss}%"
                )
        
        # === CHECK 2: Consecutive Losses ===
        if self.stats.consecutive_losses >= self.max_consecutive_losses:
            self._trip(
                f"Too many consecutive losses: {self.stats.consecutive_losses} "
                f"(limit: {self.max_consecutive_losses})"
            )
            return False, self.trip_reason
        
        if self.stats.consecutive_losses >= self.max_consecutive_losses - 1:
            logger.warning(
                f"⚠️  One loss away from circuit breaker: "
                f"{self.stats.consecutive_losses}/{self.max_consecutive_losses}"
            )
        
        # === CHECK 3: Total Exposure (optional) ===
        if 'positions' in account_info and account_info['positions']:
            positions = account_info['positions']
            balance = account_info.get('balance', 1)
            
            # Calculate total exposure as percentage of balance
            total_volume = sum(p.get('volume', 0) for p in positions)
            # Simplified: assuming each lot ~= 100,000 units
            total_exposure_value = total_volume * 100000
            
            if balance > 0:
                exposure_pct = (total_exposure_value / balance) * 100
                
                if exposure_pct > self.max_exposure:
                    self._trip(
                        f"Total exposure too high: {exposure_pct:.1f}% "
                        f"(limit: {self.max_exposure}%)"
                    )
                    return False, self.trip_reason
        
        # All checks passed
        return True, "✅ All systems green"
    
    def record_trade_result(self, profit: float, symbol: str = ""):
        """
        Record a trade result to track consecutive losses.
        
        Args:
            profit: Trade profit/loss (negative for loss)
            symbol: Symbol traded (optional, for logging)
        """
        if profit < 0:
            self.stats.consecutive_losses += 1
            logger.warning(
                f"📉 Loss recorded for {symbol or 'trade'}: ${profit:.2f} | "
                f"Consecutive losses: {self.stats.consecutive_losses}"
            )
        else:
            if self.stats.consecutive_losses > 0:
                logger.info(
                    f"✅ Win breaks losing streak! "
                    f"Previous consecutive losses: {self.stats.consecutive_losses}"
                )
            self.stats.consecutive_losses = 0
            logger.info(f"📈 Win recorded for {symbol or 'trade'}: ${profit:.2f}")
    
    def _trip(self, reason: str):
        """Trip the circuit breaker."""
        if not self.tripped:
            self.tripped = True
            self.trip_reason = reason
            self.stats.trip_count_today += 1
            self.stats.total_trips += 1
            self.stats.last_trip_reason = reason
            self.stats.last_trip_time = datetime.now()
            
            logger.critical("=" * 70)
            logger.critical(f"🚨 CIRCUIT BREAKER TRIPPED 🚨")
            logger.critical(f"Reason: {reason}")
            logger.critical(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.critical(f"Trip count today: {self.stats.trip_count_today}")
            logger.critical("=" * 70)
    
    def _reset_daily(self):
        """Reset daily counters at midnight."""
        logger.info("=" * 50)
        logger.info("🔄 Daily Circuit Breaker Reset")
        logger.info(f"Previous day stats:")
        logger.info(f"  - Trips: {self.stats.trip_count_today}")
        logger.info(f"  - Start Equity: ${self.stats.daily_start_equity or 0:,.2f}")
        logger.info("=" * 50)
        
        self.stats.daily_start_equity = None
        self.stats.last_reset_date = datetime.now().date()
        self.stats.trip_count_today = 0
        
        # Don't auto-reset the tripped state - requires manual reset
        if self.tripped:
            logger.warning(
                "⚠️  Circuit breaker is still TRIPPED. Manual reset required."
            )
    
    def manual_reset(self, reason: str = "Manual reset by operator"):
        """
        Manually reset the circuit breaker.
        
        Use with caution! Ensure the underlying issue is resolved.
        
        Args:
            reason: Reason for the reset (for audit trail)
        """
        logger.warning("=" * 70)
        logger.warning("⚠️  MANUAL CIRCUIT BREAKER RESET")
        logger.warning(f"Reason: {reason}")
        logger.warning(f"Previous trip reason: {self.trip_reason}")
        logger.warning(f"By: Operator at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.warning("=" * 70)
        
        self.tripped = False
        self.trip_reason = ""
        self.stats.consecutive_losses = 0
    
    def get_status(self) -> Dict:
        """
        Get current circuit breaker status.
        
        Returns:
            Dictionary with current status and statistics
        """
        return {
            "tripped": self.tripped,
            "trip_reason": self.trip_reason,
            "consecutive_losses": self.stats.consecutive_losses,
            "daily_start_equity": self.stats.daily_start_equity,
            "trip_count_today": self.stats.trip_count_today,
            "total_trips": self.stats.total_trips,
            "last_trip_time": self.stats.last_trip_time.isoformat() if self.stats.last_trip_time else None,
            "limits": {
                "max_daily_loss_percent": self.max_daily_loss,
                "max_consecutive_losses": self.max_consecutive_losses,
                "max_exposure_percent": self.max_exposure
            }
        }


# Example usage
if __name__ == "__main__":
    # Demo
    breaker = CircuitBreaker(max_daily_loss_percent=5.0, max_consecutive_losses=3)
    
    # Simulate account with starting equity
    account = {"equity": 10000, "balance": 10000}
    
    # Check 1: Should be safe
    safe, msg = breaker.check_safe_to_trade(account)
    print(f"Check 1: {safe} - {msg}")
    
    # Simulate some losses
    breaker.record_trade_result(-50, "EURUSD")
    breaker.record_trade_result(-75, "GBPUSD")
    breaker.record_trade_result(-100, "USDJPY")
    
    # Check 2: Should trip on consecutive losses
    safe, msg = breaker.check_safe_to_trade(account)
    print(f"Check 2: {safe} - {msg}")
    
    print("\nStatus:", breaker.get_status())
