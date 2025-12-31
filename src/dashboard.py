"""
Titan Terminal Dashboard
Renders a high-frequency trading interface using the Rich library.
"""
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from datetime import datetime

class TitanDashboard:
    def __init__(self):
        self.console = Console()
        self.layout = Layout()
        
    def generate_table(self, market_state: dict, active_trades: list = None) -> Table:
        # Fixed box to prevent jumping
        table = Table(title=f"TITAN TERMINAL | {datetime.now().strftime('%H:%M:%S')}", style="bold white", show_lines=True, box=None, padding=(0, 1))
        
        table.add_column("TICKER", style="cyan bold", justify="left")
        table.add_column("PRICE", justify="right", style="green")
        table.add_column("SPREAD", justify="right", style="dim")
        table.add_column("TREND (H4)", justify="center")
        table.add_column("STRUCTURE", justify="center")
        table.add_column("ACTIVE PLAN / SETUP", justify="left", style="bold yellow")
        
        # ... logic ...
        
        # Define Filter Logic
        cat_map = {
            "COMMODITIES": ["GOLD", "XAU", "SILVER", "XAG", "OIL", "WTI"],
            "INDICES": ["US100", "NAS", "US500", "SPX", "US30", "DJ30", "DE40", "DAX", "GER"],
            "CRYPTO": ["BTC", "ETH", "BITCOIN", "ETHEREUM"],
            "FOREX": ["EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD"]
        }
        
        # Helper to categorize a symbol
        def get_cat(s):
            s_u = s.upper()
            for c, keywords in cat_map.items():
                if any(k in s_u for k in keywords):
                    return c
            return "OTHER"

        # Organize Data
        grouped = {"COMMODITIES": [], "INDICES": [], "CRYPTO": [], "FOREX": [], "OTHER": []}
        for sym in market_state.keys():
            cat = get_cat(sym)
            grouped[cat].append(sym)
            
        for cat, symbols in grouped.items():
            if not symbols: continue
            
            table.add_row(f"[underline]{cat}[/]", "", "", "", "", "")
            
            for sym in symbols:
                data = market_state[sym]
                
                # Formatting
                bias = data.get('bias', 'NEUTRAL')
                bias_style = "green" if bias == "BULLISH" else "red" if bias == "BEARISH" else "white"
                
                plan = data.get('plan', 'WAIT')
                struct = data.get('structure', '-')
                struct_style = "red" if "PREMIUM" in struct else "green" if "DISCOUNT" in struct else "blue"
                
                price = data.get('current_price', 0.0)
                spread = data.get('spread', 0.0)
                
                # Dynamic Precision
                fmt = ".2f"
                if "JPY" in sym: fmt = ".3f"
                elif "BTC" in sym or "US30" in sym or "DE40" in sym: fmt = ".1f"
                elif "EUR" in sym or "GBP" in sym: fmt = ".5f"
                
                table.add_row(
                    f"{sym}",
                    f"{price:{fmt}}",
                    f"{spread:.1f}", # Show spread simpler
                    f"[{bias_style}]{bias}[/{bias_style}]",
                    f"[{struct_style}]{struct}[/{struct_style}]",
                    f"{plan}"
                )
            
        return table
