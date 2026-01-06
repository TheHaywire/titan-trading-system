"""Test Professional Batch 3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import track
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_professional_batch3 import *

console = Console()
strategies = [cls() for cls in PROFESSIONAL_BATCH3]

console.print(f"\n[bold cyan]PROFESSIONAL BATCH 3: {len(strategies)} strategies[/bold cyan]")
console.print(f"[bold yellow]Complete implementations - volatility, macro, ML, hybrids[/bold yellow]\n")

results_table = Table(title="Batch 3 Results")
results_table.add_column("Strategy", style="cyan")
results_table.add_column("Trades", justify="right")
results_table.add_column("Sharpe", justify="right", style="yellow")
results_table.add_column("Return", justify="right")
results_table.add_column("Status", style="green")

validated = []
promising = []
tested_count = 0

for strategy in track(strategies, description="Testing professionally..."):
    try:
        engine = BacktestEngine("GOLD", mt5.TIMEFRAME_H4, 
                              datetime.now() - timedelta(days=730), 
                              datetime.now())
        result = engine.run_backtest(strategy)
        tested_count += 1
        
        status = "❌"
        # Full validation criteria
        if (result.p_value < 0.05 and result.total_trades >= 30 and 
            result.sharpe_ratio >= 1.0 and result.win_rate >= 0.35 and 
            result.max_drawdown_pct <=  25):
            validated.append(result)
            status = "✅ VALIDATED"
            console.print(f"[green]✅ {strategy.name}: Sharpe {result.sharpe_ratio:.2f} VALIDATED![/green]")
        elif result.sharpe_ratio > 1.5 and result.total_trades >= 20:
            promising.append(result)
            status = "⭐ Promising"
        
        results_table.add_row(
            strategy.name,
            str(result.total_trades),
            f"{result.sharpe_ratio:.2f}",
            f"+{result.total_return_pct:.1f}%",
            status
        )
        
    except Exception as e:
        console.print(f"[red]{strategy.name}: ERROR - {str(e)[:50]}[/red]")
        results_table.add_row(strategy.name, "0", "N/A", "N/A", "❌ Error")

console.print("\n")
console.print(results_table)

console.print(f"\n[bold]BATCH 3 SUMMARY:[/bold]")
console.print(f"Tested: {tested_count}/{len(strategies)}")
console.print(f"Validated: {len(validated)}")
console.print(f"Promising: {len(promising)}")

if validated:
    console.print(f"\n[bold green]NEW VALIDATED CHAMPIONS:[/bold green]")
    for r in sorted(validated, key=lambda x: x.sharpe_ratio, reverse=True):
        console.print(f"  🏆 {r.strategy_name}: Sharpe {r.sharpe_ratio:.2f}, {r.total_trades} trades")

if promising:
    console.print(f"\n[bold yellow]PROMISING CANDIDATES:[/bold yellow]")
    for r in sorted(promising, key=lambda x: x.sharpe_ratio, reverse=True):
        console.print(f"  ⭐ {r.strategy_name}: Sharpe {r.sharpe_ratio:.2f}, {r.total_trades} trades")
