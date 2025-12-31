"""
TITAN TRADING SYSTEM v2.0 (Service Entry Point)
Implement the 'Hierarchy of Truth' architecture.
"""
import time
import signal
import sys
import MetaTrader5 as mt5
from datetime import datetime
from src.core.risk import RiskManager
from src.strategy.liquidity_sweeper import LiquiditySweeper
from src.core.logger import SystemLogger
from src.dashboard import TitanDashboard
from rich.live import Live

class TitanService:
    def __init__(self):
        self.logger = SystemLogger()
        self.risk = RiskManager()
        self.strategy = LiquiditySweeper()
        self.dashboard = TitanDashboard()
        self.running = False
        
    def startup(self):
        """Initialize System"""
        self.logger.info("🚀 TITAN SYSTEM v2.0 STARTING UP...")
        
        # 1. Connect to MT5
        if not mt5.initialize():
            self.logger.error(f"MT5 Init Failed: {mt5.last_error()}")
            sys.exit(1)
            
        # 2. Check Risk/Health
        if not self.risk.check_health():
             self.logger.critical("Risk Check Failed. Aborting.")
             sys.exit(1)
             
        self.running = True
        self.logger.info("✅ System Online & Healthy")
        
        # Initial Scans
        self.logger.info("Performing Initial Market Scans...")
        self.strategy.scan_strategic()
        self.strategy.scan_tactical()

    def main_loop(self):
        """The Heartbeat"""
        # Wrap in Rich Live context
        with Live(self.dashboard.generate_table(self.strategy.market_state), refresh_per_second=1, screen=True) as live:
            while self.running:
                try:
                    # 1. Update H1/H4 Zones periodically (Logic simplified here)
                    # For now, we assume they persist, but ideally re-scan every hour.
                    # self.strategy.scan_tactical() 
                    
                    # 2. Execution Tick (Real-time)
                    # self.strategy.refresh_market_data() # Optim: Removed redundant call
                    self.strategy.on_tick()
                    
                    # 3. Update UI
                    live.update(self.dashboard.generate_table(self.strategy.market_state))
                    
                    pass # High frequency -> minimal sleep
                    
                except KeyboardInterrupt:
                    self.shutdown()
                except Exception as e:
                    self.logger.error(f"Main Loop Error: {e}")
                    time.sleep(5)
                
    def shutdown(self):
        self.logger.info("🛑 SHUTTING DOWN...")
        self.running = False
        mt5.shutdown()
        sys.exit(0)

if __name__ == "__main__":
    service = TitanService()
    signal.signal(signal.SIGINT, lambda s, f: service.shutdown())
    service.startup()
    service.main_loop()
