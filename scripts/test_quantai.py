"""
QuantAI System Verification Test
================================
Tests that all QuantAI components import and initialize correctly.

Run: python scripts/test_quantai.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all imports work"""
    print("=" * 60)
    print("🧪 Testing QuantAI System Components")
    print("=" * 60)
    
    errors = []
    
    # Test Core Infrastructure
    print("\n📦 Core Infrastructure:")
    
    try:
        from titan_system.core.event_bus import EventBus, TriggerDetector, EventType
        print("  ✅ event_bus.py")
    except Exception as e:
        print(f"  ❌ event_bus.py: {e}")
        errors.append(("event_bus", str(e)))
    
    try:
        from titan_system.core.orchestrator import Orchestrator, Signal, TradeState
        print("  ✅ orchestrator.py")
    except Exception as e:
        print(f"  ❌ orchestrator.py: {e}")
        errors.append(("orchestrator", str(e)))
    
    try:
        from titan_system.core.memory import MemorySystem, ShortTermMemory, LongTermMemory, EntityMemory
        print("  ✅ memory.py")
    except Exception as e:
        print(f"  ❌ memory.py: {e}")
        errors.append(("memory", str(e)))
    
    try:
        from titan_system.core.circuit_breaker import CircuitBreaker, DrawdownStateMachine, DrawdownState
        print("  ✅ circuit_breaker.py (with DrawdownStateMachine)")
    except Exception as e:
        print(f"  ❌ circuit_breaker.py: {e}")
        errors.append(("circuit_breaker", str(e)))
    
    # Test Agents
    print("\n🤖 Agents:")
    
    try:
        from titan_system.agents.execution_decision_agent import (
            ExecutionDecisionAgent, QuantSignal, VolatilityState, RiskApproval
        )
        print("  ✅ execution_decision_agent.py")
    except Exception as e:
        print(f"  ❌ execution_decision_agent.py: {e}")
        errors.append(("execution_decision_agent", str(e)))
    
    try:
        from titan_system.agents.macro_strategist import MacroStrategist, MacroBias
        print("  ✅ macro_strategist.py")
    except Exception as e:
        print(f"  ❌ macro_strategist.py: {e}")
        errors.append(("macro_strategist", str(e)))
    
    # Test Main Engine
    print("\n🚀 Main Engine:")
    
    try:
        from titan_system.quantai_engine import QuantAIEngine
        print("  ✅ quantai_engine.py")
    except Exception as e:
        print(f"  ❌ quantai_engine.py: {e}")
        errors.append(("quantai_engine", str(e)))
    
    return errors


def test_initialization():
    """Test component initialization"""
    print("\n🔧 Testing Initialization:")
    
    errors = []
    
    try:
        from titan_system.core.event_bus import EventBus
        bus = EventBus()
        print(f"  ✅ EventBus initialized")
    except Exception as e:
        print(f"  ❌ EventBus: {e}")
        errors.append(("EventBus init", str(e)))
    
    try:
        from titan_system.core.orchestrator import Orchestrator
        orch = Orchestrator()
        print(f"  ✅ Orchestrator initialized")
    except Exception as e:
        print(f"  ❌ Orchestrator: {e}")
        errors.append(("Orchestrator init", str(e)))
    
    try:
        from titan_system.core.memory import MemorySystem
        mem = MemorySystem()
        print(f"  ✅ MemorySystem initialized")
    except Exception as e:
        print(f"  ❌ MemorySystem: {e}")
        errors.append(("MemorySystem init", str(e)))
    
    try:
        from titan_system.core.circuit_breaker import DrawdownStateMachine
        dsm = DrawdownStateMachine()
        print(f"  ✅ DrawdownStateMachine initialized (State: {dsm.current_state.value})")
    except Exception as e:
        print(f"  ❌ DrawdownStateMachine: {e}")
        errors.append(("DrawdownStateMachine init", str(e)))
    
    try:
        from titan_system.agents.execution_decision_agent import ExecutionDecisionAgent
        agent = ExecutionDecisionAgent(trading_mode="PAPER")
        print(f"  ✅ ExecutionDecisionAgent initialized (Mode: {agent.TRADING_MODE})")
    except Exception as e:
        print(f"  ❌ ExecutionDecisionAgent: {e}")
        errors.append(("ExecutionDecisionAgent init", str(e)))
    
    try:
        from titan_system.agents.macro_strategist import MacroStrategist
        macro = MacroStrategist()
        print(f"  ✅ MacroStrategist initialized")
    except Exception as e:
        print(f"  ❌ MacroStrategist: {e}")
        errors.append(("MacroStrategist init", str(e)))
    
    return errors


def test_signal_flow():
    """Test a signal through the system"""
    print("\n🔄 Testing Signal Flow:")
    
    from datetime import datetime, timezone
    
    try:
        from titan_system.core.orchestrator import Orchestrator, Signal
        from titan_system.agents.execution_decision_agent import (
            ExecutionDecisionAgent, QuantSignal, VolatilityState, RiskApproval, Direction
        )
        from titan_system.agents.execution_decision_agent import MacroBias as MacroBiasData
        
        # Create orchestrator
        orch = Orchestrator()
        
        # Create test signal
        signal = Signal(
            symbol="EURUSD",
            direction="BUY",
            source="Test",
            score=85.0,
            timestamp=datetime.now(timezone.utc),
            setup_type="TEST_SETUP"
        )
        
        # Test deduplication
        accepted = orch.receive_signal(signal)
        print(f"  ✅ Signal accepted: {accepted is not None}")
        
        # Test duplicate rejection
        dup = orch.receive_signal(signal)
        print(f"  ✅ Duplicate rejected: {dup is None}")
        
        # Test ExecutionDecisionAgent
        agent = ExecutionDecisionAgent(trading_mode="PAPER")
        
        quant = QuantSignal(
            symbol="EURUSD",
            direction=Direction.BUY,
            score=85.0,
            setup_type="TEST",
            entry_price=1.0850,
            stop_loss=1.0800,
            take_profit=1.0950
        )
        
        macro = MacroBiasData(
            direction="BULLISH",
            session_quality="PRIME",
            htf_trend="UP"
        )
        
        vol = VolatilityState(
            regime="TREND_STRONG",
            volatility="NORMAL"
        )
        
        risk = RiskApproval(
            approved=True,
            max_lot_size=0.05
        )
        
        command = agent.evaluate(quant, macro, vol, risk)
        print(f"  ✅ Execution command generated:")
        print(f"      Action: {command.action}")
        print(f"      State: {command.state.value}")
        print(f"      Score: {command.final_score:.1f}")
        
        return []
        
    except Exception as e:
        print(f"  ❌ Signal flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return [("signal_flow", str(e))]


def main():
    """Run all tests"""
    all_errors = []
    
    # Import tests
    errors = test_imports()
    all_errors.extend(errors)
    
    # Initialization tests
    errors = test_initialization()
    all_errors.extend(errors)
    
    # Signal flow test
    errors = test_signal_flow()
    all_errors.extend(errors)
    
    # Summary
    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ FAILED: {len(all_errors)} error(s)")
        for name, error in all_errors:
            print(f"   - {name}: {error}")
    else:
        print("✅ ALL TESTS PASSED!")
        print("\n🎉 QuantAI System is ready!")
        print("\nTo start the engine:")
        print("  python -m titan_system.quantai_engine")
    print("=" * 60)
    
    return len(all_errors) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
