"""
QuantAI Agents Module
=====================
Autonomous trading agents for the institutional trading system.

Agents:
- ExecutionDecisionAgent: Final trade decision arbiter
- MacroStrategist: HTF context and bias analysis
"""

from titan_system.agents.execution_decision_agent import (
    ExecutionDecisionAgent,
    TradeState,
    Direction,
    QuantSignal,
    MacroBias as MacroBiasData,
    VolatilityState,
    RiskApproval,
    ExecutionCommand
)

from titan_system.agents.macro_strategist import (
    MacroStrategist,
    MacroBias,
    MarketDirection,
    SessionQuality
)

__all__ = [
    # Agents
    "ExecutionDecisionAgent",
    "MacroStrategist",
    
    # Data structures
    "TradeState",
    "Direction",
    "QuantSignal",
    "MacroBias",
    "MacroBiasData",
    "VolatilityState",
    "RiskApproval",
    "ExecutionCommand",
    "MarketDirection",
    "SessionQuality"
]
