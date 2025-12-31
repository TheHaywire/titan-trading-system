import time
import sys
import os
import asyncio
import logging
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich import box
from datetime import datetime

# Ensure root is in path
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
from titan_system.smc.institutional_engine import InstitutionalEngine
from config.settings import settings as Config

# Setup lighter logging for CLI
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("SMC.Scanner")

class SMCSniper:
    def __init__(self):
        self.console = Console()
        self.engine = InstitutionalEngine()
        
        # Define Universe (Majors + Gold + Indices + Crosses)
        self.universe = [
            # Commodities
            "XAUUSD", "GOLD", "WTI", "BRENT",
            # Indices
            "US30", "NAS100", "SPX500", "GER40",
            # Forex Majors
            "EURUSD", "GBPUSD", "USDJPY", "USDCAD", "AUDUSD", "NZDUSD", "USDCHF",
            # Forex Crosses
            "GBPJPY", "EURJPY", "AUDJPY", "EURAUD", "GBPAUD"
        ]
        
        self.scan_results = []
        self.last_update = None
        self.is_running = True

    def connect(self):
        if not mt5.initialize():
            self.console.print("[bold red]❌ Failed to connect to MT5[/bold red]")
            return False
        return True

    def get_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, bars=500):
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None or len(rates) == 0:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def scan_universe(self):
        results = []
        
        for symbol in self.universe:
            # Check if symbol exists in Market Watch
            info = mt5.symbol_info(symbol)
            if info is None: # specific checking
                continue
                
            if not info.visible:
                if not mt5.symbol_select(symbol, True):
                    continue
            
            # Fetch Data (H1 primarily for Intraday/Swing setups)
            df = self.get_data(symbol)
            if df is None:
                continue
                
            # Analyze
            try:
                analysis = self.engine.analyze_symbol(df, symbol)
                
                # Check for Setups
                setups = analysis.get('setup', [])
                regime = analysis.get('regime', 'UNDEFINED')
                trend = analysis.get('trend', {}).get('bias', 'NEUTRAL')
                tss = analysis.get('trend', {}).get('tss', 0)
                
                if setups:
                    # Parse setup names
                    setup_names = [s['name'] for s in setups]
                    setup_str = ", ".join(setup_names)
                    trigger = setups[0].get('trigger', '')
                    
                    results.append({
                        "symbol": symbol,
                        "price": df['close'].iloc[-1],
                        "trend": trend,
                        "tss": tss,
                        "regime": regime,
                        "setups": setup_str,
                        "trigger": trigger,
                        "score": 100 # Placeholder for sorting importance
                    })
                elif regime in ["TREND_STRONG", "SQUEEZE_PRE_BREAKOUT"]:
                     # Also include strong trends or squeezes even without specific trigger
                     results.append({
                        "symbol": symbol,
                        "price": df['close'].iloc[-1],
                        "trend": trend,
                        "tss": tss,
                        "regime": regime,
                        "setups": "-",
                        "trigger": "Watch for Entry",
                        "score": 50
                    })
                    
            except Exception as e:
                # logger.error(f"Error scanning {symbol}: {e}")
                pass
                
        # Sort by Score/Importance
        results.sort(key=lambda x: x['score'], reverse=True)
        self.scan_results = results
        self.last_update = datetime.now().strftime("%H:%M:%S")

    def generate_table(self) -> Table:
        table = Table(
            title=f"🎯 SMC Sniper Scan | Updated: {self.last_update}",
            box=box.ROUNDED,
            style="cyan",
            title_style="bold magenta"
        )
        
        table.add_column("Symbol", style="bold white")
        table.add_column("Price", justify="right", style="green")
        table.add_column("Trend", style="yellow")
        table.add_column("Score", justify="center")
        table.add_column("Regime", style="blue")
        table.add_column("🚀 Setups", style="bold red")
        table.add_column("Trigger", style="italic white")
        
        for item in self.scan_results:
            # Color coding
            trend_color = "green" if item['trend'] == "BULLISH" else "red" if item['trend'] == "BEARISH" else "yellow"
            
            # Setup Coloring
            setup_display = item['setups']
            if "TCB" in setup_display:
                setup_display = f"[bold green]{setup_display}[/bold green]" if "BULLISH" in setup_display else f"[bold red]{setup_display}[/bold red]"
            elif "LSR" in setup_display:
                setup_display = f"[bold gold1]{setup_display}[/bold gold1]"
            
            table.add_row(
                item['symbol'],
                f"{item['price']:.2f}",
                f"[{trend_color}]{item['trend']}[/{trend_color}]",
                str(item['tss']),
                item['regime'],
                setup_display,
                item['trigger']
            )
            
        return table

    def run(self):
        if not self.connect():
            return
            
        self.console.print("[bold yellow]🚀 Initializing SMC Sniper... Scanning Market...[/bold yellow]")
        
        with Live(self.generate_table(), refresh_per_second=1) as live:
            while self.is_running:
                self.scan_universe()
                live.update(self.generate_table())
                
                # Wait 60s before next scan, but update clock?
                # For responsiveness, we just sleep. 
                # Ideally, we'd have a timer but this is a simple loop.
                for _ in range(60): 
                    time.sleep(1)

if __name__ == "__main__":
    try:
        sniper = SMCSniper()
        sniper.run()
    except KeyboardInterrupt:
        print("\n\n🛑 Screener Stopped.")
