"""
Proven Strategy Trading Bot
============================
Simple, focused trading bot using backtested strategies.

Based on research findings:
- EMA Cross: 63.3% win, 0.79R on USDJPY
- EMA Pullback: 0.18R avg across symbols

Runs every 15 minutes, executes on H1 signals.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import logging
from datetime import datetime, timezone
import MetaTrader5 as mt5
import pandas as pd

from config.settings import settings
from titan_system.strategies.proven_strategy import ProvenStrategy
from titan_system.core.circuit_breaker import CircuitBreaker, DrawdownStateMachine
from titan_system.execution.mt5_executor import MT5Executor
from titan_system.execution.trade_manager import TradeManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("proven_bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ProvenBot")


class ProvenTradingBot:
    """
    Simple trading bot using proven backtested strategies.
    """
    
    UNIVERSE = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "GOLD", "BTCUSD", "US500"
    ]
    
    SCAN_INTERVAL_MINUTES = 5  # More frequent scanning
    
    def __init__(self):
        self.strategy = ProvenStrategy()
        self.circuit_breaker = CircuitBreaker(max_daily_loss_percent=5.0)
        self.drawdown_sm = DrawdownStateMachine()
        self.executor = MT5Executor()
        self.trade_manager = TradeManager()
        
        self.running = False
        self.last_signal_time = {}  # symbol -> last signal time
        self.signal_cooldown_minutes = 30  # Reduced from 60
        self._max_trades_per_scan = 3  # Allow multiple trades
        self._start_equity = 0
        self._signals_today = 0
        self._trades_today = 0
        
    def start(self):
        """Start the trading bot"""
        logger.info("=" * 60)
        logger.info("PROVEN STRATEGY TRADING BOT")
        logger.info("=" * 60)
        
        if not mt5.initialize():
            logger.error(f"MT5 failed: {mt5.last_error()}")
            return
        
        if not self.executor.connect():
            logger.error("Failed to connect executor")
            return
        
        account = mt5.account_info()
        self._start_equity = account.equity
        
        logger.info(f"Account: {account.login}")
        logger.info(f"Balance: ${account.balance:,.2f}")
        logger.info(f"Equity: ${account.equity:,.2f}")
        logger.info(f"Universe: {len(self.UNIVERSE)} symbols")
        logger.info("=" * 60)
        
        self.running = True
        self._main_loop()
    
    def _main_loop(self):
        """Main trading loop"""
        last_scan = None
        
        while self.running:
            try:
                now = datetime.now(timezone.utc)
                
                # Manage existing trades first
                self.trade_manager.monitor_active_trades()
                
                # Check if time for scan
                should_scan = False
                if last_scan is None:
                    should_scan = True
                elif (now - last_scan).total_seconds() >= self.SCAN_INTERVAL_MINUTES * 60:
                    should_scan = True
                
                # Also scan on top of each hour (H1 close)
                if now.minute == 0 and (last_scan is None or last_scan.hour != now.hour):
                    should_scan = True
                
                if should_scan:
                    self._scan_and_trade()
                    last_scan = now
                
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)
        
        self._shutdown()
    
    def _scan_and_trade(self):
        """Scan for signals and execute trades"""
        logger.info("-" * 40)
        logger.info(f"Scanning at {datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}")
        
        # Reset trades per scan counter
        self._max_trades_per_scan = 3
        
        # 1. Check circuit breaker
        account = mt5.account_info()
        safe, msg = self.circuit_breaker.check_safe_to_trade({
            'equity': account.equity,
            'balance': account.balance
        })
        
        if not safe:
            logger.warning(f"Trading blocked: {msg}")
            return
        
        # 2. Update drawdown state
        state, transition = self.drawdown_sm.update(account.equity, self._start_equity)
        if transition:
            logger.warning(f"Drawdown state: {transition}")
        
        dd_actions = self.drawdown_sm.get_actions()
        if not dd_actions['allow_new_trades']:
            logger.warning("Drawdown too high - no new trades")
            return
        
        # 3. Scan for signals
        signals = self.strategy.analyze_multi_symbol(
            self.UNIVERSE,
            lambda sym: self._get_data(sym)
        )
        
        if not signals:
            logger.info("No signals found")
            return
        
        logger.info(f"Found {len(signals)} signal(s)")
        
        # 4. Filter and execute
        for signal in signals:
            # Check cooldown
            if not self._check_cooldown(signal.symbol):
                logger.info(f"Skipping {signal.symbol} - cooldown active")
                continue
            
            # Check score threshold
            min_score = dd_actions['min_score']
            if signal.score < min_score:
                logger.info(f"Skipping {signal.symbol} - score {signal.score} < {min_score}")
                continue
            
            # Execute trade
            self._execute_signal(signal, dd_actions['lot_multiplier'])
            
            # Allow multiple trades per scan
            self._max_trades_per_scan -= 1
            if self._max_trades_per_scan <= 0:
                break
    
    def _get_data(self, symbol: str) -> pd.DataFrame:
        """Get H1 data for symbol"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
        if rates is not None:
            return pd.DataFrame(rates)
        return None
    
    def _check_cooldown(self, symbol: str) -> bool:
        """Check if enough time has passed since last signal"""
        if symbol not in self.last_signal_time:
            return True
        
        elapsed = (datetime.now(timezone.utc) - self.last_signal_time[symbol]).total_seconds()
        return elapsed >= self.signal_cooldown_minutes * 60
    
    def _execute_signal(self, signal, lot_multiplier: float):
        """Execute a trade based on signal"""
        logger.info(f"\n{'='*50}")
        logger.info(f"EXECUTING: {signal.symbol} {signal.direction}")
        logger.info(f"Strategy: {signal.strategy}")
        logger.info(f"Score: {signal.score}")
        logger.info(f"Entry: {signal.entry:.5f}")
        logger.info(f"SL: {signal.stop_loss:.5f}")
        logger.info(f"TP: {signal.take_profit:.5f}")
        for r in signal.reasoning:
            logger.info(f"  - {r}")
        logger.info("="*50)
        
        # Calculate lot size
        base_lot = 0.01
        lot = round(base_lot * lot_multiplier, 2)
        lot = max(0.01, lot)
        
        # Calculate SL/TP in points
        tick_info = mt5.symbol_info(signal.symbol)
        if tick_info is None:
            logger.error(f"Cannot get symbol info for {signal.symbol}")
            return
        
        point = tick_info.point
        sl_points = abs(signal.entry - signal.stop_loss) / point
        tp_points = abs(signal.take_profit - signal.entry) / point
        
        # Execute
        result = self.executor.execute_order(
            symbol=signal.symbol,
            order_type=signal.direction,
            lot=lot,
            sl_points=int(sl_points),
            tp_points=int(tp_points),
            comment=f"Proven: {signal.strategy}"
        )
        
        if result:
            logger.info(f"Trade executed successfully!")
            self.last_signal_time[signal.symbol] = datetime.now(timezone.utc)
            self._trades_today += 1
            self._signals_today += 1
        else:
            logger.error("Trade execution failed")
    
    def _shutdown(self):
        """Graceful shutdown"""
        logger.info("\n" + "=" * 60)
        logger.info("SHUTDOWN SUMMARY")
        logger.info(f"Signals generated: {self._signals_today}")
        logger.info(f"Trades executed: {self._trades_today}")
        logger.info("=" * 60)
        
        self.running = False
        self.executor.shutdown()
        mt5.shutdown()


def main():
    bot = ProvenTradingBot()
    bot.start()


if __name__ == "__main__":
    main()
