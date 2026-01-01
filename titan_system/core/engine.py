
import asyncio
import logging
import time
import datetime
import sys
import os
# Ensure root is in path
sys.path.append(os.getcwd())

from config.settings import settings as Config
from titan_system.core.execution import MT5Execution
from titan_system.db.database import Database
from titan_system.core.circuit_breaker import CircuitBreaker

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger("Titan.Engine")

from titan_system.strategies.regression_surfer import RegressionSurfer
from titan_system.strategies.trend_surfer import TrendSurfer
from titan_system.strategies.scalper import MomentumScalper
from titan_system.strategies.institutional_gold import InstitutionalGoldStrategy # NEW
from titan_system.strategies.liquidity_hunter import LiquidityHunterStrategy # NEW STRATEGY
from titan_system.strategies.mean_reversion import MeanReversionStrategy # NEW STRATEGY (Quant Standard)
from titan_system.strategies.book_strategies import BookTechnicalStrategy # FAT TAIL VALIDATED
from titan_system.risk.position_sizer import KellyPositionSizer

from titan_system.notifications.email import EmailNotifier
from titan_system.notifications.telegram_bot import TelegramNotifier
from titan_system.analytics.market_state import MarketAnalyzer
from titan_system.analytics.sessions import SessionManager
import MetaTrader5 as mt5

# ... (Previous imports)

