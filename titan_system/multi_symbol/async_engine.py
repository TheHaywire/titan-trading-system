"""
Async Execution Engine
======================
Non-blocking execution engine using asyncio for handling 1,500+ symbols.

Architecture:
- Main event loop handles coordination
- ThreadPoolExecutor for MT5 calls (MT5 is not async-native)
- Semaphore to limit concurrent MT5 operations
- Queue-based order execution for thread safety

Why Asyncio + ThreadPoolExecutor:
- MT5 Python API is synchronous (blocking I/O)
- Wrapping in run_in_executor() allows pseudo-async behavior
- 50 concurrent workers can process 1,500 symbols in ~30 batches
- Semaphore prevents MT5 connection saturation
"""

import asyncio
import MetaTrader5 as mt5
import pandas as pd
import logging
import time
from typing import List, Dict, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
import sys
import os

sys.path.append(os.getcwd())

from titan_system.multi_symbol.universe_scanner import UniverseScanner, ActiveSymbol
from titan_system.multi_symbol.orb_strategy import ORBStrategy
from titan_system.multi_symbol.position_sizer import calculate_position_size
from titan_system.multi_symbol.portfolio_manager import PortfolioManager
from titan_system.strategies.mean_reversion import MeanReversionStrategy

logger = logging.getLogger("Titan.MultiSymbol.AsyncEngine")


@dataclass
class TradeSignal:
    """Represents a validated trade signal ready for execution."""
    symbol: str
    direction: str  # 'BUY' or 'SELL'
    entry_price: float
    stop_loss: float
    take_profit: float
    lot_size: float
    strategy: str
    confidence: float
    metadata: Dict


@dataclass
class ExecutionResult:
    """Result of order execution."""
    success: bool
    ticket: int
    symbol: str
    direction: str
    volume: float
    price: float
    message: str
    timestamp: datetime


