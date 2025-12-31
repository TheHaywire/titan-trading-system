"""
Execution Decision Agent
========================
QuantAI Architecture - The Final Arbiter

The "Brain" that fuses all agent outputs into a single trade decision.
This is the ONLY component that can authorize trade execution.

Intelligence Fusion:
1. Quant Signal (from strategy analysis)
2. Macro Bias (from HTF analysis)
3. Volatility State (from regime detection)
4. Risk Approval (from risk manager)

Trade State Classification:
- EXCELLENT: 90-100 score, all systems aligned → Auto-execute
- ACCEPTABLE: 70-89 score, minor concerns → Execute with caution
- WARNING: 50-69 score, significant concerns → Alert only
- INVALID: <50 or risk blocked → No action
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Titan.ExecutionDecisionAgent")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class TradeState(Enum):
    """Trade quality classification - determines action taken"""
    EXCELLENT = "EXCELLENT"    # 90-100: Fire and forget
    ACCEPTABLE = "ACCEPTABLE"  # 70-89: Execute with standard monitoring
    WARNING = "WARNING"        # 50-69: Paper trade or alert only
    INVALID = "INVALID"        # <50 or blocked: No action


class Direction(Enum):
    """Trade direction"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class QuantSignal:
    """Signal from quantitative analysis (strategies)"""
    symbol: str
    direction: Direction
    score: float  # 0-100
    setup_type: str
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    expected_r: float = 0.0
    confidence: str = "MEDIUM"
    invalidation: str = ""
    reasoning: List[str] = field(default_factory=list)
    
    
