import asyncio
import logging
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime

# Core Components
from titan_system.core.execution import MT5Execution
from titan_system.core.trade_manager import TradeManager
from titan_system.core.circuit_breaker import CircuitBreaker 
from titan_system.strategies.book_strategies import BookTechnicalStrategy

# Database
from titan_system.data.database import SessionLocal, engine as db_engine
from titan_system.data.models import Base, StrategyAssignment, Ticker

# Configuration
from titan_system.titan_futures_config import TitanFuturesConfig

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("titan_production.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Titan.ProductionEngine")

class InstitutionalEngine:
    """
    The Single Source of Truth for Live Trading.
    Orchestrates: Data -> Strategy -> Risk -> Execution -> Management.
    """
    def __init__(self):
        self.config = TitanFuturesConfig()
        self.execution = MT5Execution(self.config)
        
        # Risk & Management
        # Note: CircuitBreaker might assume different args, simplified here
        self.circuit_breaker = CircuitBreaker(max_daily_loss_pct=5.0) 
        self.trade_manager = TradeManager(self.execution)
        
        self.running = False
        self.strategies = {}
        self.active_assignments = {}
        
        # Initialize DB
        Base.metadata.create_all(bind=db_engine)
        self.db = SessionLocal()

    def _initialize_system(self):
        """Connects to MT5, loads strategies, updates DB."""
        if not self.execution.connect():
            logger.critical("Failed to connect to MT5. Aborting.")
            return False
            
        # 1. Load Validated Strategies
        self.strategies["FAT_TAILS"] = BookTechnicalStrategy(
            use_trend_filter=True,
            trailing_stop_mode='SMA50'
        )
        logger.info("Loaded Strategies: FAT_TAILS (BookTechnical)")
        
        # 2. Sync Assignments (Hardcoded "Fat Tail" list for Phase 5)
        # In Phase 6, we will make this purely DB-driven.
        fat_tail_symbols = [
            "COCOA", "XAUUSD", "US500", "PALLADIUM", # MT5 Specific names might vary
            "#Cocoa", "Gold", "US500Cash" # Add likely variants
        ]
        
        self._sync_strategy_assignments(fat_tail_symbols, "FAT_TAILS")
        return True

    def _sync_strategy_assignments(self, whitelist, strategy_name):
        """Ensures the DB and local cache have the correct strategy map."""
        for symbol in whitelist:
            # Check availability in MT5 first
            if not mt5.symbol_info(symbol):
                continue
                
            # Update local cache
            self.active_assignments[symbol] = strategy_name
            
            # Update DB (Upsert)
            existing = self.db.query(StrategyAssignment).filter_by(symbol=symbol).first()
            if not existing:
                new_assignment = StrategyAssignment(symbol=symbol, strategy_name=strategy_name)
                self.db.add(new_assignment)
            else:
                existing.strategy_name = strategy_name
        
        self.db.commit()
        logger.info(f"Active Strategy Assignments: {len(self.active_assignments)} symbols")

    async def run_forever(self):
        """Main Institutional Loop"""
        if not self._initialize_system():
            return
            
        self.running = True
        logger.info("🚀 TITAN INSTITUTIONAL ENGINE STARTED")
        
        try:
            while self.running:
                loop_start = datetime.now()
                
                # 1. Manage Existing Positions (Trailing Stops)
                self.trade_manager.manage_positions(self.active_assignments)
                
                # 2. Scan Markets for New Entries
                await self._scan_markets()
                
                # 3. Heartbeat & Sleep
                elapsed = (datetime.now() - loop_start).total_seconds()
                sleep_time = max(1.0, 60 - elapsed) # Run every minute roughly
                await asyncio.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("Manual Stop Requested.")
        except Exception as e:
            logger.critical(f"Engine Crash: {e}", exc_info=True)
        finally:
            self.execution.shutdown()
            self.db.close()

    async def _scan_markets(self):
        """Iterate through assigned symbols and check for signals."""
        for symbol, strategy_name in self.active_assignments.items():
            strategy = self.strategies.get(strategy_name)
            if not strategy: continue
            
            # Data Fetching (Efficient H1)
            # Need 200 bars for SMA 200
            df = self.execution.get_data(symbol, mt5.TIMEFRAME_H1, 250)
            if df is None: continue
            
            # Analysis
            signals = strategy.analyze(df)
            
            if signals:
                # Process the most recent signal only
                latest_signal = signals[-1]
                
                # Verify freshness (is signal from the just-closed candle?)
                # df.iloc[-1] is the current forming candle usually in get_data? 
                # Strategy logic looks at [-1] as current.
                # If we want closed candle signals, we usually look at timestamp.
                # Assuming strategy handles this (it returns time).
                
                self._process_signal(symbol, latest_signal)

    async def _process_signal(self, symbol, signal):
        """Risk Check -> Execution."""
        # 1. Circuit Breaker Check
        safe, reason = self.circuit_breaker.check_safe_to_trade(self.execution.get_account_info())
        if not safe:
             logger.warning(f"Trade Rejected by Risk Engine: {reason}")
             return

        # 2. Check Existing Position (Don't double dip)
        positions = self.execution.get_positions()
        for pos in positions:
            if pos['symbol'] == symbol:
                return # Already in a trade
        
        # 3. Get Symbol Info for Sizing
        # We need this for the Sizer
        import MetaTrader5 as mt5
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            logger.error(f"Could not get symbol info for {symbol}")
            return

        # 4. Standard Risk Params
        sl_pips = 100 # Initial Safety Net (Strategy should ideally provide this)
        tp_pips = 0   # 0 = Infinite/Trailing (Home Run Mode)
        
        # Determine Entry & SL Prices for Sizing
        tick = mt5.symbol_info_tick(symbol)
        direction = signal['signal']
        
        if direction == "BUY":
            entry_price = tick.ask
            # Convert pips to price distance
            sl_price = entry_price - (sl_pips * symbol_info.point * 10) # 1 pip = 10 points
        else:
            entry_price = tick.bid
            sl_price = entry_price + (sl_pips * symbol_info.point * 10)
            
        # 5. Calculate Institutional Size
        from titan_system.risk.position_sizer import InstitutionalPositionSizer
        sizer = InstitutionalPositionSizer(max_risk_pct=self.config.MAX_POSITION_RISK_PCT)
        
        equity = self.execution.get_account_info().get('equity', 0)
        volume = sizer.calculate_lots(equity, symbol_info, sl_price, entry_price)
        
        if volume == 0.0:
            logger.warning(f"Sizing returned 0 lots for {symbol}. Trade Aborted.")
            return

        # 6. Execute
        logger.info(f"⚡ SIGNAL: {symbol} {direction} | {signal['comment']} | Size: {volume}")
        
        result = self.execution.execute_order(
            symbol=symbol,
            order_type=direction,
            volume=volume,
            sl_pips=sl_pips,
            tp_pips=tp_pips,
            comment=f"{signal['strategy']} (Titan v3)"
        )
        
        if result:
            logger.info(f"✅ EXECUTED: {symbol} {direction} @ {result['open_price']}")

if __name__ == "__main__":
    # Windows Asyncio Policy Fix
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    engine = InstitutionalEngine()
    asyncio.run(engine.run_forever())
