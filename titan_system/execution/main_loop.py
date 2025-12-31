import time
import logging
import traceback
from datetime import datetime, timezone
import pandas as pd

from titan_system.data.ingest_mt5 import ingest_history
from titan_system.research.data_loader import load_data
from titan_system.research.backtester import Backtester
from titan_system.portfolio.risk_engine import RiskEngine
from titan_system.execution.mt5_executor import MT5Executor

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("titan_live.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("Titan.Live")

from titan_system.research.strategies.trend_surfer import TrendSurferStrategy
from titan_system.research.scanner import MarketScanner
from titan_system.notifications.telegram_bot import TelegramNotifier
from titan_system.execution.trade_manager import TradeManager
import asyncio

class TitanBot:
    def __init__(self, universe=None):
        # Expanded Universe: Mega Movers (FX, Crypto, Indices, Commodities)
        self.universe = universe or [
            "GOLD", "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", # FX
            "BTCUSD", "ETHUSD", "SOLUSD", "MATICUSD", # Crypto
            "US500", "US30", "USTEC", "GER40", # Indices
            "WTI" # Commodities
        ]
        self.risk_engine = RiskEngine(max_daily_drawdown=0.05)
        self.executor = MT5Executor(risk_engine=self.risk_engine)
        self.strategy = TrendSurferStrategy()
        self.scanner = MarketScanner(self.strategy, universe=self.universe)
        self.notifier = TelegramNotifier()
        self.trade_manager = TradeManager()
        self.running = False
        
    def start(self):
        self.running = True
        log.info(f"[START] Titan Intelligent Scanner Started (Universe Size: {len(self.universe)})")
        
        while self.running:
            try:
                if not self.executor.connect():
                    log.error("Failed to connect to MT5. Retrying in 30s...")
                    self.send_telegram_sync("⚠️ *Titan Alert:* MT5 Connection Lost. Attempting auto-recovery...")
                    time.sleep(30)
                    continue

                log.info("[HEARTBEAT] System Healthy. Initializing cycle...")
                self.run_cycle()

                # Smart Sleep: Wait for next candle close (Top of Hour)
                now = datetime.now(timezone.utc)
                next_hour = now.replace(minute=0, second=0, microsecond=0).timestamp() + 3600
                sleep_seconds = next_hour - now.timestamp() + 5 
                
                log.info(f"Waiting for next candle close... Sleeping {int(sleep_seconds/60)}m {int(sleep_seconds%60)}s")
                time.sleep(sleep_seconds)

            except Exception as e:
                log.critical(f"UNHANDLED CRASH in Main Loop: {e}")
                log.error(traceback.format_exc())
                self.send_telegram_sync(f"🚨 *CRITICAL CRASH:* {e}\nAttempting system restart...")
                time.sleep(10) # Cooling period before restart

    def send_telegram_sync(self, msg, priority="NORMAL"):
        """Sync wrapper for async telegram send."""
        if self.notifier and self.notifier.enabled:
            try:
                asyncio.run(self.notifier.send_message(msg, priority=priority))
            except Exception as e:
                log.error(f"Telegram Notification Failed: {e}")

    def run_cycle(self):
        """One complete scanning and execution cycle."""
        try:
            log.info("--- Starting Market Scan Cycle ---")
            
            # 0. Manage Active Trades (Break-Even / Partial TP)
            self.trade_manager.monitor_active_trades()
            
            # 1. Scan the Universe
            opportunities = self.scanner.scan()
            
            if not opportunities:
                log.info("No high-quality opportunities found in this cycle.")
                return

            # 2. Pick the Best Opportunity (Highest Score)
            best = opportunities[0]
            symbol = best['symbol']
            score = best['score']
            signal = best['order_type']
            comment = best['comment']
            ctx = best.get('context', {})
            
            log.info(f"Market Climate: {ctx.get('climate')} {ctx.get('meter')} (Speed: {ctx.get('speed_ratio', 1):.2f}x)")
            log.info(f"Best Opportunity: {symbol} (Score: {score}/100) -> {signal}")
            log.info(f"Reason: {comment}")
            
            # Print Checklist for transparency
            log.info("--- Decision Checklist ---")
            for item in best.get('checklist', []):
                log.info(f"  {item}")
            log.info("--------------------------")

            # 3. Execution Threshold
            if score >= 80 and signal in ["BUY", "SELL"]:
                log.info(f"[TRADE] Executing BEST signal: {symbol} {signal}...")
                
                # Pre-trade Notification
                self.send_telegram_sync(f"🚨 *TRADE ALERT: {symbol}*\nScore: {score}/100\nSignal: {signal}\nReason: {comment}", priority="HIGH")
                
                result = self.executor.execute_order(symbol, signal, 0.01, comment=f"Scanner: {comment}")
                
                if result:
                    self.send_telegram_sync(f"✅ *TRADE SUCCESS*\n{symbol} {signal} @ {result.get('price')}\nSL: {result.get('sl')} | TP: {result.get('tp')}", priority="SUCCESS")
                else:
                    self.send_telegram_sync(f"❌ *TRADE FAILED*\n{symbol} {signal} - Check logs for Risk/MT5 error.")
            else:
                log.info(f"Score ({score}) below execution threshold (80). Watching...")
                # Small update for high-conviction holds (e.g. 60-80)
                if score >= 60:
                    self.send_telegram_sync(f"🔍 *Scanned High Probability:* {symbol} (Score: {score})\nWaiting for full confluence.")
                
        except Exception as e:
            log.error(f"Cycle Error: {e}")
            log.error(traceback.format_exc())

if __name__ == "__main__":
    # You can define a custom universe here
    bot = TitanBot()
    bot.start()
