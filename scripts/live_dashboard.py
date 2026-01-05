"""
LIVE TRADING DASHBOARD
======================
Real-time monitoring of all bot activity, positions, and market signals.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich import box

console = Console()

class TradingDashboard:
    def __init__(self):
        self.watchlist = ["GOLD", "XAUUSD", "BTCUSD", "ETHUSD", "US100", "EURUSD", "GBPUSD"]
        
    def start(self):
        if not mt5.initialize():
            console.print("[red]MT5 initialization failed[/red]")
            return
        
        with Live(self.generate_dashboard(), refresh_per_second=1, console=console) as live:
            while True:
                try:
                    live.update(self.generate_dashboard())
                    time.sleep(2)
                except KeyboardInterrupt:
                    break
        
        mt5.shutdown()
    
    def generate_dashboard(self):
        """Generate the full dashboard layout"""
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        layout["left"].split_column(
            Layout(name="account", size=8),
            Layout(name="positions")
        )
        
        layout["right"].split_column(
            Layout(name="signals", size=15),
            Layout(name="markets")
        )
        
        # Header
        layout["header"].update(self.make_header())
        
        # Account info
        layout["account"].update(self.make_account_panel())
        
        # Positions
        layout["positions"].update(self.make_positions_table())
        
        # Signals
        layout["signals"].update(self.make_signals_panel())
        
        # Markets
        layout["right"]["markets"].update(self.make_market_scan())
        
        # Footer
        layout["footer"].update(self.make_footer())
        
        return layout
    
    def make_header(self):
        """Header with title and time"""
        text = Text()
        text.append("🤖 AUTONOMOUS TRADING DASHBOARD", style="bold cyan")
        text.append(" | ", style="white")
        text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="yellow")
        return Panel(text, box=box.DOUBLE)
    
    def make_account_panel(self):
        """Account information panel"""
        acc = mt5.account_info()
        if not acc:
            return Panel("Account info unavailable", title="💰 Account")
        
        positions = mt5.positions_get()
        num_positions = len(positions) if positions else 0
        
        total_pnl = sum([p.profit for p in positions]) if positions else 0
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="bold white")
        
        table.add_row("Equity", f"${acc.equity:,.2f}")
        table.add_row("Balance", f"${acc.balance:,.2f}")
        table.add_row("Floating P/L", f"[{'green' if total_pnl >= 0 else 'red'}]${total_pnl:+,.2f}[/]")
        table.add_row("Open Positions", f"{num_positions}")
        table.add_row("Margin Used", f"${acc.margin:,.2f}")
        table.add_row("Free Margin", f"${acc.margin_free:,.2f}")
        
        return Panel(table, title="💰 Account Status", border_style="green")
    
    def make_positions_table(self):
        """Current positions table"""
        positions = mt5.positions_get()
        
        if not positions:
            return Panel("[dim]No open positions[/dim]", title="📊 Open Positions")
        
        table = Table(box=box.SIMPLE, padding=(0, 1))
        table.add_column("Symbol", style="cyan")
        table.add_column("Dir", style="white")
        table.add_column("Size", justify="right")
        table.add_column("Entry", justify="right")
        table.add_column("Current", justify="right")
        table.add_column("P/L", justify="right")
        
        for pos in positions[:10]:  # Show max 10
            direction = "BUY" if pos.type == 0 else "SELL"
            dir_color = "green" if pos.type == 0 else "red"
            pnl_color = "green" if pos.profit >= 0 else "red"
            
            table.add_row(
                pos.symbol,
                f"[{dir_color}]{direction}[/{dir_color}]",
                f"{pos.volume}",
                f"{pos.price_open:.5f}",
                f"{pos.price_current:.5f}",
                f"[{pnl_color}]${pos.profit:+.2f}[/{pnl_color}]"
            )
        
        return Panel(table, title=f"📊 Open Positions ({len(positions)})", border_style="blue")
    
    def make_signals_panel(self):
        """Recent signals/activity"""
        text = Text()
        text.append("🔍 Scanning markets every 30s...\n", style="dim")
        text.append("⚡ MTF Bot: Active\n", style="green")
        text.append("📈 Watching 11 symbols\n", style="cyan")
        text.append("🎯 Min Score: 75/100\n", style="yellow")
        text.append("\n")
        text.append("Waiting for high-conviction setups...", style="dim italic")
        
        return Panel(text, title="🎯 Bot Activity", border_style="yellow")
    
    def make_market_scan(self):
        """Market scan showing current signals"""
        table = Table(box=box.SIMPLE_HEAD, padding=(0, 1))
        table.add_column("Symbol", style="cyan")
        table.add_column("Signal", justify="center")
        table.add_column("RSI", justify="right")
        table.add_column("Trend", justify="center")
        table.add_column("Score", justify="right")
        
        for symbol in self.watchlist:
            try:
                if not mt5.symbol_select(symbol, True):
                    continue
                
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 50)
                if rates is None or len(rates) < 20:
                    continue
                
                df = pd.DataFrame(rates)
                df['ema9'] = df['close'].ewm(span=9).mean()
                df['ema21'] = df['close'].ewm(span=21).mean()
                
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                df['rsi'] = 100 - (100 / (1 + gain/loss))
                
                curr = df.iloc[-1]
                
                # Simple scoring
                score = 50
                signal = "HOLD"
                
                if curr['rsi'] < 30:
                    score += 25
                    signal = "BUY"
                elif curr['rsi'] > 70:
                    score += 25
                    signal = "SELL"
                
                if curr['ema9'] > curr['ema21']:
                    if signal != "SELL":
                        score += 15
                        signal = "BUY"
                elif curr['ema9'] < curr['ema21']:
                    if signal != "BUY":
                        score += 15
                        signal = "SELL"
                
                trend = "↑" if curr['ema9'] > curr['ema21'] else "↓"
                trend_color = "green" if curr['ema9'] > curr['ema21'] else "red"
                
                signal_color = "green" if signal == "BUY" else "red" if signal == "SELL" else "dim"
                score_color = "green" if score >= 75 else "yellow" if score >= 60 else "dim"
                
                table.add_row(
                    symbol,
                    f"[{signal_color}]{signal}[/{signal_color}]",
                    f"{curr['rsi']:.0f}",
                    f"[{trend_color}]{trend}[/{trend_color}]",
                    f"[{score_color}]{score}[/{score_color}]"
                )
                
            except:
                continue
        
        return Panel(table, title="📡 Market Scanner (M5)", border_style="magenta")
    
    def make_footer(self):
        """Footer with controls"""
        text = Text()
        text.append("Press ", style="dim")
        text.append("Ctrl+C", style="bold red")
        text.append(" to exit | Updates every 2 seconds", style="dim")
        return Panel(text, box=box.SIMPLE)


if __name__ == "__main__":
    dashboard = TradingDashboard()
    dashboard.start()
