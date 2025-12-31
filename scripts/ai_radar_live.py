
import os
import sys
import time
import pandas as pd
import polars as pl
import MetaTrader5 as mt5
from datetime import datetime
import json

# Ensure Project Root is in Path
sys.path.append(os.getcwd())

try:
    from titan_system.ai.features import compute_features
    from config.settings import settings as Config
except ImportError:
    print("❌ Could not import Titan System components. Run from project root.")
    sys.exit(1)

# Try to import Rich
try:
    from rich.console import Console
    from rich.table import Table
    from rich.live import Live
    from rich.panel import Panel
    USE_RICH = True
except ImportError:
    USE_RICH = False

def get_radar_data():
    if not mt5.initialize():
        return None
    
    # Fetch GOLD data (H1 for tactical)
    symbol = "XAUUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
    if rates is None:
        # Try GOLD
        symbol = "GOLD"
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)
    
    if rates is None:
        return None
        
    df = pd.DataFrame(rates)
    pl_df = pl.from_pandas(df)
    
    # Compute v2 Features (Expanded Institutional Set)
    try:
        clean_df, matrix = compute_features(pl_df, version="v2")
        latest = clean_df.tail(1).to_dicts()[0]
        return latest
    except Exception as e:
        print(f"Error computing features: {e}")
        return None

def display_radar():
    console = Console()
    console.print("[bold yellow]🚀 TITAN AI RADAR STARTING...[/bold yellow]")
    
    with Live(console=console, refresh_per_second=0.5) as live:
        # Run for a few iterations in demo mode or forever
        for _ in range(5):
            data = get_radar_data()
            if not data:
                live.update(Panel("MetaTrader 5 Connection Failed or Data Unavailable.\nEnsure MT5 is logged in and 'GOLD' or 'XAUUSD' is in Market Watch.", title="[red]Connection Error"))
                time.sleep(5)
                continue
            
            table = Table(title=f"🏛️ TITAN INSTITUTIONAL SENSORS: XAUUSD (GOLD)\n[dim]Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")
            table.add_column("Institutional Sensor", style="cyan", no_wrap=True)
            table.add_column("AI Normalized [0→1]", justify="center", style="bold green")
            table.add_column("Market Condition", justify="left")
            table.add_column("Strategy Category", style="dim")

            sensors = [
                ("RSI Momentum", "f_rsi", "Momentum"),
                ("Trend Structure", "f_trend", "Trend Following"),
                ("Volatility Heat", "f_vol", "Volatility"),
                ("CCI Mean Reversal", "f_cci", "Mean Reversion"),
                ("Williams %R (Exhaustion)", "f_wr", "Mean Reversion"),
                ("Stochastic Oscillations", "f_stoch", "Momentum / Scalp"),
                ("ADX Trend Strength", "f_adx", "Volatility / Trend"),
                ("Pullback Depth", "f_pullback", "Execution Quality"),
            ]

            for label, key, category in sensors:
                val = data.get(key, 0.5)
                
                # Market Condition Logic
                condition = "Normal"
                color = "white"
                if val < 0.2: 
                    condition = "EXTREME OVERSOLD / WEAK"
                    color = "blue"
                elif val < 0.4:
                    condition = "BULLISH ACCUMULATION / OVERSOLD"
                    color = "cyan"
                elif val > 0.8:
                    condition = "EXTREME OVERBOUGHT / EXHAUSTION"
                    color = "red"
                elif val > 0.6:
                    condition = "BULLISH MOMENTUM / OVERBOUGHT"
                    color = "yellow"

                table.add_row(
                    label, 
                    f"{val:.3f}", 
                    f"[{color}]{condition}[/{color}]",
                    category
                )

            # Institutional Logic Narrative
            logic_narrative = []
            adx_val = data.get('f_adx', 0)
            wr_val = data.get('f_wr', 0.5)
            cci_val = data.get('f_cci', 0.5)
            trend_val = data.get('f_trend', 0)

            # 1. Trend Analysis logic
            if adx_val < 0.25:
                logic_narrative.append("⚠️ [yellow]CHOPPY MARKET[/yellow]: ADX is weak. 'Breakout' and 'Trend Following' categories are [dim]SUPPRESSED[/dim] to avoid traps.")
            elif trend_val > 0.4:
                logic_narrative.append("🚀 [green]TREND ALIGNED[/green]: Strong Bullish Structure. Prioritizing 'Trend Continuation' setups.")
            
            # 2. Mean Reversion logic
            if wr_val < 0.15 or cci_val < 0.2:
                logic_narrative.append("📉 [cyan]VALUE ZONE[/cyan]: Williams %R & CCI show exhaustion. 'Mean Reversion' category is [bold]ACTIVE[/bold]. Looking for a floor.")
            elif wr_val > 0.85 or cci_val > 0.8:
                logic_narrative.append("🔥 [red]HEAT ZONE[/red]: Indicators at mathematical ceiling. High risk of correction. 'Momentum' category is [dim]CAUTIOUS[/dim].")

            # 3. Execution logic
            if data.get('f_pullback', 0) > 0.7:
                logic_narrative.append("🎯 [green]OPTIMAL ENTRY[/green]: Pullback depth is significant. Entry quality is currently [bold]PREMIUM[/bold].")

            if not logic_narrative:
                logic_narrative.append("⚖️ [dim]NEUTRAL[/dim]: No extreme signals. System is in 'Scanning' mode, waiting for confluence.")

            # Create the Layout
            from rich.layout import Layout
            from rich.text import Text
            
            logic_text = Text.from_markup("\n".join(logic_narrative))
            
            live.update(
                Panel(
                    renderable=table,
                    title="[bold blue]TITAN AI RADAR v2.0[/bold blue]",
                    subtitle="Institutional Confluence Engine"
                )
            )
            
            # Since Live.update takes one renderable, we group them
            from rich.console import Group
            display_group = Group(
                table,
                Panel(logic_text, title="🧠 Institutional Reasoning (Real-time)", border_style="cyan")
            )
            live.update(display_group)
            
            time.sleep(2)
            
    console.print("\n[bold green]✅ Radar Demo Complete.[/bold green]")

if __name__ == "__main__":
    if USE_RICH:
        display_radar()
    else:
        print("Rich not found, using standard output...")
        for _ in range(3):
            data = get_radar_data()
            if data:
                print(f"\n--- AI RADAR: {datetime.now()} ---")
                for k, v in data.items():
                    if k.startswith("f_"):
                        print(f"{k:12}: {v:.4f}")
            time.sleep(3)
