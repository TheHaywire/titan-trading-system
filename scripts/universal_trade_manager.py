import sys
import os
import time
import logging
import MetaTrader5 as mt5
from datetime import datetime

# Path Hack
sys.path.append(os.getcwd())

from titan_system.execution.trade_manager import TradeManager
from rich.console import Console
from rich.table import Table

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SHIELD] %(message)s',
    handlers=[
        logging.FileHandler("universal_trade_manager.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Shield")
console = Console()

class UniversalShield:
    """
    Standalone Trade Protection Daemon.
    Monitors all active positions and applies the Tiered De-Risking logic.
    """
    
    def __init__(self):
        self.manager = TradeManager() # Manages all configured magic numbers
        self.interval = 5 # Rapid check every 5 seconds
        
    def start(self):
        console.print("[bold green]TITAN UNIVERSAL SHIELD - ONLINE[/bold green]")
        console.print("Protecting all strategies with Tiered De-Risking...")
        console.print(f"Managed Magics: {self.manager.managed_magics}")
        console.print("-" * 50)
        
        if not mt5.initialize():
            logger.error("MT5 initialization failed")
            return
        
        try:
            while True:
                # Run the management cycle
                self.manager.monitor_active_trades()
                
                # Visual Dashboard Update (Every 60s)
                self.display_status(60)
                
                time.sleep(self.interval)
                
        except KeyboardInterrupt:
            logger.info("Universal Shield stopped by user.")
        finally:
            mt5.shutdown()

    def display_status(self, cycle_interval):
        # We use a static counter for visual status
        if not hasattr(self, '_last_summary'): self._last_summary = 0
        if time.time() - self._last_summary < cycle_interval: return
        self._last_summary = time.time()
        
        positions = mt5.positions_get()
        if positions is None: return
        
        table = Table(title=f"Shield Status - {datetime.now().strftime('%H:%M:%S')}")
        table.add_column("Ticket", style="cyan")
        table.add_column("Symbol", style="white")
        table.add_column("Profit ($)", style="green")
        table.add_column("SL", style="yellow")
        
        for pos in positions:
            if pos.magic in self.manager.managed_magics:
                table.add_row(
                    str(pos.ticket),
                    pos.symbol,
                    f"${pos.profit:,.2f}",
                    f"{pos.sl:.5f}"
                )
        
        console.clear() # Optional: keep terminal clean
        console.print(table)
        console.print(f"\n[dim]Next full summary in {cycle_interval}s...[/dim]")

if __name__ == "__main__":
    shield = UniversalShield()
    shield.start()
