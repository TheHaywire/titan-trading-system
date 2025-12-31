
import os
import sys
import time
import pandas as pd
import polars as pl
import MetaTrader5 as mt5
from datetime import datetime
from rich.console import Console, Group
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

# Ensure Project Root is in Path
sys.path.append(os.getcwd())

from titan_system.backtest.indicators import (
    compute_rsi, compute_cci, compute_williams_r, 
    compute_stoch, compute_adx
)

def analyze_strategy_categories(symbol="XAUUSD"):
    if not mt5.initialize():
        return None
    
    # Fetch Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)
    if rates is None: rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M15, 0, 300)
    if rates is None: return None
    
    df = pl.from_pandas(pd.DataFrame(rates))
    
    # Run all computations in a single select for maximum speed
    results = df.select([
        pl.col("close").rolling_mean(50).alias("sma_50"),
        pl.col("close").rolling_mean(200).alias("sma_200"),
        compute_adx(pl.col("high"), pl.col("low"), pl.col("close")).alias("adx"),
        compute_cci(pl.col("high"), pl.col("low"), pl.col("close")).alias("cci"),
        compute_williams_r(pl.col("high"), pl.col("low"), pl.col("close")).alias("wr"),
        compute_rsi(pl.col("close")).alias("rsi"),
        (pl.col("high") - pl.col("low")).rolling_mean(14).alias("tr_avg"),
        (pl.col("high") - pl.col("low")).alias("tr_curr")
    ]).tail(1).to_dicts()[0]

    close_val = df['close'][-1]
    trend_str = "BULLISH" if results['sma_50'] > results['sma_200'] else "BEARISH"
    trend_power = "STRONG" if results['adx'] > 25 else "WEAK/CHOP"
    vol_status = "EXPANDING" if results['tr_curr'] > results['tr_avg'] else "CONTRACTING"

    return {
        "symbol": symbol,
        "price": close_val,
        "categories": {
            "Trend Following": f"{trend_str} ({trend_power})",
            "Mean Reversion": f"CCI: {results['cci']:.0f} | W%R: {results['wr']:.0f}",
            "Momentum": f"RSI: {results['rsi']:.1f}",
            "Volatility": vol_status,
            "Breakout": "SQUEEZE" if vol_status == "CONTRACTING" and results['adx'] < 20 else "N/A"
        },
        "indicators": results
    }

def run_dashboard():
    console = Console()
    with Live(console=console, refresh_per_second=1) as live:
        while True:
            data = analyze_strategy_categories()
            if not data:
                live.update(Panel("Waiting for MT5 Data...", title="[red]Error"))
                time.sleep(2)
                continue
            
            table = Table(title=f"TITAN LIVE STRATEGY ANALYZER: {data['symbol']}")
            table.add_column("Category", style="cyan")
            table.add_column("Current Status", style="bold white")
            table.add_column("Institutional Meaning", style="dim")

            # MAPPING REAL-TIME DATA TO MEANING
            cats = data['categories']
            inds = data['indicators']
            
            # Trend Meaning
            trend_meaning = "Market is in trend discovery mode."
            if "STRONG" in cats['Trend Following']:
                trend_meaning = "Institutional money is aggressive. Prioritize Trend Followers."
            else:
                trend_meaning = "No trend edge. Suppressing trend entries to avoid chop."
                
            # Mean Reversion Meaning
            mr_meaning = "Price is within fair value."
            if inds['cci'] > 200 or inds['wr'] > -10:
                mr_meaning = "🎯 CEILING: Price is mathematically exhausted. Expect reversal."
            elif inds['cci'] < -200 or inds['wr'] < -90:
                mr_meaning = "🛡️ FLOOR: Price is deeply undervalued. Looking for Buy triggers."

            # Breakout Meaning
            brk_meaning = "Volatility is normal."
            if cats['Breakout'] == "SQUEEZE":
                brk_meaning = "💣 SQUEEZE: Volatility is coiled. Institutional breakout is IMMINENT."

            table.add_row("Trend Following", cats['Trend Following'], trend_meaning)
            table.add_row("Mean Reversion", cats['Mean Reversion'], mr_meaning)
            table.add_row("Momentum", cats['Momentum'], "Measuring the speed of the current move.")
            table.add_row("Volatility", cats['Volatility'], f"Market is currently {cats['Volatility'].lower()}.")
            table.add_row("Breakout Radar", cats['Breakout'], brk_meaning)

            live.update(table)
            time.sleep(2)

if __name__ == "__main__":
    run_dashboard()