@dataclass
class MacroBias:
    """Bias from macro/HTF analysis"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    session_quality: str  # PRIME, GOOD, MARGINAL, POOR
    htf_trend: str  # UP, DOWN, SIDEWAYS
    correlation_aligned: bool = True
    participation_allowed: bool = True
    reasoning: List[str] = field(default_factory=list)
    score_adjustment: int = 0  # -20 to +20


@dataclass
class VolatilityState:
    """Current volatility and regime state"""
    regime: str  # TREND_STRONG, TREND_WEAK, RANGE, SQUEEZE
    volatility: str  # LOW, NORMAL, HIGH, EXTREME
    atr_percentile: float = 50.0  # 0-100
    suitable_for_entry: bool = True
    lot_size_multiplier: float = 1.0
    reasoning: List[str] = field(default_factory=list)


@dataclass
class RiskApproval:
    """Approval from risk manager"""
    approved: bool = True
    max_lot_size: float = 0.01
    reason_code: str = ""
    drawdown_state: str = "NORMAL"  # NORMAL, ELEVATED, CRITICAL, HALTED
    correlation_warning: Optional[str] = None
    sl_adjustment: float = 0.0  # Additional SL buffer in points


@dataclass
class ExecutionCommand:
    """Final trade command - output of the agent"""
    symbol: str
    action: str  # BUY, SELL, SKIP, ALERT
    state: TradeState
    lot_size: float = 0.0
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    final_score: float = 0.0
    
    # Audit trail
    quant_score: float = 0.0
    macro_adjustment: int = 0
    risk_approved: bool = True
    reasoning: List[str] = field(default_factory=list)
    rejection_reason: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "state": self.state.value,
            "lot_size": self.lot_size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "final_score": self.final_score,
            "reasoning": self.reasoning,
            "rejection_reason": self.rejection_reason,
            "timestamp": self.timestamp.isoformat()
        }


# =============================================================================
# EXECUTION DECISION AGENT
# =============================================================================

class ExecutionDecisionAgent:
    """
    The Final Arbiter - Fuses all intelligence into actionable commands.
    
    This agent:
    1. Receives inputs from Quant, Macro, Volatility, and Risk agents
    2. Calculates a unified score
    3. Classifies the trade state
    4. Generates the execution command
    5. Maintains full audit trail
    """
    
    # Thresholds (configurable)
    EXCELLENT_THRESHOLD = 90
    ACCEPTABLE_THRESHOLD = 70
    WARNING_THRESHOLD = 50
    
    # Mode: LIVE executes trades, PAPER only logs
    TRADING_MODE = "LIVE"  # LIVE | PAPER | BACKTEST
    
    # Score weights
    WEIGHTS = {
        "quant": 0.60,      # 60% weight to quantitative signal
        "macro": 0.25,      # 25% weight to macro bias
        "volatility": 0.15  # 15% weight to volatility state
    }
    
    def __init__(self, trading_mode: str = "LIVE"):
        self.TRADING_MODE = trading_mode
        self._decision_log: List[ExecutionCommand] = []
        self._stats = {
            "evaluations": 0,
            "excellent_count": 0,
            "acceptable_count": 0,
            "warning_count": 0,
            "invalid_count": 0,
            "executed_count": 0
        }
        
    def evaluate(
        self,
        quant_signal: QuantSignal,
        macro_bias: MacroBias,
        volatility_state: VolatilityState,
        risk_approval: RiskApproval
    ) -> ExecutionCommand:
        """
        Main evaluation method - the ONLY way to get an execution command.
        
        Args:
            quant_signal: Signal from quantitative analysis
            macro_bias: Bias from macro/HTF analysis
            volatility_state: Current volatility state
            risk_approval: Approval from risk manager
            
        Returns:
            ExecutionCommand with final decision
        """
        self._stats["evaluations"] += 1
        symbol = quant_signal.symbol
        reasoning = []
        
        # =====================================================================
        # STEP 1: Calculate base score from quant signal
        # =====================================================================
        base_score = quant_signal.score
        reasoning.append(f"Quant Score: {base_score:.1f}")
        
        # =====================================================================
        # STEP 2: Apply macro adjustments
        # =====================================================================
        macro_score = 0
        
        # Direction alignment bonus/penalty
        if macro_bias.direction == "BULLISH" and quant_signal.direction == Direction.BUY:
            macro_score += 10
            reasoning.append("✅ Macro aligned: HTF Bullish, Signal Buy")
        elif macro_bias.direction == "BEARISH" and quant_signal.direction == Direction.SELL:
            macro_score += 10
            reasoning.append("✅ Macro aligned: HTF Bearish, Signal Sell")
        elif macro_bias.direction != "NEUTRAL":
            if (macro_bias.direction == "BULLISH" and quant_signal.direction == Direction.SELL) or \
               (macro_bias.direction == "BEARISH" and quant_signal.direction == Direction.BUY):
                macro_score -= 15
                reasoning.append("⚠️ Counter-trend trade against macro bias")
        
        # Session quality
        session_adjustments = {
            "PRIME": 5,
            "GOOD": 0,
            "MARGINAL": -5,
            "POOR": -10
        }
        session_adj = session_adjustments.get(macro_bias.session_quality, 0)
        macro_score += session_adj
        if session_adj != 0:
            reasoning.append(f"Session quality: {macro_bias.session_quality} ({session_adj:+d})")
        
        # Participation gate
        if not macro_bias.participation_allowed:
            macro_score -= 20
            reasoning.append("🚫 Market participation gate CLOSED")
        
        # Apply macro adjustment
        macro_score += macro_bias.score_adjustment
        reasoning.extend(macro_bias.reasoning)
        
        # =====================================================================
        # STEP 3: Apply volatility adjustments
        # =====================================================================
        vol_score = 0
        
        if not volatility_state.suitable_for_entry:
            vol_score -= 15
            reasoning.append(f"⚠️ Volatility unsuitable: {volatility_state.regime}")
        
        if volatility_state.volatility == "EXTREME":
            vol_score -= 10
            reasoning.append("🌪️ Extreme volatility detected")
        elif volatility_state.volatility == "LOW" and "TREND" in volatility_state.regime:
            vol_score -= 5
            reasoning.append("📉 Low volatility in trend regime")
            
        reasoning.extend(volatility_state.reasoning)
        
        # =====================================================================
        # STEP 4: Calculate final weighted score
        # =====================================================================
        final_score = (
            base_score * self.WEIGHTS["quant"] +
            (50 + macro_score) * self.WEIGHTS["macro"] +  # Normalize macro to 0-100 range
            (50 + vol_score) * self.WEIGHTS["volatility"]   # Normalize vol to 0-100 range
        )
        
        # Clamp to 0-100
        final_score = max(0, min(100, final_score))
        
        # =====================================================================
        # STEP 5: Risk gate (binary check)
        # =====================================================================
        risk_blocked = False
        if not risk_approval.approved:
            risk_blocked = True
            reasoning.append(f"🛑 RISK BLOCKED: {risk_approval.reason_code}")
        
        if risk_approval.drawdown_state in ["CRITICAL", "HALTED"]:
            risk_blocked = True
            reasoning.append(f"🛑 DRAWDOWN STATE: {risk_approval.drawdown_state}")
        
        if risk_approval.correlation_warning:
            reasoning.append(f"⚠️ {risk_approval.correlation_warning}")
            final_score -= 5  # Minor penalty
        
        # =====================================================================
        # STEP 6: Classify trade state
        # =====================================================================
        state = self._classify_state(final_score, risk_blocked)
        
        # Update stats
        state_stats = {
            TradeState.EXCELLENT: "excellent_count",
            TradeState.ACCEPTABLE: "acceptable_count",
            TradeState.WARNING: "warning_count",
            TradeState.INVALID: "invalid_count"
        }
        self._stats[state_stats[state]] += 1
        
        # =====================================================================
        # STEP 7: Determine action
        # =====================================================================
        action, rejection_reason = self._determine_action(
            state, quant_signal.direction, risk_blocked
        )
        
        if rejection_reason:
            reasoning.append(f"❌ {rejection_reason}")
        
        # =====================================================================
        # STEP 8: Calculate position size
        # =====================================================================
        lot_size = 0.0
        if action in ["BUY", "SELL"]:
            lot_size = self._calculate_lot_size(
                risk_approval.max_lot_size,
                volatility_state.lot_size_multiplier,
                state
            )
            self._stats["executed_count"] += 1
        
        # =====================================================================
        # STEP 9: Adjust SL if needed
        # =====================================================================
        adjusted_sl = quant_signal.stop_loss
        if risk_approval.sl_adjustment > 0:
            # Widen SL based on risk manager recommendation
            if quant_signal.direction == Direction.BUY:
                adjusted_sl -= risk_approval.sl_adjustment
            else:
                adjusted_sl += risk_approval.sl_adjustment
            reasoning.append(f"SL widened by {risk_approval.sl_adjustment:.1f} pts (risk adjustment)")
        
        # =====================================================================
        # STEP 10: Generate execution command
        # =====================================================================
        command = ExecutionCommand(
            symbol=symbol,
            action=action,
            state=state,
            lot_size=lot_size,
            entry_price=quant_signal.entry_price,
            stop_loss=adjusted_sl,
            take_profit=quant_signal.take_profit,
            final_score=final_score,
            quant_score=base_score,
            macro_adjustment=macro_score,
            risk_approved=risk_approval.approved,
            reasoning=reasoning,
            rejection_reason=rejection_reason
        )
        
        # Log decision
        self._decision_log.append(command)
        if len(self._decision_log) > 100:
            self._decision_log = self._decision_log[-100:]
        
        # Print decision
        self._log_decision(command)
        
        return command
    
    def _classify_state(self, score: float, risk_blocked: bool) -> TradeState:
        """Classify the trade into a state category"""
        if risk_blocked or score < self.WARNING_THRESHOLD:
            return TradeState.INVALID
        elif score >= self.EXCELLENT_THRESHOLD:
            return TradeState.EXCELLENT
        elif score >= self.ACCEPTABLE_THRESHOLD:
            return TradeState.ACCEPTABLE
        else:
            return TradeState.WARNING
    
    def _determine_action(
        self, 
        state: TradeState, 
        direction: Direction,
        risk_blocked: bool
    ) -> Tuple[str, str]:
        """
        Determine the action based on state and mode.
        Returns (action, rejection_reason)
        """
        if risk_blocked:
            return "SKIP", "Risk manager blocked this trade"
        
        if state == TradeState.INVALID:
            return "SKIP", "Score below minimum threshold"
        
        if state == TradeState.WARNING:
            if self.TRADING_MODE == "LIVE":
                return "ALERT", "Score in warning zone - alert only"
            else:
                return direction.value, ""  # Paper/backtest can still execute
        
        if state in [TradeState.EXCELLENT, TradeState.ACCEPTABLE]:
            return direction.value, ""
        
        return "SKIP", "Unknown state"
    
    def _calculate_lot_size(
        self,
        max_lot: float,
        vol_multiplier: float,
        state: TradeState
    ) -> float:
        """Calculate final lot size with state-based adjustment"""
        lot = max_lot * vol_multiplier
        
        # State-based scaling
        state_multipliers = {
            TradeState.EXCELLENT: 1.0,    # Full size
            TradeState.ACCEPTABLE: 0.75,  # 75% size
            TradeState.WARNING: 0.5,      # 50% size (paper only)
            TradeState.INVALID: 0.0
        }
        
        lot *= state_multipliers.get(state, 0.5)
        
        # Minimum lot
        lot = max(0.01, round(lot, 2))
        
        return lot
    
    def _log_decision(self, command: ExecutionCommand):
        """Log the trading decision with appropriate level"""
        emoji_map = {
            TradeState.EXCELLENT: "🌟",
            TradeState.ACCEPTABLE: "✅",
            TradeState.WARNING: "⚠️",
            TradeState.INVALID: "❌"
        }
        emoji = emoji_map.get(command.state, "❓")
        
        if command.action in ["BUY", "SELL"]:
            logger.info(
                f"\n{'='*60}\n"
                f"{emoji} TRADE DECISION: {command.state.value}\n"
                f"   Symbol: {command.symbol}\n"
                f"   Action: {command.action}\n"
                f"   Score: {command.final_score:.1f}/100\n"
                f"   Lot: {command.lot_size}\n"
                f"   Entry: {command.entry_price}\n"
                f"   SL: {command.stop_loss} | TP: {command.take_profit}\n"
                f"   Mode: {self.TRADING_MODE}\n"
                f"{'='*60}"
            )
        else:
            logger.info(
                f"{emoji} [{command.state.value}] {command.symbol}: {command.action} "
                f"(Score: {command.final_score:.1f}) - {command.rejection_reason or 'Filtered'}"
            )
    
    def get_recent_decisions(self, count: int = 10) -> List[ExecutionCommand]:
        """Get recent decisions"""
        return self._decision_log[-count:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total = self._stats["evaluations"]
        return {
            **self._stats,
            "mode": self.TRADING_MODE,
            "excellent_rate": self._stats["excellent_count"] / total if total > 0 else 0,
            "execution_rate": self._stats["executed_count"] / total if total > 0 else 0
        }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create agent in LIVE mode
    agent = ExecutionDecisionAgent(trading_mode="LIVE")
    
    # Simulate inputs from other agents
    quant = QuantSignal(
        symbol="EURUSD",
        direction=Direction.BUY,
        score=85.0,
        setup_type="TCB_BULLISH",
        entry_price=1.0850,
        stop_loss=1.0800,
        take_profit=1.0950,
        expected_r=2.0,
        reasoning=["H4 trend up", "H1 pullback to EMA", "RSI > 50"]
    )
    
    macro = MacroBias(
        direction="BULLISH",
        session_quality="PRIME",
        htf_trend="UP",
        correlation_aligned=True,
        participation_allowed=True,
        reasoning=["D1 higher highs", "London session active"]
    )
    
    volatility = VolatilityState(
        regime="TREND_STRONG",
        volatility="NORMAL",
        atr_percentile=60.0,
        suitable_for_entry=True,
        lot_size_multiplier=1.0
    )
    
    risk = RiskApproval(
        approved=True,
        max_lot_size=0.05,
        drawdown_state="NORMAL"
    )
    
    # Evaluate
    command = agent.evaluate(quant, macro, volatility, risk)
    
    print(f"\n=== Final Command ===")
    print(f"Action: {command.action}")
    print(f"State: {command.state.value}")
    print(f"Lot: {command.lot_size}")
    print(f"Score: {command.final_score:.1f}")
    
    print(f"\n=== Reasoning ===")
    for r in command.reasoning:
        print(f"  • {r}")
    
    print(f"\n=== Stats ===")
    for k, v in agent.get_stats().items():
        print(f"  {k}: {v}")
