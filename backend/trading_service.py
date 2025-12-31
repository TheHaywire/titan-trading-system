import threading
import time
import logging
import MetaTrader5 as mt5
import sys
import os

# Add parent directory to path to import existing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mt5_interface import MT5Interface
from core.strategy import Strategy
from notification import EmailNotification
from core.market_scanner import MarketScanner
import config
import schedule

class TradingService:
    def __init__(self):
        self.trader = None
        self.thread = None

    def start(self):
        if self.trader and self.trader.running:
            return "Already running"
        
        # Import here to avoid circulars if any
        from autonomous_trader import AutonomousTrader
        self.trader = AutonomousTrader()
        
        self.thread = threading.Thread(target=self.trader.start_24_7_monitoring)
        self.thread.daemon = True # Kill when main process dies
        self.thread.start()
        return "Started Autonomous Trader"

    def stop(self):
        if self.trader:
            self.trader.stop()
        if self.thread:
            self.thread.join(timeout=5)
        return "Stopped"

    def get_status(self):
        if not self.trader:
            return {"running": False, "equity": 0}
            
        # Get live equity if connected
        equity = 0
        if self.trader.interface.connected:
            info = mt5.account_info()
            if info: equity = info.equity
            
        return {
            "running": self.trader.running,
            "connected": self.trader.interface.connected,
            "equity": equity,
            "active_schedules": len(schedule.jobs),
            "exposure": self.trader.get_net_exposure() if self.trader else {},
            "regime": self.trader.market_regime if self.trader else {},
            "latency": self.trader.interface.get_latency() if self.trader else -1,
            "scanner": self.trader.latest_scan_result if self.trader else {}
        }
    
    def get_reasoning_data(self):
        if not self.trader:
            return {"accepted": [], "rejected": []}
        return self.trader.latest_reasoning_log

trading_service = TradingService()
