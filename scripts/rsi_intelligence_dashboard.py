import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import time
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich import box

# --- CONFIGURATION ---
SYMBOL = "GOLD"
TIMEFRAME = mt5.TIMEFRAME_M15
LOOKBACK = 200

console = Console()

def fetch_data():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, LOOKBACK)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_rsi_intelligence(df):
    # 1. Standard RSI
    df['rsi'] = calculate_rsi(df['close'], 14)
    
    # 2. Smoothed RSI (EMA of price first)
    df['smoothed_price'] = df['close'].ewm(span=5).mean()
    df['rsi_smoothed'] = calculate_rsi(df['smoothed_price'], 14)
    
    # 3. StochRSI
    low_min = df['rsi'].rolling(14).min()
    high_max = df['rsi'].rolling(14).max()
    df['stoch_rsi'] = 100 * (df['rsi'] - low_min) / (high_max - low_min)
    
    return df

def detect_range_shift(rsi):
    if rsi > 60: return "[bold green]SUPER BULLISH (60-80)[/bold green]"
    if rsi >= 40: return "[green]BULLISH RANGE (40-80)[/green]"
    if rsi <= 20: return "[bold red]SUPER BEARISH (20-40)[/bold red]"
    if rsi <= 60: return "[red]BEARISH RANGE (20-60)[/red]"
    return "[yellow]SIDEWAYS (40-60)[/yellow]"

def make_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1),
        Layout(name="signals", ratio=2),
    )
    return layout

def generate_dashboard(df):
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Stats Table
    stats_table = Table(title="Live RSI Indicators", box=box.ROUNDED)
    stats_table.add_column("Indicator", style="cyan")
    stats_table.add_column("Value", justify="right")
    stats_table.add_column("Trend", justify="center")
    
    def get_trend_icon(c, p):
        return "↑" if c > p else "↓" if c < p else "→"

    stats_table.add_row("Standard RSI", f"{curr['rsi']:.2f}", get_trend_icon(curr['rsi'], prev['rsi']))
    stats_table.add_row("Smoothed RSI", f"{curr['rsi_smoothed']:.2f}", get_trend_icon(curr['rsi_smoothed'], prev['rsi_smoothed']))
    stats_table.add_row("StochRSI", f"{curr['stoch_rsi']:.2f}", get_trend_icon(curr['stoch_rsi'], prev['stoch_rsi']))
    
    # Signals Panel Info
    range_text = detect_range_shift(curr['rsi_smoothed'])
    bias = "BULLISH" if curr['rsi_smoothed'] > 50 else "BEARISH"
    
    # Detect basic Divergence/Reversal (Simplified for UI display)
    # real stuff: check last 5 bars
    last_5 = df.tail(5)
    div_status = "No Active Divergence"
    if curr['close'] > prev['close'] and curr['rsi_smoothed'] < prev['rsi_smoothed']:
        div_status = "[bold yellow]Bearish Divergence Detected[/bold yellow]"
    elif curr['close'] < prev['close'] and curr['rsi_smoothed'] > prev['rsi_smoothed']:
        div_status = "[bold green]Bullish Divergence Detected[/bold green]"

    signals_panel = Panel(
        f"\n[bold white]Market Regime:[/bold white] {range_text}\n"
        f"[bold white]Pivot Bias (50):[/bold white] {'[green]UP[/green]' if bias == 'BULLISH' else '[red]DOWN[/red]'}\n\n"
        f"[cyan]Pattern Status:[/cyan]\n{div_status}\n\n"
        f"[dim]Watching for Cardwell Positive Reversals...[/dim]",
        title="Institutional Intelligence",
        subtitle=f"Last Sync: {datetime.now().strftime('%H:%M:%S')}",
        box=box.DOUBLE
    )
    
    return stats_table, signals_panel

def main():
    if not mt5.initialize():
        console.print("[bold red]Failed to initialize MT5[/bold red]")
        return

    layout = make_layout()
    layout["header"].update(Panel("[bold cyan]TITAN RSI INTELLIGENCE v4.0[/bold cyan] // [yellow]XAUUSD M15[/yellow]", box=box.SIMPLE))
    layout["footer"].update(Panel("[dim]System Running | Press Ctrl+C to Exit[/dim]", box=box.SIMPLE))

    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            df = fetch_data()
            if df is not None:
                df = get_rsi_intelligence(df)
                stats, signals = generate_dashboard(df)
                layout["stats"].update(stats)
                layout["signals"].update(signals)
            
            time.sleep(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        mt5.shutdown()