class AsyncExecutionEngine:
    """
    Asyncio-based execution engine for high-throughput symbol processing.
    
    Designed to handle 1,500+ symbols efficiently by:
    - Running symbol analysis concurrently
    - Batching MT5 API calls
    - Queue-based order execution
    - Real-time position management
    
    Usage:
        engine = AsyncExecutionEngine()
        await engine.start()
        
        # Or run a single scan cycle
        signals = await engine.run_scan_cycle(active_symbols)
    """
    
    MAGIC_NUMBER = 234001
    
    def __init__(
        self,
        max_concurrent: int = 50,
        risk_percent: float = 2.0,
        max_positions: int = 5,
        scan_interval: int = 60
    ):
        """
        Initialize the async execution engine.
        
        Args:
            max_concurrent: Max concurrent symbol processing tasks
            risk_percent: Default risk per trade as % of balance
            max_positions: Maximum simultaneous positions
            scan_interval: Seconds between scan cycles
        """
        self.max_concurrent = max_concurrent
        self.risk_percent = risk_percent
        self.max_positions = max_positions
        self.scan_interval = scan_interval
        
        # Thread pool for blocking MT5 calls
        self.executor = ThreadPoolExecutor(max_workers=max_concurrent)
        
        # Semaphore to limit concurrent MT5 operations
        self.semaphore = asyncio.Semaphore(max_concurrent)
        
        # Components
        self.scanner = UniverseScanner(max_workers=max_concurrent // 2)
        self.portfolio = PortfolioManager(max_positions=max_positions)
        
        # Strategies
        self.strategies = [
            ORBStrategy({'session': 'auto', 'vwap_confirmation': True}),
            MeanReversionStrategy({'bb_std': 2.0, 'rsi_oversold': 30, 'rsi_overbought': 70})
        ]
        
        # State
        self.running = False
        self.cycle_count = 0
        self.signals_generated = 0
        self.orders_executed = 0
        
    def connect(self) -> bool:
        """Ensure MT5 connection."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        return True
    
    async def fetch_tick(self, symbol: str) -> Optional[Dict]:
        """
        Async-wrapped tick retrieval.
        
        Args:
            symbol: MT5 symbol
            
        Returns:
            Dict with bid, ask, last, volume or None
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            
            def _fetch():
                tick = mt5.symbol_info_tick(symbol)
                if tick is None:
                    return None
                return {
                    'symbol': symbol,
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'last': tick.last,
                    'volume': tick.volume,
                    'time': tick.time
                }
            
            return await loop.run_in_executor(self.executor, _fetch)
    
    async def fetch_ohlcv(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M15,
                          bars: int = 200) -> Optional[pd.DataFrame]:
        """
        Async-wrapped OHLCV data retrieval.
        
        Args:
            symbol: MT5 symbol
            timeframe: MT5 timeframe constant
            bars: Number of bars to fetch
            
        Returns:
            DataFrame or None
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            
            def _fetch():
                rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
                if rates is None:
                    return None
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
            
            return await loop.run_in_executor(self.executor, _fetch)
    
    async def process_symbol(self, symbol: ActiveSymbol) -> List[TradeSignal]:
        """
        Process a single symbol through all strategies.
        
        Args:
            symbol: ActiveSymbol from scanner
            
        Returns:
            List of valid TradeSignals
        """
        signals = []
        
        try:
            # Fetch M15 data
            df = await self.fetch_ohlcv(symbol.symbol)
            if df is None or df.empty:
                return signals
            
            # Run through each strategy
            for strategy in self.strategies:
                try:
                    result = strategy.analyze(symbol.symbol, df)
                    
                    if result and result.get('signal') in ['BUY', 'SELL']:
                        # Calculate position size
                        account = mt5.account_info()
                        balance = account.balance if account else 1000
                        
                        size_result = calculate_position_size(
                            account_balance=balance,
                            entry_price=result.get('entry', symbol.last_price),
                            stop_loss_price=result['stop_loss'],
                            risk_percent=self.risk_percent,
                            symbol=symbol.symbol
                        )
                        
                        if size_result.is_valid:
                            signal = TradeSignal(
                                symbol=symbol.symbol,
                                direction=result['signal'],
                                entry_price=result.get('entry', symbol.last_price),
                                stop_loss=result['stop_loss'],
                                take_profit=result['take_profit'],
                                lot_size=size_result.lot_size,
                                strategy=strategy.name,
                                confidence=result.get('confidence', 0.5),
                                metadata={
                                    'rvol': symbol.rvol,
                                    'atr': symbol.atr,
                                    'spread': symbol.spread,
                                    **result.get('metadata', {})
                                }
                            )
                            signals.append(signal)
                            self.signals_generated += 1
                            
                except Exception as e:
                    logger.debug(f"Strategy {strategy.name} error on {symbol.symbol}: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing {symbol.symbol}: {e}")
        
        return signals
    
    async def run_scan_cycle(self, active_symbols: List[ActiveSymbol]) -> List[TradeSignal]:
        """
        Process all active symbols concurrently.
        
        Args:
            active_symbols: List of ActiveSymbol from scanner
            
        Returns:
            List of valid TradeSignals
        """
        start_time = time.time()
        all_signals = []
        
        logger.info(f"Processing {len(active_symbols)} symbols...")
        
        # Create tasks for all symbols
        tasks = [self.process_symbol(sym) for sym in active_symbols]
        
        # Run concurrently with gather
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Collect signals
        for result in results:
            if isinstance(result, list):
                all_signals.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Task error: {result}")
        
        elapsed = time.time() - start_time
        logger.info(f"Scan complete: {len(all_signals)} signals from "
                   f"{len(active_symbols)} symbols in {elapsed:.1f}s")
        
        return all_signals
    
    async def execute_order(self, signal: TradeSignal) -> ExecutionResult:
        """
        Execute a trade order via MT5.
        
        Args:
            signal: Validated TradeSignal
            
        Returns:
            ExecutionResult with success status
        """
        async with self.semaphore:
            loop = asyncio.get_event_loop()
            
            def _execute():
                if not mt5.initialize():
                    return ExecutionResult(
                        success=False, ticket=0, symbol=signal.symbol,
                        direction=signal.direction, volume=signal.lot_size,
                        price=0, message="MT5 not initialized",
                        timestamp=datetime.now()
                    )
                
                # Get current price
                tick = mt5.symbol_info_tick(signal.symbol)
                if not tick:
                    return ExecutionResult(
                        success=False, ticket=0, symbol=signal.symbol,
                        direction=signal.direction, volume=signal.lot_size,
                        price=0, message="Failed to get tick",
                        timestamp=datetime.now()
                    )
                
                # Prepare order
                order_type = mt5.ORDER_TYPE_BUY if signal.direction == 'BUY' else mt5.ORDER_TYPE_SELL
                price = tick.ask if signal.direction == 'BUY' else tick.bid
                
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": signal.symbol,
                    "volume": float(signal.lot_size),
                    "type": order_type,
                    "price": price,
                    "sl": float(signal.stop_loss),
                    "tp": float(signal.take_profit),
                    "deviation": 20,
                    "magic": self.MAGIC_NUMBER,
                    "comment": f"TITAN_{signal.strategy}",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }
                
                result = mt5.order_send(request)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logger.info(f"ORDER EXECUTED: {signal.symbol} {signal.direction} "
                              f"{signal.lot_size} lots @ {result.price}")
                    return ExecutionResult(
                        success=True, ticket=result.order, symbol=signal.symbol,
                        direction=signal.direction, volume=signal.lot_size,
                        price=result.price, message="OK",
                        timestamp=datetime.now()
                    )
                else:
                    logger.error(f"ORDER FAILED: {signal.symbol} - {result.retcode}: {result.comment}")
                    return ExecutionResult(
                        success=False, ticket=0, symbol=signal.symbol,
                        direction=signal.direction, volume=signal.lot_size,
                        price=0, message=f"{result.retcode}: {result.comment}",
                        timestamp=datetime.now()
                    )
            
            return await loop.run_in_executor(self.executor, _execute)
    
    async def main_loop(self, dry_run: bool = False):
        """
        Main trading loop.
        
        Cycle (every scan_interval seconds):
        1. SCAN: Run universe scanner -> Get Active Symbols
        2. ANALYZE: Run strategies on Active Symbols
        3. FILTER: Apply portfolio constraints (max 5 positions)
        4. SIZE: Position sizing (already done in process_symbol)
        5. EXECUTE: Send orders
        6. LOG: Record all actions
        
        Args:
            dry_run: If True, don't execute actual orders
        """
        logger.info("="*60)
        logger.info("TITAN MULTI-SYMBOL ENGINE STARTING")
        logger.info(f"Max Positions: {self.max_positions} | Risk: {self.risk_percent}%")
        logger.info(f"Scan Interval: {self.scan_interval}s | Dry Run: {dry_run}")
        logger.info("="*60)
        
        self.running = True
        dry_run_count = 0  # Track dry-run "executions"
        
        while self.running:
            try:
                self.cycle_count += 1
                cycle_start = time.time()
                
                logger.info(f"\n--- CYCLE {self.cycle_count} ---")
                
                # 1. SCAN: Get active symbols (run in executor to not block)
                loop = asyncio.get_event_loop()
                active_symbols = await loop.run_in_executor(
                    self.executor, 
                    lambda: self.scanner.scan_universe(min_rvol=2.0)
                )
                
                if not active_symbols:
                    logger.info("No active symbols found. Waiting...")
                    await asyncio.sleep(self.scan_interval)
                    continue
                
                logger.info(f"Found {len(active_symbols)} high-RVOL symbols")
                
                # 2. ANALYZE: Process symbols through strategies
                signals = await self.run_scan_cycle(active_symbols)
                
                if not signals:
                    logger.info("No signals generated.")
                    await asyncio.sleep(self.scan_interval)
                    continue
                
                # Sort by confidence
                signals.sort(key=lambda s: s.confidence, reverse=True)
                
                # Log top signals
                logger.info(f"Generated {len(signals)} signals. Top 5:")
                for sig in signals[:5]:
                    logger.info(f"  {sig.symbol:12} {sig.direction:4} | {sig.strategy:15} | "
                              f"Conf: {sig.confidence:.2f} | Lot: {sig.lot_size} | "
                              f"Entry: {sig.entry_price:.5f} | SL: {sig.stop_loss:.5f}")
                
                # 3. FILTER & 5. EXECUTE
                current_positions = self.portfolio.get_position_count()
                available_slots = self.max_positions - current_positions
                
                if dry_run:
                    # In dry-run, simulate position tracking
                    available_slots = max(0, self.max_positions - dry_run_count)
                
                executed_this_cycle = 0
                
                for signal in signals:
                    # Check if we've hit max positions
                    if executed_this_cycle >= available_slots:
                        logger.info(f"Max positions reached ({self.max_positions}). Stopping execution.")
                        break
                    
                    # Spread filter: Skip if spread too high (>100 points)
                    if signal.metadata.get('spread', 0) > 100:
                        logger.debug(f"Skipping {signal.symbol}: Spread too high ({signal.metadata['spread']})")
                        continue
                    
                    # Check portfolio constraints (skip in dry-run as we track separately)
                    if not dry_run:
                        validation = self.portfolio.validate_new_trade(
                            signal.symbol, signal.direction, signal.lot_size
                        )
                        
                        if not validation['allowed']:
                            logger.debug(f"Skipping {signal.symbol}: {validation['reason']}")
                            continue
                    
                    # Execute
                    if dry_run:
                        logger.info(f"[DRY RUN] Would execute: {signal.symbol} {signal.direction} "
                                   f"{signal.lot_size} lots @ {signal.entry_price:.5f} "
                                   f"(SL: {signal.stop_loss:.5f}, TP: {signal.take_profit:.5f})")
                        dry_run_count += 1
                        executed_this_cycle += 1
                    else:
                        result = await self.execute_order(signal)
                        if result.success:
                            self.orders_executed += 1
                            executed_this_cycle += 1
                
                # 6. LOG
                cycle_time = time.time() - cycle_start
                exec_count = dry_run_count if dry_run else self.orders_executed
                logger.info(f"Cycle {self.cycle_count} complete in {cycle_time:.1f}s | "
                           f"Signals: {len(signals)} | {'Simulated' if dry_run else 'Executed'}: {exec_count}")
                
                # Wait for next cycle
                await asyncio.sleep(self.scan_interval)
                
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                self.running = False
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(10)
    
    async def start(self, dry_run: bool = False):
        """Start the engine."""
        if not self.connect():
            logger.error("Failed to connect to MT5. Exiting.")
            return
        
        await self.main_loop(dry_run=dry_run)
    
    def stop(self):
        """Stop the engine gracefully."""
        self.running = False
        logger.info("Engine stopping...")
    
    def get_status(self) -> Dict:
        """Get current engine status."""
        return {
            'running': self.running,
            'cycle_count': self.cycle_count,
            'signals_generated': self.signals_generated,
            'orders_executed': self.orders_executed,
            'max_positions': self.max_positions,
            'current_positions': self.portfolio.get_position_count(),
            'available_slots': self.portfolio.get_available_slots()
        }


# Entry point for running the engine
async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Titan Multi-Symbol Trading Engine')
    parser.add_argument('--dry-run', action='store_true', help='Run without executing orders')
    parser.add_argument('--max-positions', type=int, default=5, help='Max simultaneous positions')
    parser.add_argument('--risk', type=float, default=2.0, help='Risk per trade (%)')
    parser.add_argument('--interval', type=int, default=60, help='Scan interval (seconds)')
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    engine = AsyncExecutionEngine(
        max_positions=args.max_positions,
        risk_percent=args.risk,
        scan_interval=args.interval
    )
    
    await engine.start(dry_run=args.dry_run)


if __name__ == "__main__":
    asyncio.run(main())
