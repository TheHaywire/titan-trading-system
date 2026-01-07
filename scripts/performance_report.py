import sqlite3
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from datetime import datetime, timedelta

console = Console()

def generate_report():
    db_path = 'data/titan.db'
    try:
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM trades", conn)
        conn.close()
    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/red]")
        return

    if df.empty:
        console.print("[yellow]No trades found in database for reporting.[/yellow]")
        return

    # Convert numeric columns
    df['profit'] = pd.to_numeric(df['profit'], errors='coerce')
    df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
    
    # --- 1. OVERALL STATS ---
    total_trades = len(df)
    total_profit = df['profit'].sum()
    win_rate = (len(df[df['profit'] > 0]) / total_trades) * 100 if total_trades > 0 else 0
    avg_profit = df['profit'].mean()
    max_win = df['profit'].max()
    max_loss = df['profit'].min()
    
    overall_table = Table(title="Overall Live Performance (MT5 Sync)", show_header=True, header_style="bold magenta")
    overall_table.add_column("Metric", style="cyan")
    overall_table.add_column("Value", style="white")
    
    overall_table.add_row("Total Trades", str(total_trades))
    overall_table.add_row("Net Profit", f"${total_profit:,.2f}")
    overall_table.add_row("Win Rate", f"{win_rate:.1f}%")
    overall_table.add_row("Avg Trade profit", f"${avg_profit:,.2f}")
    overall_table.add_row("Largest Win", f"${max_win:,.2f}")
    overall_table.add_row("Largest Loss", f"${max_loss:,.2f}")
    
    console.print(overall_table)

    # --- 2. BREAKDOWN BY SYMBOL ---
    symbol_df = df.groupby('symbol').agg(
        Trades=('id', 'count'),
        Profit=('profit', 'sum'),
        Win_Rate=('profit', lambda x: (len(x[x > 0]) / len(x)) * 100 if len(x) > 0 else 0)
    ).sort_values(by='Profit', ascending=False)

    symbol_table = Table(title="Performance by Symbol", show_header=True, header_style="bold blue")
    symbol_table.add_column("Symbol", style="cyan")
    symbol_table.add_column("Trades", style="white")
    symbol_table.add_column("Profit", style="green")
    symbol_table.add_column("Win Rate", style="yellow")

    for symbol, row in symbol_df.iterrows():
        profit_style = "bold green" if row['Profit'] >= 0 else "bold red"
        symbol_table.add_row(
            symbol, 
            str(int(row['Trades'])), 
            f"${row['Profit']:,.2f}", 
            f"{row['Win_Rate']:.1f}%",
            style=profit_style if row['Profit'] < 0 else None
        )
    
    console.print(symbol_table)

    # --- 3. BREAKDOWN BY MAGIC NUMBER (Strategy) ---
    # Magic Number mapping
    magic_map = {
        999001: "GOLD Scalper (M15)",
        888888: "Autonomous Signal Scout",
        777777: "Institutional MTF",
        123456: "USDCAD Champion",
        0: "Manual / Other"
    }
    
    df['strategy'] = df['magic'].map(lambda x: magic_map.get(x, f"Magic {x}"))
    
    strategy_df = df.groupby('strategy').agg(
        Trades=('id', 'count'),
        Profit=('profit', 'sum'),
        Win_Rate=('profit', lambda x: (len(x[x > 0]) / len(x)) * 100 if len(x) > 0 else 0)
    ).sort_values(by='Profit', ascending=False)

    strategy_table = Table(title="Performance by Strategy", show_header=True, header_style="bold green")
    strategy_table.add_column("Strategy", style="cyan")
    strategy_table.add_column("Trades", style="white")
    strategy_table.add_column("Profit", style="green")
    strategy_table.add_column("Win Rate", style="yellow")

    for strategy, row in strategy_df.iterrows():
        profit_style = "bold green" if row['Profit'] >= 0 else "bold red"
        strategy_table.add_row(
            strategy, 
            str(int(row['Trades'])), 
            f"${row['Profit']:,.2f}", 
            f"{row['Win_Rate']:.1f}%"
        )
    
    console.print(strategy_table)

    # --- 4. RECENT ACTIVITY (Last 24h) ---
    df['close_time'] = pd.to_datetime(df['close_time'], errors='coerce')
    last_24h = df[df['close_time'] > datetime.now() - timedelta(days=1)]
    
    if not last_24h.empty:
        p24 = last_24h['profit'].sum()
        console.print(Panel(f"[bold]Last 24h Profit: [cyan]${p24:,.2f}[/cyan][/bold] ({len(last_24h)} trades)", title="Live Pulse"))
    else:
        console.print("[yellow]No trades in last 24h.[/yellow]")

if __name__ == "__main__":
    generate_report()
