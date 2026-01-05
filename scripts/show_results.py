"""Quick results analysis"""
import pandas as pd
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()

df = pd.read_csv('strategy_research_results_20260106_000325.csv')

console.print("\n[bold cyan]STRATEGY RESEARCH LAB - RESULTS SUMMARY[/bold cyan]\n")
console.print(f"Total backtests: {len(df)}")

# Filter significant results
sig = df[(df['p_value'] < 0.05) & (df['total_trades'] >= 10)]
console.print(f"Statistically significant (p<0.05): {len(sig)}\n")

# Top 15 by Sharpe
top = sig.nlargest(15, 'sharpe_ratio')

table = Table(title="Top 15 Strategies by Sharpe Ratio", box=box.ROUNDED)
table.add_column("Strategy", style="yellow")
table.add_column("Symbol", style="magenta")
table.add_column("TF", style="blue")
table.add_column("Sharpe", justify="right", style="green")
table.add_column("Win%", justify="right")
table.add_column("Trades", justify="right")
table.add_column("Return%", justify="right")

for _, row in top.iterrows():
    sharpe_color = "green" if row['sharpe_ratio'] > 0 else "red"
    return_color = "green" if row['total_return_pct'] > 0 else "red"
    
    table.add_row(
        row['strategy'],
        row['symbol'],
        row['timeframe'],
        f"[{sharpe_color}]{row['sharpe_ratio']:.2f}[/{sharpe_color}]",
        f"{row['win_rate']*100:.1f}%",
        f"{int(row['total_trades'])}",
        f"[{return_color}]{row['total_return_pct']:+.1f}%[/{return_color}]"
    )

console.print(table)
console.print()

# Summary stats
positive_sharpe = sig[sig['sharpe_ratio'] > 0]
console.print(f"[bold]Strategies with positive Sharpe: {len(positive_sharpe)}/{len(sig)} ({len(positive_sharpe)/len(sig)*100:.0f}%)[/bold]")
console.print(f"Average Sharpe (all): {sig['sharpe_ratio'].mean():.2f}")
console.print(f"Best Sharpe: {sig['sharpe_ratio'].max():.2f}")
console.print(f"Average Win Rate: {sig['win_rate'].mean()*100:.1f}%")
console.print(f"Average Return: {sig['total_return_pct'].mean():.1f}%")
