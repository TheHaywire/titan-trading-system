import MetaTrader5 as mt5
import pandas as pd
import sqlite3
import os
from rich.console import Console
from rich.table import Table

console = Console()

def run_audit():
    console.print("[bold cyan]Titan Trading System - Absolute Truth Audit[/bold cyan]")
    
    # 1. MT5 Position Audit
    if not mt5.initialize():
        console.print("[red]Failed to initialize MT5[/red]")
        return

    positions = mt5.positions_get()
    mt5.shutdown()
    
    pos_table = Table(title="Live MT5 Positions")
    pos_table.add_column("Ticket", style="dim")
    pos_table.add_column("Symbol")
    pos_table.add_column("Type")
    pos_table.add_column("Magic", style="bold yellow")
    pos_table.add_column("Profit", justify="right")
    pos_table.add_column("Source", style="italic")

    bot_pos_count = 0
    if positions:
        for p in positions:
            p_dict = p._asdict()
            source = "BOT (Alpha/Mission)" if p_dict['magic'] == 888888 else "MANUAL / LEGACY"
            if p_dict['magic'] == 888888: bot_pos_count += 1
            
            pos_table.add_row(
                str(p_dict['ticket']),
                p_dict['symbol'],
                "BUY" if p_dict['type'] == 0 else "SELL",
                str(p_dict['magic']),
                f"${p_dict['profit']:,.2f}",
                source
            )
    else:
        pos_table.add_row("None", "", "", "", "", "")
    
    console.print(pos_table)
    
    # 2. Database Decision Audit
    db_path = "data/titan.db"
    if os.path.exists(db_path):
        try:
            conn = sqlite3.connect(db_path)
            df = pd.read_sql_query("SELECT timestamp, symbol, decision, strategy, score FROM signal_decisions ORDER BY id DESC LIMIT 10", conn)
            conn.close()
            
            dec_table = Table(title="Recent Bot Decisions (Persistent Ledger)")
            dec_table.add_column("Time")
            dec_table.add_column("Symbol")
            dec_table.add_column("Decision")
            dec_table.add_column("Strategy")
            dec_table.add_column("Score")
            
            for _, row in df.iterrows():
                dec_table.add_row(
                    str(row['timestamp']),
                    row['symbol'],
                    row['decision'],
                    str(row['strategy']),
                    f"{row['score']:.1f}"
                )
            console.print(dec_table)
        except Exception as e:
            console.print(f"[red]DB Audit Error: {e}[/red]")
    else:
        console.print("[yellow]No decision database found yet.[/yellow]")

    console.print(f"\n[bold green]Summary: {bot_pos_count} trades managed by Active Bot.[/bold green]")

if __name__ == "__main__":
    run_audit()
