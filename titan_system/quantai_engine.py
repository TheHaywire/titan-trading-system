"""
QuantAI Trading Engine
======================
Institutional Agentic Trading System - Unified Runner

This is the main entry point for the QuantAI system. It wires together:
- Event Bus (trigger detection)
- Orchestrator (agent coordination)
- Memory System (short/long/entity memory)
- Execution Decision Agent (final arbiter)
- Macro Strategist (HTF context)
- Risk Management (circuit breaker, drawdown state machine)
- MT5 Execution

Run:
    python -m titan_system.quantai_engine

Or:
    python titan_system/quantai_engine.py
"""

import asyncio
import logging
import time
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5

from config.settings import settings

# Core Infrastructure
from titan_system.core.event_bus import EventBus, TriggerDetector, EventType, Event
from titan_system.core.orchestrator import Orchestrator, Signal, TradeState
from titan_system.core.memory import MemorySystem
from titan_system.core.circuit_breaker import CircuitBreaker, DrawdownStateMachine, DrawdownState

# Agents
from titan_system.agents.execution_decision_agent import (
    ExecutionDecisionAgent, QuantSignal, VolatilityState, RiskApproval, Direction
)
from titan_system.agents.macro_strategist import MacroStrategist, MacroBias

# Existing Components
from titan_system.execution.mt5_executor import MT5Executor
from titan_system.execution.trade_manager import TradeManager
from titan_system.smc.institutional_engine import InstitutionalEngine
from titan_system.smc.volatility_engine import VolatilityEngine
from titan_system.notifications.telegram_bot import TelegramNotifier

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler("quantai.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("QuantAI")


# =============================================================================
# QUANTAI ENGINE
# =============================================================================

class QuantAIEngine:
    """
    The Unified QuantAI Trading Engine.
    
    Orchestrates all agents and systems for institutional-grade trading.
    
    Flow:
        1. Trigger Detection (candle close, session change, etc.)
        2. Event Publication
        3. Agent Pipeline:
            - Market State Building
            - Quant Signal Generation
            - Macro Bias Analysis
            - Risk Approval
            - Execution Decision
        4. Trade Execution (if approved)
        5. Post-Trade Monitoring
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, universe: List[str] = None, trading_mode: str = None):
        """
        Initialize the QuantAI Engine.
        
        Args:
            universe: List of symbols to trade
            trading_mode: LIVE, PAPER, or BACKTEST (default from settings)
        """
        self.trading_mode = trading_mode or settings.trading_mode
        
        # Universe
        self.universe = universe or [
            "EURUSD", "GBPUSD", "USDJPY", "GOLD",
            "BTCUSD", "US500", "GER40"
        ]
        
        # Core Infrastructure
        self.event_bus = EventBus()
        self.orchestrator = Orchestrator(event_bus=self.event_bus)
        self.trigger_detector = TriggerDetector(monitored_timeframes=["M15", "H1", "H4"])
        self.memory = MemorySystem()
        
        # Risk Management
        self.circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=settings.max_daily_loss_percent,
            max_consecutive_losses=5
        )
        self.drawdown_sm = DrawdownStateMachine()
        
        # Agents
        self.execution_agent = ExecutionDecisionAgent(trading_mode=self.trading_mode)
        self.macro_strategist = MacroStrategist()
        
        # Analysis Engines
        self.institutional_engine = InstitutionalEngine()
        self.volatility_engine = VolatilityEngine()
        
        # Execution
        self.executor = MT5Executor()
        self.trade_manager = TradeManager()
        self.notifier = TelegramNotifier()
        
        # State
        self.running = False
        self.cycle_count = 0
        self.last_cycle_time = None
        self._session_start_equity = 0.0
        
        # Register event handlers
        self._register_handlers()
        
        logger.info(f"🚀 QuantAI Engine v{self.VERSION} initialized")
        logger.info(f"   Mode: {self.trading_mode}")
        logger.info(f"   Universe: {len(self.universe)} symbols")
        
    def _register_handlers(self):
        """Register event handlers with the event bus"""
        self.event_bus.subscribe(EventType.CANDLE_CLOSE, self._on_candle_close)
        self.event_bus.subscribe(EventType.SESSION_BOUNDARY, self._on_session_change)
        self.event_bus.subscribe(EventType.POSITION_UPDATE, self._on_position_update)
        self.event_bus.subscribe(EventType.RISK_EVENT, self._on_risk_event)
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_candle_close(self, event: Event):
        """Handle candle close - main analysis trigger"""
        symbol = event.data.get("symbol")
        timeframe = event.data.get("timeframe")
        
        # Only analyze on H1/H4 closes
        if timeframe in ["H1", "H4"]:
            logger.info(f"📊 Analysis triggered: {symbol} {timeframe} close")
            self._analyze_symbol(symbol)
    
    def _on_session_change(self, event: Event):
        """Handle session boundary change"""
        new_session = event.data.get("new_session")
        logger.info(f"🌍 Session change: {new_session}")
        
        # Clear macro cache for fresh analysis
        self.macro_strategist.clear_cache()
        
        # Reset session counters in orchestrator
        self.orchestrator.reset_daily()
        
        # Send notification
        asyncio.create_task(self._notify(
            f"🌍 *Session Change*\n"
            f"New Session: {new_session}\n"
            f"Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"
        ))
    
    def _on_position_update(self, event: Event):
        """Handle position opened/closed"""
        action = event.data.get("action")
        ticket = event.data.get("ticket")
        
        if action == "CLOSED":
            # Update memory with trade result
            # (In production, we'd fetch the actual trade details)
            logger.info(f"📉 Position #{ticket} closed - updating memory")
    
    def _on_risk_event(self, event: Event):
        """Handle risk state changes"""
        risk_level = event.data.get("risk_level")
        reason = event.data.get("reason")
        
        if risk_level in ["CRITICAL", "HALTED"]:
            asyncio.create_task(self._notify(
                f"🚨 *RISK ALERT*\n"
                f"State: {risk_level}\n"
                f"Reason: {reason}",
                priority="CRITICAL"
            ))
    
    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def start(self):
        """Start the engine main loop"""
        self.running = True
        
        # Connect to MT5
        if not self.executor.connect():
            logger.critical("Failed to connect to MT5!")
            return
        
        # Initialize trigger detector
        self.trigger_detector.initialize(self.universe)
        
        # Get starting equity
        account = self.executor.get_account_info()
        self._session_start_equity = account.get('equity', 0)
        self.memory.short_term.update_equity(
            self._session_start_equity, 
            account.get('balance', 0)
        )
        
        logger.info(f"💰 Session Start Equity: ${self._session_start_equity:,.2f}")
        
        # Send startup notification
        await self._notify(
            f"🚀 *QuantAI Engine Started*\n"
            f"Mode: {self.trading_mode}\n"
            f"Universe: {len(self.universe)} symbols\n"
            f"Equity: ${self._session_start_equity:,.2f}"
        )
        
        # Main loop
        while self.running:
            try:
                await self._tick()
                await asyncio.sleep(1)  # 1 second tick
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                break
            except Exception as e:
                logger.error(f"Engine error: {e}")
                await asyncio.sleep(5)
        
        await self._shutdown()
    
    async def _tick(self):
        """One tick of the engine"""
        # 1. Check circuit breaker
        account = self.executor.get_account_info()
        safe, reason = self.circuit_breaker.check_safe_to_trade(account)
        
        if not safe:
            if self.cycle_count % 60 == 0:  # Log every 60 ticks
                logger.warning(f"⛔ Trading halted: {reason}")
            self.cycle_count += 1
            return
        
        # 2. Update drawdown state machine
        dd_state, transition_msg = self.drawdown_sm.update(
            account.get('equity', 0),
            self._session_start_equity
        )
        if transition_msg:
            await self._notify(f"📊 {transition_msg}")
        
        # 3. Update memory
        self.memory.short_term.update_equity(
            account.get('equity', 0),
            account.get('balance', 0)
        )
        
        # 4. Detect triggers
        events = self.trigger_detector.scan(self.universe)
        
        # 5. Publish events
        for event in events:
            self.event_bus.publish(event)
        
        # 6. Process event queue
        self.event_bus.process_pending()
        
        # 7. Manage active trades
        self.trade_manager.monitor_active_trades()
        
        self.cycle_count += 1
        self.last_cycle_time = datetime.now(timezone.utc)
    
    # =========================================================================
    # ANALYSIS PIPELINE
    # =========================================================================
    
    def _analyze_symbol(self, symbol: str):
        """
        Full analysis pipeline for a symbol.
        Called when a significant candle closes.
        """
        try:
            # 1. Get historical data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
            if rates is None or len(rates) < 50:
                logger.warning(f"Insufficient data for {symbol}")
                return
            
            import pandas as pd
            df = pd.DataFrame(rates)
            
            # 2. Run institutional analysis
            inst_analysis = self.institutional_engine.analyze_symbol(df, symbol)
            
            # Check for valid setup
            setups = inst_analysis.get('setup', [])
            if not setups:
                logger.debug(f"No setups for {symbol}")
                return
            
            # 3. Generate quant signal from best setup
            best_setup = setups[0]
            
            # Determine direction
            setup_name = best_setup.get('name', '')
            if 'BULLISH' in setup_name or 'LONG' in setup_name:
                direction = Direction.BUY
            elif 'BEARISH' in setup_name or 'SHORT' in setup_name:
                direction = Direction.SELL
            else:
                return
            
            # Calculate score based on regime and momentum
            regime = inst_analysis.get('regime', '')
            momentum = inst_analysis.get('momentum', {})
            
            base_score = 70  # Start at acceptable
            if 'STRONG' in regime:
                base_score += 15
            if momentum.get('rsi', 50) > 50 and direction == Direction.BUY:
                base_score += 5
            elif momentum.get('rsi', 50) < 50 and direction == Direction.SELL:
                base_score += 5
            
            # 4. Create quant signal
            current_price = df.iloc[-1]['close']
            quant_signal = QuantSignal(
                symbol=symbol,
                direction=direction,
                score=base_score,
                setup_type=setup_name,
                entry_price=current_price,
                stop_loss=best_setup.get('stop', current_price * 0.99),
                take_profit=best_setup.get('target', current_price * 1.02),
                expected_r=2.0,
                reasoning=[
                    f"Setup: {setup_name}",
                    f"Regime: {regime}",
                    f"RSI: {momentum.get('rsi', 'N/A')}"
                ]
            )
            
            # 5. Check with orchestrator for deduplication
            signal_obj = Signal(
                symbol=symbol,
                direction=direction.value,
                source="InstitutionalEngine",
                score=base_score,
                timestamp=datetime.now(timezone.utc),
                setup_type=setup_name
            )
            
            if not self.orchestrator.receive_signal(signal_obj):
                logger.debug(f"Signal deduplicated/throttled: {symbol}")
                return
            
            # 6. Get macro bias
            open_exposure = self.memory.short_term.get_open_exposure()
            macro_bias = self.macro_strategist.analyze(symbol, open_exposure)
            
            # Convert to agent format
            from titan_system.agents.execution_decision_agent import MacroBias as MacroBiasData
            macro_data = MacroBiasData(
                direction=macro_bias.direction,
                session_quality=macro_bias.session_quality,
                htf_trend=macro_bias.htf_trend,
                correlation_aligned=macro_bias.correlation_aligned,
                participation_allowed=macro_bias.participation_allowed,
                reasoning=macro_bias.reasoning,
                score_adjustment=macro_bias.score_adjustment
            )
            
            # 7. Get volatility state
            vol_analysis = inst_analysis.get('volatility', {})
            vol_state = VolatilityState(
                regime=vol_analysis.get('regime', 'NORMAL_VOLATILITY'),
                volatility=vol_analysis.get('state', 'NORMAL'),
                atr_percentile=vol_analysis.get('atr_percentile', 50),
                suitable_for_entry=vol_analysis.get('regime') != 'EXTREME_VOLATILITY',
                lot_size_multiplier=self.drawdown_sm.get_actions()['lot_multiplier']
            )
            
            # 8. Get risk approval
            dd_actions = self.drawdown_sm.get_actions()
            account = self.executor.get_account_info()
            
            risk_approval = RiskApproval(
                approved=dd_actions['allow_new_trades'],
                max_lot_size=0.01 * dd_actions['lot_multiplier'],  # Base 0.01 lot
                drawdown_state=self.drawdown_sm.current_state.value,
                correlation_warning=self.memory.entity.get_exposure_warning(
                    symbol, open_exposure
                )
            )
            
            # 9. Execute decision agent
            command = self.execution_agent.evaluate(
                quant_signal=quant_signal,
                macro_bias=macro_data,
                volatility_state=vol_state,
                risk_approval=risk_approval
            )
            
            # 10. Execute if approved
            if command.action in ["BUY", "SELL"] and self.trading_mode == "LIVE":
                self._execute_trade(command)
            elif command.action in ["BUY", "SELL"]:
                logger.info(f"📝 [PAPER] Would execute: {command.symbol} {command.action}")
            
        except Exception as e:
            logger.error(f"Analysis error for {symbol}: {e}")
            import traceback
            traceback.print_exc()
    
    def _execute_trade(self, command):
        """Execute a trade command"""
        try:
            result = self.executor.execute_order(
                symbol=command.symbol,
                order_type=command.action,
                lot=command.lot_size,
                sl_points=500,  # TODO: Calculate from command.stop_loss
                tp_points=1000,
                comment=f"QuantAI: {command.state.value}"
            )
            
            if result:
                # Record execution
                self.orchestrator.record_trade_execution(command.symbol, command.action)
                
                # Notify
                asyncio.create_task(self._notify(
                    f"✅ *Trade Executed*\n"
                    f"Symbol: {command.symbol}\n"
                    f"Action: {command.action}\n"
                    f"Lot: {command.lot_size}\n"
                    f"Score: {command.final_score:.1f}\n"
                    f"State: {command.state.value}",
                    priority="HIGH"
                ))
                
                logger.info(f"✅ Trade executed: {command.symbol} {command.action}")
            else:
                logger.error(f"Trade execution failed: {command.symbol}")
                
        except Exception as e:
            logger.error(f"Execution error: {e}")
    
    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    async def _notify(self, message: str, priority: str = "NORMAL"):
        """Send notification via Telegram"""
        try:
            if self.notifier and self.notifier.enabled:
                await self.notifier.send_message(message, priority=priority)
        except Exception as e:
            logger.debug(f"Notification failed: {e}")
    
    async def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down QuantAI Engine...")
        
        self.running = False
        self.executor.shutdown()
        
        # Final stats
        stats = self.execution_agent.get_stats()
        orch_stats = self.orchestrator.get_stats()
        
        logger.info("=" * 50)
        logger.info("📊 SESSION SUMMARY")
        logger.info(f"   Cycles: {self.cycle_count}")
        logger.info(f"   Signals Received: {orch_stats['signals_received']}")
        logger.info(f"   Signals Deduplicated: {orch_stats['signals_deduplicated']}")
        logger.info(f"   Trades Executed: {stats['executed_count']}")
        logger.info("=" * 50)
        
        await self._notify(
            f"🛑 *QuantAI Engine Stopped*\n"
            f"Cycles: {self.cycle_count}\n"
            f"Trades: {stats['executed_count']}"
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get current engine status"""
        return {
            "version": self.VERSION,
            "mode": self.trading_mode,
            "running": self.running,
            "cycle_count": self.cycle_count,
            "universe_size": len(self.universe),
            "circuit_breaker": self.circuit_breaker.get_status(),
            "drawdown_state": self.drawdown_sm.get_status(),
            "orchestrator": self.orchestrator.get_stats(),
            "execution_agent": self.execution_agent.get_stats(),
            "memory": self.memory.get_status()
        }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""
    print("=" * 60)
    print("🚀 QuantAI - Institutional Agentic Trading System")
    print(f"   Version: {QuantAIEngine.VERSION}")
    print(f"   Mode: {settings.trading_mode}")
    print("=" * 60)
    
    # Initialize MT5
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return
    
    print(f"✅ MT5 Connected: {mt5.account_info().login}")
    
    # Create and start engine
    engine = QuantAIEngine()
    
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("\n👋 Shutdown requested")
    finally:
        mt5.shutdown()


if __name__ == "__main__":
    main()