class TitanEngine:
    def __init__(self):
        logger.info("Initializing Titan Engine - Active Trading Mode")
        
        # 1. Initialize Memory (DB)
        self.db = Database(Config.db_path)
        
        # Initialize Notifiers
        self.notifier = EmailNotifier()
        self.telegram = TelegramNotifier()
        
        # 2. Risk Management (Circuit Breaker)
        self.circuit_breaker = CircuitBreaker(
            max_daily_loss_percent=Config.max_daily_loss_percent,
            auto_reset_daily=True
        )
        
        # 3. Initialize Execution Interface
        self.execution = MT5Execution(Config)
        
        # 4. Initialize The Brain (Market Analyzer)
        self.brain = MarketAnalyzer(self.execution)

        # 5. Load Universe DO NOT USE CONFIG
        # self.trading_symbols = Config.trading_symbols 
        # Dynamic Load:
        self.trading_symbols = self.db.get_active_universe(limit=50)
        
        # Override with Fat Tail Whitelist if available
        # This ensures we trade the validated symbols
        # TODO: Move this to a "Whitelist Manager" in a future refactor
        fat_tail_whitelist = [
            "COCOA", "PALL-MAR26", "PLAT-APR26", "GOLD", "XAUUSD", "US500", "US500Cash", 
            "GerMid50Cash", "Rheinmetall", "Givaudan", "EliLilly", "Spotify"
        ]
        # Merge DB symbols with our Hardcoded Winners (to ensure they are scanned)
        # Note: In production, we should just ensure these are IN the DB.
        # verifying if symbol names match exactly might be tricky, assuming standard names.
        
        # Create a set for uniqueness
        universe_set = set(self.trading_symbols) if self.trading_symbols else set()
        
        # Add winners only if they exist in valid symbols list (checked later by brain)
        # simplified: just add them. Brain will reject if invalid.
        for ft in fat_tail_whitelist:
            universe_set.add(ft)
            
        self.trading_symbols = list(universe_set)

        if not self.trading_symbols:
            logger.warning("⚠️ No Active Universe found! Falling back to Config.")
            self.trading_symbols = Config.trading_symbols

        logger.info(f"🌌 Active Universe: {len(self.trading_symbols)} symbols (inc. Fat Tails)")
        
        # 6. Initialize Cloud Logger (Google Sheets)
        try:
             from titan_system.integrations.google_sheets import TitanSheets
             self.cloud_logger = TitanSheets()
        except Exception as e:
             logger.warning(f"Could not load Google Sheets Integration: {e}")
             self.cloud_logger = None

        # 6. Load Strategies
        self.strategies = [
            # The Crown Jewel for GOLD
            InstitutionalGoldStrategy(config={
                "execution_client": self.execution
            }),
            # The Fat Tail Hunter (Book Strategy)
            BookTechnicalStrategy(
                use_trend_filter=True, # Validated Optimization
                require_confluence=False
            ),
            LiquidityHunterStrategy(config={}),
            MeanReversionStrategy(config={}),
            # Generic Strategies for everything else
            TrendSurfer(config={
                "fast_period": 50, 
                "slow_period": 200,
                "adx_threshold": Config.adx_threshold
            }),
            MomentumScalper(config={
                "rsi_period": 14,
                "adx_threshold": 20
            }),
            RegressionSurfer()
        ]
        
        self.running = False
        self.position_sizer = KellyPositionSizer(max_risk_pct=2.0, kelly_fraction=0.5)
        self.last_analysis_time = 0
        self.last_report_date = None
        self.scan_results = {} # For API/Dashboard

    def get_status(self):
        """Returns the current system status for the API"""
        summary = self.execution.get_account_summary() or {}
        session_status = SessionManager.get_market_status()
        
        # Determine aggregate regime from one of the symbols (e.g. EURUSD) or global
        # For now, simplistic approach
        regime = {"status": "UNKNOWN", "adx": 0}
        
        return {
            "running": self.running,
            "connected": self.execution.connected,
            "equity": summary.get('equity', 0),
            "balance": summary.get('balance', 0),
            "open_positions": len(self.execution.get_positions()),
            "market_scan": self.scan_results,
            "session": session_status,
            "regime": regime
        }

    async def start(self):
        """Main Async Event Loop"""
        logger.info("🚀 Starting Engine...")
        
        if not self.execution.connect():
            logger.error("❌ Initial connection failed. Entering retry loop...")
            # Don't return, let the loop handle retries

        self.running = True
        
        try:
            while self.running:
                # Connection Check
                if not self.execution.connected:
                    logger.warning("⚠️ MT5 Disconnected. Attempting Reconnect...")
                    if self.execution.connect():
                        logger.info("✅ Reconnected to MT5")
                    else:
                        await asyncio.sleep(5)
                        continue

                start_time = time.time()
                
                await self.tick()
                
                elapsed = time.time() - start_time
                sleep_time = max(0.1, 1.0 - elapsed)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Engine Shutdown Requested")
        finally:
            self.execution.shutdown()
            logger.info("💀 Engine Stopped.")

    def get_status(self):
        """Returns the current system status for the API"""
        summary = self.execution.get_account_summary() or {}
        session_status = SessionManager.get_market_status()
        
        # Determine aggregate regime from one of the symbols (e.g. EURUSD) or global
        # For now, simplistic approach
        regime = {"status": "UNKNOWN", "adx": 0}
        
    def get_status(self):
        """Returns the current system status for the API"""
        summary = self.execution.get_account_summary() or {}
        session_status = SessionManager.get_market_status()
        
        # Determine aggregate regime from one of the symbols (e.g. EURUSD) or global
        # For now, simplistic approach
        regime = {"status": "UNKNOWN", "adx": 0}
        
        return {
            "running": self.running,
            "connected": self.execution.connected,
            "equity": summary.get('equity', 0),
            "balance": summary.get('balance', 0),
            "open_positions": len(self.execution.get_positions()),
            "market_scan": self.scan_results,
            "session": session_status,
            "regime": regime
        }
    
    async def tick(self):
        """One cycle of the engine (every 1 second)"""
        
        # Broadcast State for Dashboard
        self._broadcast_status()
        
        # Heartbeat every 10s
        if int(time.time()) % 10 == 0:
            summary = self.execution.get_account_summary()
            if summary:
                logger.info(f"💓 Heartbeat | Equity: {summary['equity']} | Positions: {len(self.execution.get_positions())}")
        
        # Check for Daily Report (at 23:59)
        current_time = datetime.datetime.now()
        if current_time.hour == 23 and current_time.minute >= 55 and self.last_report_date != current_time.date():
            await self.generate_daily_report()
        
        # Run Analysis every 15 minutes (or 60s for testing)
        # For demo purposes, we run scanning every minute
        if time.time() - self.last_analysis_time > 60:
            self.last_analysis_time = time.time()
            await self.run_analysis_cycle()

    def _broadcast_status(self):
        """Writes current system state to a JSON file for the separate Dashboard process."""
        try:
            summary = self.execution.get_account_summary() or {}
            
            state = {
                "timestamp": time.time(),
                "equity": summary.get('equity', 0),
                "balance": summary.get('balance', 0),
                "open_positions": len(self.execution.get_positions()),
                "profit_today": 0.0, # TODO: Calc from DB
                "active_universe": len(self.trading_symbols),
                "running": self.running
            }
            
            # Update Cloud Logger & Sync Settings
            if self.cloud_logger and int(time.time()) % 60 == 0: # Every minute
                 self.cloud_logger.update_dashboard(state)
                 self.sync_cloud_settings()
            
            # Local Dashboard Update
            with open("titan_system/dashboard/state.json", "w") as f:
                json.dump(state, f)

        except Exception as e:
            # logger.error(f"Status broadcast failed: {e}") # Reduce spam
            pass

    def sync_cloud_settings(self):
        """Pulls settings from the Cloud Cockpit and applies them."""
        if not self.cloud_logger: return
        
        try:
            settings = self.cloud_logger.read_cockpit_settings()
            if not settings: return
            
            # Apply Settings
            if "TRADING_ENABLED" in settings:
                should_run = settings["TRADING_ENABLED"]
                if not should_run and self.running:
                    logger.info("🛑 Cockpit requested STOP. Pausing engine.")
                    self.running = False
                elif should_run and not self.running and not self.circuit_breaker.is_triggered():
                    logger.info("🟢 Cockpit requested START. Resuming engine.")
                    self.running = True
            
            logger.info(f"☁️ Synced Cockpit: {settings}")
            
        except Exception as e:
            logger.error(f"Cloud Sync Failed: {e}")

    async def run_analysis_cycle(self):
        logger.info("🔎 Starting Market Analysis Cycle...")
        
        current_scan = {"Detailed Analysis": []}
        
        
        current_scan = {"Detailed Analysis": []}
        
        for symbol in self.trading_symbols:
            # 1. Get Data & Analyze with The Brain
            market_state = await self.brain.analyze_symbol(symbol)
            
            if not market_state:
                logger.warning(f"Could not fetch data for {symbol}")
                continue

            # 2. Analyze with ALL Strategies (Passing Market State if adaptable, or raw DF for now)
            # Short-term: Fetch H1 DF again for legacy strategies until they are upgraded
            # But we can optimize this later. For now, we trust the Brain first.
            
            # Log the glass box reasoning
            logger.info(f"🧠 {symbol} Score: {market_state['score']} ({market_state['bias']})")
            
            if self.cloud_logger:
                bias_msg = f"Score: {market_state['score']} ({market_state['bias']}). " + " ".join(market_state['reasoning'][:1])
                self.cloud_logger.log_reasoning(symbol, "MARKET_SCAN", bias_msg)
                
            for reason in market_state['reasoning']:
                 logger.info(f"   > {reason}")

            best_result = None
            
            # For now, we still run legacy strategies on H1 data for execution safety
            # But we FILTER them using the Brain's Bias
            
            df = self.execution.get_data(symbol, mt5.TIMEFRAME_H1, 300)
            if df is None: continue

            # NEW: Strategy Routing
            # Query DB for assigned strategy? 
            # Optimization: Load mapping once at start of cycle or cache it.
            # For now, we iterate all loaded strategies but check names?
            # Or simplier: Just run all, but weigh/filter by what DB says?
            # "Professional" implies strict adherence. 
            
            # Let's get the assigned strategy from DB (or cache)
            assigned_strat, strat_score = self.db.get_assigned_strategy(symbol) 
            
            # SAFEGUARD: Only trade if backtest was profitable or near breakeven
            # Relaxed filter to allow "slightly negative" strategies to run live (Market regime might differ)
            current_score = strat_score if strat_score is not None else -999.0
            
            if current_score <= -1.0 and assigned_strat != "HOLD":
                 logger.info(f"  🚫 {symbol}: Strategy {assigned_strat} skipped (Poor Expectancy: {current_score:.2f}%)")
                 continue
            
            for strategy in self.strategies:
                # ROUTING LOGIC:
                # 1. If Strategy is RegressionSurfer, ALWAYS RUN IT (Statistical Arbitrage Scanner).
                # 2. If Strategy is Assigned Winner, RUN IT.
                # 3. Else, SKIP.
                
                is_scanner = isinstance(strategy, RegressionSurfer)
                is_institutional = isinstance(strategy, InstitutionalGoldStrategy) and symbol in ["GOLD", "XAUUSD"]
                # Route Fat Tails to Book Strategy
                is_book_target = isinstance(strategy, BookTechnicalStrategy) and symbol in fat_tail_whitelist
                
                is_assigned = (assigned_strat and strategy.name == assigned_strat)
                
                # If no strategy, allow Institutional for GOLD or Book for Fat Tails
                if not assigned_strat:
                    if is_institutional: is_assigned = True
                    if is_book_target: is_assigned = True

                if not is_scanner and not is_assigned and not is_institutional and not is_book_target:
                     continue
                        
                # Adapter for Book Strategy (needs df directly, logic inside handles it)
                if isinstance(strategy, BookTechnicalStrategy):
                     # Book Strategy returns a list of signals for the WHOLE df. 
                     # We need to check the LAST signal.
                     # We need to wrap it to fit the "analyze(symbol, df) -> result dict" interface
                     # OR modify BookStrategy to have an analyze_live() wrapper.
                     # Quick adapter here:
                     signals = strategy.analyze(df)
                     # Check if last signal is recent (last candle)
                     # signals is a list of dicts.
                     result = {'signal': 'HOLD', 'confidence': 0, 'metadata': {}}
                     
                     if signals:
                         last_sig = signals[-1]
                         # Check time. Creating a robust time check is hard without converting everything.
                         # Assuming the strategy returned a valid signal for the *current* state.
                         # The `analyze` method in BookStrategy checks `i = len(df)-1`.
                         # So if it returned a signal, it IS for now (or the very last bar).
                         
                         result = {
                             'signal': last_sig['signal'],
                             'confidence': 0.85, # High confidence for Fat Tails
                             'setup': last_sig['strategy'],
                             'metadata': last_sig
                         }
                else:
                     result = strategy.analyze(symbol, df)
                
                # GLASS BOX FILTER
                # If Market Bias is BEARISH, ignore Buy Signals?
                # For aggressive scalping, maybe not. But let's log the conflict.
                if result['signal'] == 'BUY' and market_state['bias'] == 'BEARISH':
                     result['confidence'] *= 0.5 # Penalty
                     
                signal_type = result['signal']
                if signal_type in ['BUY', 'SELL']:
                    logger.info(f"  👉 {symbol} [{strategy.name}]: {signal_type} | Conf: {result.get('confidence', 0)}")
                    
                    if self.cloud_logger:
                        setup_info = result.get('setup', 'Standard')
                        self.cloud_logger.log_reasoning(
                            symbol, 
                            f"SIGNAL: {strategy.name}", 
                            f"{signal_type} based on {setup_info}. Conf: {result.get('confidence', 0)}"
                        )
                    
                    if best_result is None or result.get('confidence', 0) > best_result.get('confidence', 0):
                        best_result = result
                        best_result['strategy'] = strategy.name
            
            if not best_result:
                best_result = {"signal": "HOLD", "reason": "No Strategy Triggered"}

            # 3. Prepare Dashboard Scan Item (Using Brain Data)
            scan_item = {
                "symbol": symbol,
                "price": df['close'].iloc[-1],
                "change_24h": ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100,
                "trend": market_state['timeframes']['H1']['trend'],
                "risk": "HIGH" if market_state['timeframes']['H1']['volatility'] == 'HIGH' else "LOW",
                "signal": best_result['signal'] if best_result['signal'] in ['BUY', 'SELL'] else None,
                "strategy": best_result.get('strategy', ''),
                "score": market_state['score'],
                "reasoning": market_state['reasoning'],
                "categories": market_state.get('categories', {}), # NEW: Pass Categories to UI
                "ai_insight": market_state.get('ai_insight', '{}')
            }
            current_scan["Detailed Analysis"].append(scan_item)

            # 4. Execute Best Signal
            if best_result['signal'] in ['BUY', 'SELL']:
                logger.info(f"  ⚡ SIGNAL DETECTED for {symbol}: {best_result['signal']} via {best_result['strategy']}")
                
                # Risk Check
                account_info = self.execution.get_account_info()
                safe, reason = self.circuit_breaker.check_safe_to_trade(account_info)
                
                if not safe:
                    logger.warning(f"  🛑 Trade Rejected by Circuit Breaker: {reason}")
                    self.db.log("WARNING", "Engine", f"Trade rejected: {reason}", {"symbol": symbol})
                    continue

                if not Config.enable_trading:
                    logger.info("  🔒 Trading Disabled in Settings. Skipping execution.")
                    continue

                # Calculate Optimal Position Size (Kelly Criterion)
                account_info = self.execution.get_account_info()
                equity = account_info.get('equity', 10000)
                
                # Get metrics for position sizing
                metrics = best_result.get('metrics', {})
                z_score = metrics.get('z_score', 0)
                
                # Estimate win probability from Z-Score
                win_prob = self.position_sizer.estimate_win_probability(z_score) if z_score else 0.6
                
                # Calculate SL/TP based on volatility
                std_dev = metrics.get('std_dev', 0)
                entry_price = market_state.get('prices', {}).get('current', 0)
                
                if std_dev and entry_price:
                    # SL at 1 std dev, TP at 2 std dev (risk-reward ratio)
                    stop_loss = entry_price - std_dev if best_result['signal'] == 'BUY' else entry_price + std_dev
                    take_profit = entry_price + (2 * std_dev) if best_result['signal'] == 'BUY' else entry_price - (2 * std_dev)
                    
                    # Calculate optimal lot size
                    lot_size = self.position_sizer.calculate_position_size(
                        equity=equity,
                        symbol=symbol,
                        entry_price=entry_price,
                        stop_loss=stop_loss,
                        win_probability=win_prob,
                        win_loss_ratio=2.0  # Our TP is 2x our SL
                    )
                else:
                    # Fallback to conservative default
                    lot_size = 0.01
                    stop_loss = None
                    take_profit = None
                
                # Execute
                logger.info(f"  🚀 Executing {best_result['signal']} on {symbol} | Lot: {lot_size} | Win Prob: {win_prob*100:.0f}%")
                trade_result = self.execution.execute_order(
                    symbol=symbol, 
                    order_type=best_result['signal'], 
                    volume=lot_size,
                    sl_pips=50,   # Backup fixed SL
                    tp_pips=100,  # Backup fixed TP
                    comment=f"Titan-{best_result['strategy'][:3]}"
                )
                
                if trade_result:
                    logger.info(f"  ✅ Order Success: {trade_result}")
                    self.db.record_trade(trade_result)
                    
                    if self.cloud_logger:
                        self.cloud_logger.log_trade(trade_result)
                        
                    self.notifier.send_trade_alert(trade_result, market_analysis=market_state)
                    # Use asyncio task for telegram to not block
                    asyncio.create_task(self.telegram.send_trade_alert(trade_result, market_state))
                else:
                    logger.error(f"  ❌ Order Failed for {symbol}")
        
        # Update shared state for API
        self.scan_results = current_scan

    async def generate_daily_report(self):
        """Generates and sends the daily profit report."""
        # Prevent spam - only generate once per day
        today = datetime.datetime.now().date()
        if self.last_report_date == today:
            return  # Already sent today
            
        logger.info("📊 Generating Daily Report...")
        try:
            trades = self.db.get_trades_today()
            account = self.execution.get_account_summary()
            
            # FIX: Handle None profits safely
            total_profit = sum(t.get('profit', 0) or 0 for t in trades)
            win_count = sum(1 for t in trades if (t.get('profit') or 0) > 0)
            
            stats = {
                'total_profit': total_profit,
                'trades_count': len(trades),
                'win_rate': (win_count / len(trades) * 100) if trades else 0,
                'balance': account.get('balance', 0),
                'equity': account.get('equity', 0)
            }
            
            self.notifier.send_daily_report(stats)
            
            # Send Telegram Summary
            tg_msg = (
                f"📊 DAILY REPORT\n"
                f"Profit: ${stats['total_profit']:.2f}\n"
                f"Trades: {stats['trades_count']} (Win Rate: {stats['win_rate']:.1f}%)\n"
                f"Equity: ${stats['equity']:.2f}"
            )
            asyncio.create_task(self.telegram.send_message(tg_msg, priority="SUCCESS"))

            self.last_report_date = today
            logger.info("✅ Daily Report Sent")
            
        except Exception as e:
            logger.error(f"Failed to generate daily report: {e}")

if __name__ == "__main__":
    engine = TitanEngine()
    try:
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        pass
