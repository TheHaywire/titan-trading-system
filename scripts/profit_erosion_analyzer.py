import sqlite3
import pandas as pd
import MetaTrader5 as mt5
import sys
import os
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

# Path Hack
sys.path.append(os.path.join(os.getcwd()))

console = Console()

def analyze_erosion():
    console.print("[bold cyan]🔍 PROFIT EROSION ANALYSIS[/bold cyan]")
    
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return

    db_path = 'data/titan.db'
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM trades ORDER BY close_time DESC LIMIT 100", conn)
        conn.close()
    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/red]")
        mt5.shutdown()
        return

    if df.empty:
        console.print("[yellow]No trades found to analyze.[/yellow]")
        mt5.shutdown()
        return

    results = []
    
    for _, trade in df.iterrows():
        symbol = trade['symbol']
        ticket = int(trade['ticket'])
        open_time = pd.to_datetime(trade['open_time'])
        close_time = pd.to_datetime(trade['close_time'])
        open_price = float(trade['open_price'])
        close_price = float(trade['close_price'])
        trade_type = trade['type']
        volume = float(trade['volume'])
        final_profit = float(trade['profit'])
        magic = int(trade['magic'])

        # Fetch M1 bars during trade duration
        # We add a small buffer
        bars = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, open_time, close_time)
        
        if bars is None or len(bars) == 0:
            continue
            
        bar_df = pd.DataFrame(bars)
        
        if trade_type in ["BUY", 0]: # MT5 0 is BUY
            mfe_price = bar_df['high'].max()
            # Calculate theoretical max profit
            mfe_profit = (mfe_price - open_price) * volume * 100 # Rough estimate for GOLD
            # More accurate: use MT5's calc but for simplicity we use price delta
        else:
            mfe_price = bar_df['low'].min()
            mfe_profit = (open_price - mfe_price) * volume * 100
            
        erosion = mfe_profit - final_profit
        
        results.append({
            'ticket': ticket,
            'symbol': symbol,
            'magic': magic,
            'mfe_profit': mfe_profit,
            'final_profit': final_profit,
            'erosion': erosion,
            'outcome': "PROFIT" if final_profit > 0 else "LOSS"
        })

    report_df = pd.DataFrame(results)
    
    if report_df.empty:
        console.print("[yellow]No bar data found for trades.[/yellow]")
        mt5.shutdown()
        return

    # Filter for trades that were > $100 in profit but ended in LOSS
    heartbreak = report_df[(report_df['mfe_profit'] > 100) & (report_df['outcome'] == "LOSS")]
    
    table = Table(title="Profit Erosion (Top 20 Recent Trades)")
    table.add_column("Ticket", style="cyan")
    table.add_column("Symbol", style="white")
    table.add_column("MFE ($)", style="green")
    table.add_column("Final ($)", style="white")
    table.add_column("Erosion ($)", style="red")
    table.add_column("Outcome", style="bold")
    
    for _, row in report_df.head(20).iterrows():
        outcome_style = "green" if row['outcome'] == "PROFIT" else "red"
        table.add_row(
            str(row['ticket']),
            row['symbol'],
            f"{row['mfe_profit']:.2f}",
            f"{row['final_profit']:.2f}",
            f"{row['erosion']:.2f}",
            f"[{outcome_style}]{row['outcome']}[/{outcome_style}]"
        )
        
    console.print(table)
    
    if not heartbreak.empty:
        console.print(f"\n[bold red]⚠️ FOUND {len(heartbreak)} HEARTBREAK TRADES[/bold red]")
        console.print("These trades reached significant profit but reversed into a loss.")
        
    mt5.shutdown()

if __name__ == "__main__":
    analyze_erosion()
