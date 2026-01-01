"""
Institutional Monitoring Dashboard (EPIC-11)
A real-time terminal UI using the Rich library.
Displays Portfolio Health, Quant Risk (VaR), and Execution Logs.
"""

import time
import os
import sys
from datetime import datetime

# Ensure root is in path
sys.path.append(os.getcwd())

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console
from rich.text import Text
from rich import box

import MetaTrader5 as mt5
from titan_system.analytics.institutional_risk import InstitutionalQuant
from titan_system.core.execution import MT5Execution
from config.settings import settings as Config

class TitanDashboard:
    def __init__(self):
        self.console = Console()
        self.quant = InstitutionalQuant()
        self.execution = MT5Execution(Config)
        self.execution.connect()
        
    def make_header(self) -> Panel:
        """Creates the dashboard header."""
        grid = Table.grid(expand=True)
        grid.add_column(justify="left", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="right", ratio=1)
        
        # Kill Switch Status
        # We simulate checking a file or a state
        ks_status = "[bold green]SAFE[/bold green]"
        
        grid.add_row(
            Text(f"🕒 {datetime.now().strftime('%H:%M:%S')}", style="cyan"),
            Text("🏛️ TITAN INSTITUTIONAL COMMAND", style="bold white"),
            Text(f"🛡️ Safety: {ks_status}", style="bold")
        )
        return Panel(grid, style="blue")

    def make_portfolio_panel(self) -> Panel:
        """Displays account equity and leverage."""
        acc = mt5.account_info()
        if not acc:
            return Panel("❌ MT5 Offline", title="Portfolio", border_style="red")
            
        table = Table.grid(expand=True)
        table.add_column(style="dim")
        table.add_column(justify="right")
        
        table.add_row("Balance", f"${acc.balance:,.2f}")
        table.add_row("Equity", f"[bold green]${acc.equity:,.2f}[/bold green]")
        table.add_row("Margin Level", f"{acc.margin_level:.2f}%")
        
        # Calculated Leverage
        notional = sum([p.volume * 100000 * p.price_current for p in (mt5.positions_get() or [])])
        eff_lev = notional / acc.equity if acc.equity > 0 else 0
        
        table.add_row("Eff. Leverage", f"{eff_lev:.2x}")
        
        return Panel(table, title="[bold white]Account Health[/bold white]", border_style="cyan")

    def make_risk_panel(self) -> Panel:
        """Displays VaR and Concentration metrics."""
        positions = mt5.positions_get()
        var_results = self.quant.calculate_var(positions)
        
        table = Table.grid(expand=True)
        table.add_column(style="dim")
        table.add_column(justify="right")
        
        table.add_row("VaR (95%)", f"[bold red]${var_results['total_var_usd']:,.2f}[/bold red]")
        table.add_row("VaR %", f"{var_results['var_percentage']:.2f}%")
        
        stress = self.quant.simulate_black_swan(positions, 0.05)
        table.add_row("Crash Test (5%)", f"-${stress:,.2f}")
        
        return Panel(table, title="[bold white]Quant Risk (VaR)[/bold white]", border_style="magenta")

    def make_trades_table(self) -> Table:
        """Creates a table of active positions."""
        table = Table(box=box.SIMPLE, expand=True)
        table.add_column("Symbol", style="bold")
        table.add_column("Type", justify="center")
        table.add_column("Lots", justify="right")
        table.add_column("Profit", justify="right")
        table.add_column("Duration", justify="right")
        
        positions = mt5.positions_get()
        if not positions:
            table.add_row("No Active Positions", "", "", "", "")
            return table
            
        for p in positions:
            color = "green" if p.profit > 0 else "red"
            dur = (datetime.now().timestamp() - p.time) / 60 # minutes
            table.add_row(
                p.symbol,
                "BUY" if p.type == 0 else "SELL",
                str(p.volume),
                f"[{color}]${p.profit:,.2f}[/{color}]",
                f"{dur:.1f}m"
            )
        return table

    def generate_layout(self) -> Layout:
        """Assembles the dashboard layout."""
        layout = Layout()
        layout.split(
             Layout(name="header", size=3),
             Layout(name="main", ratio=1),
             Layout(name="footer", size=3)
        )
        layout["main"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="right", ratio=2)
        )
        layout["left"].split_column(
            Layout(name="portfolio", ratio=1),
            Layout(name="risk", ratio=1)
        )
        
        # Fill Content
        layout["header"].update(self.make_header())
        layout["portfolio"].update(self.make_portfolio_panel())
        layout["risk"].update(self.make_risk_panel())
        layout["right"].update(Panel(self.make_trades_table(), title="Active Market Exposure"))
        layout["footer"].update(Panel("Press Ctrl+C to Exit Institutional View", style="dim center"))
        
        return layout

def run_dashboard():
    dashboard = TitanDashboard()
    with Live(dashboard.generate_layout(), refresh_per_second=1) as live:
        try:
            while True:
                time.sleep(1)
                live.update(dashboard.generate_layout())
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    run_dashboard()
