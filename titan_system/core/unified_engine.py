"""
TITAN UNIFIED ENGINE (V2.0)
============================
Consolidated engine merging TitanEngine and QuantAIEngine.
Single entry point for all institutional trading operations.

Key Features:
- Markov Regime Detection (integrated)
- Auto-Strategy Selection (per regime)
- Multi-Timeframe Analysis
- Event-Driven Architecture
- Risk Management (Circuit Breaker, Kill Switch, VaR)
- Position Management (Break-Even, Trailing)
- Notifications (Email, Telegram)

This replaces both:
- titan_system/core/engine.py (TitanEngine)
- titan_system/quantai_engine.py (QuantAIEngine)
"""

import asyncio
import logging
import time
import datetime
import sys
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd

# Config
from config.settings import settings as Config

# Core Components
from titan_system.db.database import Database
from titan_system.core.circuit_breaker import CircuitBreaker
from titan_system.core.memory import MemorySystem
from titan_system.execution.mt5_executor import MT5Executor
from titan_system.execution.trade_manager import TradeManager

# Analytics
from titan_system.analytics.market_state import MarketAnalyzer
from titan_system.analytics.sessions import SessionManager

# Regime Detection & Auto-Strategy
try:
    from titan_system.analytics.regime_detector import MarkovRegimeSwitcher, MarketRegime
    from titan_system.analytics.auto_strategy import AutoStrategySelector, auto_select
    REGIME_AVAILABLE = True
except ImportError:
    REGIME_AVAILABLE = False

# Risk & Allocation
from titan_system.risk.allocation import AllocationAgent
from titan_system.risk.kill_switch import KillSwitch

# Notifications  
from titan_system.notifications.email import EmailNotifier
from titan_system.notifications.telegram_bot import TelegramNotifier

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("titan_unified.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Titan.Unified")


class TradingMode(Enum):
    LIVE = "LIVE"
    PAPER = "PAPER"
    BACKTEST = "BACKTEST"


@dataclass
class EngineStatus:
    """Current engine state"""
    running: bool = False
    mode: str = "LIVE"
    equity: float = 0.0
    positions_open: int = 0
    signals_today: int = 0
    trades_today: int = 0
    pnl_today: float = 0.0
    current_regime: str = "UNKNOWN"
    last_tick: str = ""


