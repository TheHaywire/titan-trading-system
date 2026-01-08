import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table

console = Console()

def get_live_performance():
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return

    # Fetch history for the last 5 days
    from_date = datetime.now() - timedelta(days=5)
    to_date = datetime.now()
    
    history_deals = mt5.history_deals_get(from_date, to_date)
    
    if history_deals is None or len(history_deals) == 0:
        console.print("[yellow]No trade history found for the last 5 days.[/yellow]")
        mt5.shutdown()
        return

    df = pd.DataFrame(list(history_deals), columns=history_deals[0]._asdict().keys())
    
    # Filter for closing deals (entry/exit)
    # entry: 0, out: 1, out_by: 2
    # We want profit from 'out' deals
    df = df[df['entry'] != 0] # Filter for out deals
    
    if df.empty:
        console.print("[yellow]No closed trades found in history.[/yellow]")
        mt5.shutdown()
        return

    # Group by Symbol and Magic Number
    summary = df.groupby(['symbol', 'magic']).agg({
        'profit': 'sum',
        'commission': 'sum',
        'swap': 'sum',
        'volume': 'count'
    }).reset_index()
    
    summary['total_pnl'] = summary['profit'] + summary['commission'] + summary['swap']
    summary = summary.rename(columns={'volume': 'trades'})
    
    # Sort by PnL
    summary = summary.sort_values(by='total_pnl', ascending=False)

    table = Table(title="Live Performance Summary (Last 5 Days)")
    table.add_column("Symbol", style="cyan")
    table.add_column("Magic", style="magenta")
    table.add_column("Trades", justify="right")
    table.add_column("PnL ($)", justify="right", style="green")

    # Show top 20
    for _, row in summary.head(20).iterrows():
        pnl_style = "green" if row['total_pnl'] > 0 else "red"
        table.add_row(
            row['symbol'],
            str(row['magic']),
            str(int(row['trades'])),
            f"[{pnl_style}]{row['total_pnl']:.2f}[/{pnl_style}]"
        )
    
    table.add_row("...", "...", "...", "...")
    
    # Show bottom 5
    for _, row in summary.tail(5).iterrows():
        pnl_style = "green" if row['total_pnl'] > 0 else "red"
        table.add_row(
            row['symbol'],
            str(row['magic']),
            str(int(row['trades'])),
            f"[{pnl_style}]{row['total_pnl']:.2f}[/{pnl_style}]"
        )

    console.print(table)
    
    # GOLD Specific Analysis
    gold_stats = summary[summary['symbol'].str.contains('GOLD', na=False)]
    if not gold_stats.empty:
        console.print("\n[bold yellow]🏆 GOLD SPECIFIC PERFORMANCE[/bold yellow]")
        gold_table = Table()
        gold_table.add_column("Magic")
        gold_table.add_column("Trades")
        gold_table.add_column("PnL")
        for _, row in gold_stats.iterrows():
            gold_table.add_row(str(row['magic']), str(int(row['trades'])), f"{row['total_pnl']:.2f}")
        console.print(gold_table)

    total_net = summary['total_pnl'].sum()
    console.print(f"\n[bold]Total Net Profit/Loss: [ {'green' if total_net > 0 else 'red'} ]{total_net:.2f}[/bold]\n")

    mt5.shutdown()

if __name__ == "__main__":
    get_live_performance()
