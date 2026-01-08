"""
LIVE TRADING DASHBOARD - ENHANCED
==================================
Real-time monitoring with:
- Regime Detection (Markov Switching Model)
- Auto-Strategy Recommendations
- Position Management Status
- Monte Carlo Validation
- Advanced Analytics
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich import box

# Import Titan Analytics
try:
    from titan_system.analytics.regime_detector import MarkovRegimeSwitcher, MarketRegime
    from titan_system.analytics.auto_strategy import AutoStrategySelector
    REGIME_AVAILABLE = True
except ImportError:
    REGIME_AVAILABLE = False

console = Console()

class TradingDashboard:
    def __init__(self):
        self.watchlist = ["GOLD", "XAUUSD", "BTCUSD", "ETHUSD", "US100", "EURUSD", "GBPUSD"]
        
        # Regime Detection
        if REGIME_AVAILABLE:
            self.regime_detector = MarkovRegimeSwitcher()
            self.strategy_selector = AutoStrategySelector()
            self.regime_fitted = {}
            self.current_regimes = {}
        else:
            self.regime_detector = None
            self.strategy_selector = None
            
        self.last_regime_update = 0
        self.regime_update_interval = 60  # Update regime every 60s
        
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
            Layout(name="left", ratio=2),
            Layout(name="right", ratio=3)
        )
        
        layout["left"].split_column(
            Layout(name="account", size=9),
            Layout(name="positions")
        )
        
        layout["right"].split_column(
            Layout(name="top_right"),
            Layout(name="bottom_right")
        )
        
        layout["right"]["top_right"].split_row(
            Layout(name="regime"),
            Layout(name="signals")
        )
        
        layout["right"]["bottom_right"].update(self.make_market_scan())
        
        # Header
        layout["header"].update(self.make_header())
        
        # Account info
        layout["account"].update(self.make_account_panel())
        
        # Positions
        layout["positions"].update(self.make_positions_table())
        
        # Regime Detection Panel (NEW)
        layout["right"]["top_right"]["regime"].update(self.make_regime_panel())
        
        # Signals
        layout["right"]["top_right"]["signals"].update(self.make_signals_panel())
        
        # Footer
        layout["footer"].update(self.make_footer())
        
        return layout
        
    
    def make_header(self):
        """Header with title and time"""
        text = Text()
        text.append("🤖 AUTONOMOUS TRADING DASHBOARD", style="bold cyan")
        text.append(" | ", style="white")
        text.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), style="yellow")
        text.append(" | ", style="white")
        if REGIME_AVAILABLE:
            text.append("Regime Detection: ACTIVE", style="bold green")
        else:
            text.append("Regime Detection: DISABLED", style="dim")
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
        
        return Panel(table, title=f"[POSITIONS] Open Positions ({len(positions)})", border_style="blue")
    
    def make_regime_panel(self):
        """Regime detection panel showing market state for key symbols"""
        if not REGIME_AVAILABLE or not self.regime_detector:
            return Panel("[dim]Regime detection not available[/dim]", title="[REGIME]", border_style="dim")
        
        table = Table(box=box.SIMPLE, padding=(0, 1), show_header=True)
        table.add_column("Symbol", style="cyan")
        table.add_column("Regime", justify="center")
        table.add_column("Conf", justify="right")
        table.add_column("Strategy", justify="left")
        
        # Only update regimes periodically to avoid lag
        now = time.time()
        should_update = (now - self.last_regime_update) > self.regime_update_interval
        
        key_symbols = ["GOLD", "XAUUSD", "BTCUSD", "EURUSD"]
        
        for symbol in key_symbols:
            try:
                if not mt5.symbol_select(symbol, True):
                    continue
                
                # Get H1 data for regime detection
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 150)
                if rates is None or len(rates) < 100:
                    continue
                
                df = pd.DataFrame(rates)
                
                # Fit on first call
                if symbol not in self.regime_fitted:
                    self.regime_detector.fit(df)
                    self.regime_fitted[symbol] = True
                
                # Detect regime
                if should_update or symbol not in self.current_regimes:
                    regime_state = self.regime_detector.detect(df)
                    self.current_regimes[symbol] = regime_state
                else:
                    regime_state = self.current_regimes.get(symbol)
                
                if not regime_state:
                    continue
                
                # Get recommendation
                rec = self.regime_detector.get_strategy_recommendation(regime_state)
                
                # Format regime display
                regime_name = regime_state.current_regime.value
                if regime_name == "TRENDING":
                    regime_style = "bold green"
                    regime_icon = "📈"
                elif regime_name == "MEAN_REVERTING":
                    regime_style = "bold yellow"
                    regime_icon = "↔️"
                elif regime_name == "HIGH_VOLATILITY":
                    regime_style = "bold red"
                    regime_icon = "⚡"
                else:
                    regime_style = "dim"
                    regime_icon = "?"
                
                confidence = regime_state.confidence * 100
                preferred = rec.get('preferred_strategies', [])[:2]  # First 2
                pref_str = ", ".join(preferred) if preferred else "-"
                
                table.add_row(
                    symbol,
                    f"[{regime_style}]{regime_icon} {regime_name}[/]",
                    f"{confidence:.0f}%",
                    f"[dim]{pref_str}[/]"
                )
                
            except Exception:
                continue
        
        if should_update:
            self.last_regime_update = now
        
        return Panel(table, title="[REGIME] Markov Detection", border_style="magenta")
    
    def make_signals_panel(self):
        """Bot activity with regime-aware status"""
        text = Text()
        
        # Count regimes
        regime_counts = {"TRENDING": 0, "MEAN_REVERTING": 0, "HIGH_VOLATILITY": 0}
        if self.current_regimes:
            for sym, state in self.current_regimes.items():
                regime_name = state.current_regime.value if state else "UNKNOWN"
                if regime_name in regime_counts:
                    regime_counts[regime_name] += 1
        
        text.append("🔍 Scanning every 30s\\n", style="dim")
        text.append(f"📊 Watchlist: {len(self.watchlist)} symbols\\n", style="cyan")
        text.append("\\n")
        
        # Regime summary
        text.append("MARKET REGIMES:\\n", style="bold white")
        if regime_counts["TRENDING"] > 0:
            text.append(f"  📈 Trending: {regime_counts['TRENDING']}\\n", style="green")
        if regime_counts["MEAN_REVERTING"] > 0:
            text.append(f"  ↔️ Ranging: {regime_counts['MEAN_REVERTING']}\\n", style="yellow")
        if regime_counts["HIGH_VOLATILITY"] > 0:
            text.append(f"  ⚡ High Vol: {regime_counts['HIGH_VOLATILITY']}\\n", style="red")
        
        text.append("\\n")
        text.append("🎯 Min Score: 70\\n", style="yellow")
        text.append("🛡️ Regime risk multiplier active\\n", style="cyan")
        
        return Panel(text, title="[ACTIVITY] Bot Status", border_style="yellow")
    
    def make_market_scan(self):
        """Market scan showing current signals with regime info"""
        table = Table(box=box.SIMPLE_HEAD, padding=(0, 1))
        table.add_column("Symbol", style="cyan")
        table.add_column("Signal", justify="center")
        table.add_column("RSI", justify="right")
        table.add_column("Trend", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Regime", justify="center")
        
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
                
                # Get cached regime if available
                regime_display = "[dim]-[/]"
                if hasattr(self, 'current_regimes') and symbol in self.current_regimes:
                    state = self.current_regimes[symbol]
                    if state:
                        regime_name = state.current_regime.value
                        if regime_name == "TRENDING":
                            regime_display = "[green]📈 Trend[/]"
                        elif regime_name == "MEAN_REVERTING":
                            regime_display = "[yellow]↔ Range[/]"
                        elif regime_name == "HIGH_VOLATILITY":
                            regime_display = "[red]⚡ HiVol[/]"
                
                table.add_row(
                    symbol,
                    f"[{signal_color}]{signal}[/]",
                    f"{curr['rsi']:.0f}",
                    f"[{trend_color}]{trend}[/]",
                    f"[{score_color}]{score}[/]",
                    regime_display
                )
                
            except Exception:
                continue
        
        return Panel(table, title="[SCANNER] Market Signals (M5) + Regime", border_style="magenta")
    
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