class TitanUnifiedEngine:
    """
    The Unified Titan Trading Engine (V2.0)
    
    Consolidates TitanEngine and QuantAIEngine into a single system.
    Provides regime-aware, institutional-grade trading.
    """
    
    VERSION = "2.0.0"
    
    def __init__(self, 
                 universe: List[str] = None,
                 trading_mode: TradingMode = TradingMode.LIVE,
                 risk_percent: float = 0.05):
        """
        Initialize the Unified Engine.
        
        Args:
            universe: List of symbols to trade
            trading_mode: LIVE, PAPER, or BACKTEST
            risk_percent: Default risk per trade (0.05 = 5%)
        """
        logger.info("=" * 60)
        logger.info(f"TITAN UNIFIED ENGINE V{self.VERSION}")
        logger.info("=" * 60)
        
        self.mode = trading_mode
        self.risk_percent = risk_percent
        self.running = False
        
        # 1. Database & Memory
        self.db = Database(Config.db_path)
        self.memory = MemorySystem()
        
        # 2. Trading Universe
        self.universe = universe or [
            "GOLD", "XAUUSD", "BTCUSD", "ETHUSD",
            "US100", "US30", "GER40",
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD"
        ]
        logger.info(f"Universe: {len(self.universe)} symbols")
        
        # 3. Risk Management
        self.circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=Config.max_daily_loss_percent,
            auto_reset_daily=True
        )
        self.kill_switch = KillSwitch(email_notifier=None, telegram_notifier=None)
        self.allocation = AllocationAgent(max_symbols=10, max_correlation=0.7)
        
        # 4. Notifications
        self.email = EmailNotifier()
        self.telegram = TelegramNotifier()
        self.kill_switch.email = self.email
        self.kill_switch.telegram = self.telegram
        
        # 5. Execution
        self.executor = MT5Executor()
        self.trade_manager = TradeManager(managed_magics=[900001])
        
        # 6. Analytics
        self.brain = MarketAnalyzer(self.executor)
        
        # 7. Regime Detection (NEW)
        if REGIME_AVAILABLE:
            self.regime_detector = MarkovRegimeSwitcher()
            self.strategy_selector = AutoStrategySelector()
            self.regime_fitted = {}
            self.current_regimes = {}
            logger.info("[REGIME] Markov Regime Detection: ACTIVE")
        else:
            self.regime_detector = None
            self.strategy_selector = None
            logger.warning("[REGIME] Regime detection not available")
        
        # 8. State Tracking
        self.status = EngineStatus()
        self.signals_today = 0
        self.trades_today = 0
        self.last_daily_report = None
        
        # 9. Timing
        self.tick_interval = 30  # seconds between ticks
        self.regime_update_interval = 60  # cycles between regime updates
        self.regime_cycle_count = 0
        
        logger.info("Engine initialized successfully")
    
    def initialize_mt5(self) -> bool:
        """Initialize MT5 connection"""
        if not mt5.initialize():
            logger.critical("MT5 initialization failed")
            return False
        
        account = mt5.account_info()
        if not account:
            logger.critical("Failed to get account info")
            return False
        
        self.status.equity = account.equity
        logger.info(f"Connected to Account: {account.login}")
        logger.info(f"Equity: ${account.equity:,.2f}")
        logger.info(f"Balance: ${account.balance:,.2f}")
        
        return True
    
    async def start(self):
        """Start the main engine loop"""
        logger.info("Starting Titan Unified Engine...")
        
        if not self.initialize_mt5():
            return
        
        self.running = True
        self.status.running = True
        self.status.mode = self.mode.value
        
        logger.info(f"Mode: {self.mode.value}")
        logger.info(f"Risk per trade: {self.risk_percent * 100}%")
        logger.info("Entering main loop...")
        
        try:
            while self.running:
                await self._tick()
                await asyncio.sleep(self.tick_interval)
                
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Engine error: {e}")
        finally:
            self._shutdown()
    
    async def _tick(self):
        """One cycle of the engine"""
        self.status.last_tick = datetime.datetime.now().strftime("%H:%M:%S")
        
        try:
            # 1. Check circuit breaker
            if self.circuit_breaker.is_tripped():
                logger.warning("[CIRCUIT BREAKER] Tripped - skipping cycle")
                return
            
            # 2. Update regime detection periodically
            self.regime_cycle_count += 1
            if self.regime_cycle_count >= self.regime_update_interval:
                await self._update_regimes()
                self.regime_cycle_count = 0
            
            # 3. Manage existing positions
            self.trade_manager.monitor_active_trades()
            
            # 4. Scan for new signals
            signals = await self._scan_universe()
            
            # 5. Execute approved signals
            for signal in signals:
                await self._execute_signal(signal)
            
            # 6. Update status
            self._update_status()
            
        except Exception as e:
            logger.error(f"Tick error: {e}")
    
    async def _update_regimes(self):
        """Update regime detection for key symbols"""
        if not REGIME_AVAILABLE or not self.regime_detector:
            return
        
        key_symbols = ["GOLD", "XAUUSD", "BTCUSD", "EURUSD"]
        
        for symbol in key_symbols:
            try:
                if not mt5.symbol_select(symbol, True):
                    continue
                
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
                if rates is None or len(rates) < 100:
                    continue
                
                df = pd.DataFrame(rates)
                
                # Fit on first call
                if symbol not in self.regime_fitted:
                    self.regime_detector.fit(df)
                    self.regime_fitted[symbol] = True
                
                # Detect regime
                regime_state = self.regime_detector.detect(df)
                old_regime = self.current_regimes.get(symbol)
                self.current_regimes[symbol] = regime_state
                
                # Log regime changes
                if old_regime and old_regime.current_regime != regime_state.current_regime:
                    logger.info(f"[REGIME SHIFT] {symbol}: {old_regime.current_regime.value} -> {regime_state.current_regime.value}")
                
            except Exception as e:
                logger.debug(f"Regime update failed for {symbol}: {e}")
        
        # Update status with dominant regime
        if self.current_regimes:
            dominant = max(self.current_regimes.values(), key=lambda x: x.confidence if x else 0)
            if dominant:
                self.status.current_regime = dominant.current_regime.value
    
    async def _scan_universe(self) -> List[Dict]:
        """Scan all symbols for signals"""
        signals = []
        
        for symbol in self.universe:
            try:
                analysis = await self.brain.analyze_symbol(symbol)
                if not analysis:
                    continue
                
                score = analysis.get('score', 0)
                bias = analysis.get('bias', 'NEUTRAL')
                regime_info = analysis.get('regime', {})
                
                # Score threshold
                if score < 70:
                    continue
                
                # Get strategy recommendation
                if REGIME_AVAILABLE and self.strategy_selector:
                    strategy_rec = auto_select(analysis)
                    if not strategy_rec.get('selected_strategy'):
                        continue
                    risk_mult = strategy_rec.get('risk_multiplier', 1.0)
                else:
                    strategy_rec = {}
                    risk_mult = 1.0
                
                signals.append({
                    'symbol': symbol,
                    'direction': 'BUY' if bias == 'BULLISH' else 'SELL',
                    'score': score,
                    'analysis': analysis,
                    'strategy': strategy_rec.get('selected_strategy', 'Default'),
                    'risk_multiplier': risk_mult,
                    'regime': regime_info.get('current', 'UNKNOWN')
                })
                
                self.signals_today += 1
                
            except Exception as e:
                logger.debug(f"Scan failed for {symbol}: {e}")
        
        return signals
    
    async def _execute_signal(self, signal: Dict):
        """Execute a validated signal"""
        symbol = signal['symbol']
        direction = signal['direction']
        score = signal['score']
        risk_mult = signal.get('risk_multiplier', 1.0)
        
        logger.info("")
        logger.info("=" * 40)
        logger.info(f"[SIGNAL] {symbol} {direction} (Score: {score})")
        logger.info(f"Strategy: {signal.get('strategy')} | Regime: {signal.get('regime')}")
        
        # Calculate position size
        account = mt5.account_info()
        base_risk = account.equity * self.risk_percent
        risk_amount = base_risk * risk_mult
        
        if risk_mult != 1.0:
            logger.info(f"[REGIME] Risk adjusted: {risk_mult:.1f}x (${base_risk:.0f} -> ${risk_amount:.0f})")
        
        # Execute via executor
        success = self.executor.execute_trade(
            symbol=symbol,
            direction=direction,
            risk_usd=risk_amount,
            reason=f"Score {score} | {signal.get('strategy')}"
        )
        
        if success:
            self.trades_today += 1
            self.status.trades_today = self.trades_today
            logger.info(f"[EXECUTED] {symbol} {direction}")
            
            # Notify
            self.telegram.send_message(f"🎯 Trade: {direction} {symbol} (Score: {score})")
        else:
            logger.warning(f"[REJECTED] {symbol} execution failed")
    
    def _update_status(self):
        """Update engine status"""
        try:
            account = mt5.account_info()
            if account:
                self.status.equity = account.equity
            
            positions = mt5.positions_get()
            self.status.positions_open = len(positions) if positions else 0
            self.status.signals_today = self.signals_today
            
        except Exception:
            pass
    
    def _shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down Titan Unified Engine...")
        self.running = False
        self.status.running = False
        
        try:
            mt5.shutdown()
        except Exception:
            pass
        
        logger.info("Engine stopped")
    
    def get_status(self) -> Dict:
        """Get current engine status"""
        return {
            'version': self.VERSION,
            'running': self.status.running,
            'mode': self.status.mode,
            'equity': self.status.equity,
            'positions_open': self.status.positions_open,
            'signals_today': self.status.signals_today,
            'trades_today': self.status.trades_today,
            'current_regime': self.status.current_regime,
            'last_tick': self.status.last_tick,
            'regime_detection': REGIME_AVAILABLE
        }


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("TITAN UNIFIED ENGINE - INSTITUTIONAL TRADING SYSTEM")
    print("=" * 60 + "\n")
    
    engine = TitanUnifiedEngine(
        trading_mode=TradingMode.LIVE,
        risk_percent=0.05
    )
    
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        print("\nShutdown complete.")


if __name__ == "__main__":
    main()
