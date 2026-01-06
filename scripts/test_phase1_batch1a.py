"""
COMPREHENSIVE GOLD TEST - PHASE 1
==================================
Testing Pattern Recognition Strategies (Batch 1A: Candlestick Patterns)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_patterns import *

console = Console()

# Configuration
symbol = "GOLD"
timeframes = [
    (mt5.TIMEFRAME_H1, "H1"),
    (mt5.TIMEFRAME_H4, "H4"),
    (mt5.TIMEFRAME_D1, "D1")
]
days_back = 730  # 2 years
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

# Strategies (5 implemented so far)
strategies = [
    HammerShootingStar_Strategy(),
    Engulfing_Strategy(),
    DojiReversal_Strategy(),
    MorningEveningStar_Strategy(),
    ThreeSoldiers_Strategy()
]

console.print(Panel.fit(
    f"[bold]📈 PHASE 1: Candlestick Patterns on GOLD[/bold]\n"
    f"Strategies: {len(strategies)} (Batch 1A)\n"
    f"Timeframes: {len(timeframes)}\n"
    f"Total tests: {len(strategies) * len(timeframes)}\n"
    f"Period: 24 months",
    border_style="cyan"
))

results = []

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    console=console
) as progress:
    
    task = progress.add_task("[cyan]Testing patterns...", total=len(strategies) * len(timeframes))
    
    for tf, tf_name in timeframes:
        for strategy in strategies:
            try:
                progress.update(task, description=f"[cyan]{strategy.name} {tf_name}...")
                
                engine = BacktestEngine(symbol, tf, start_date, end_date)
                result = engine.run_backtest(strategy)
                results.append(result)
                
            except Exception as e:
                console.print(f"[red]Error: {strategy.name}: {str(e)}[/red]")
            
            progress.advance(task)

console.print("\n[green]✓ Batch 1A Complete![/green]\n")

# Apply critic validation
validated = [r for r in results if 
             r.p_value < 0.05 and 
             r.total_trades >= 30 and 
             r.sharpe_ratio >= 1.0 and
             r.win_rate >= 0.35 and
             r.max_drawdown_pct <= 25]

console.print(Panel.fit(
    f"[bold]RESULTS - Batch 1A[/bold]\n"
    f"Total tests: {len(results)}\n"
    f"Validated: {len(validated)}",
    border_style="green" if len(validated) > 0 else "yellow"
))

# Show top 5
top = sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)[:5]

table = Table(title="Top 5 Candlestick Patterns")
table.add_column("Strategy", style="yellow")
table.add_column("TF", style="blue")
table.add_column("Sharpe", justify="right")
table.add_column("Trades", justify="right")
table.add_column("Win%", justify="right")

for r in top:
    sharpe_color = "green" if r.sharpe_ratio > 0 else "red"
    table.add_row(
        r.strategy_name,
        r.timeframe,
        f"[{sharpe_color}]{r.sharpe_ratio:.2f}[/{sharpe_color}]",
        str(r.total_trades),
        f"{r.win_rate*100:.1f}%"
    )

console.print(table)

if len(validated) > 0:
    console.print("\n[bold green]✅ NEW WINNERS FOUND![/bold green]\n")
    for r in validated:
        console.print(f"  {r.strategy_name} ({r.timeframe})")
        console.print(f"    Sharpe: {r.sharpe_ratio:.2f} | Trades: {r.total_trades} | Win: {r.win_rate*100:.1f}%\n")
else:
    console.print("\n[yellow]⚠️  No patterns passed validation in Batch 1A[/yellow]")
    console.print("[dim]Continuing to Batch 1B (Chart Patterns)...[/dim]\n")

# Export results
import pandas as pd
data = []
for r in results:
    data.append({
        'phase': 'Phase1_Batch1A',
        'strategy': r.strategy_name,
        'timeframe': r.timeframe,
        'sharpe': r.sharpe_ratio,
        'trades': r.total_trades,
        'win_rate': r.win_rate,
        'return_pct': r.total_return_pct,
        'max_dd': r.max_drawdown_pct,
        'p_value': r.p_value
    })

df = pd.DataFrame(data)
df.to_csv(f"phase1_batch1a_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)

console.print(f"[green]✓ Results exported[/green]\n")
console.print(f"[bold]Progress: Batch 1A/8 complete[/bold]")
console.print(f"[dim]Remaining: Batch 1B + Phases 2-8[/dim]")
