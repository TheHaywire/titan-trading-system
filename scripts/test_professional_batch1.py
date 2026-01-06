"""Test Professional Batch 1"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import track
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_professional_batch1 import *

console = Console()
strategies = [cls() for cls in PROFESSIONAL_STRATEGIES]

console.print(f"\n[bold cyan]PROFESSIONAL BATCH 1: {len(strategies)} strategies[/bold cyan]")
console.print(f"[bold yellow]FULL implementations - NO placeholders![/bold yellow]\n")

validated = []
promising = []

for strategy in track(strategies, description="Testing professionally..."):
    try:
        engine = BacktestEngine("GOLD", mt5.TIMEFRAME_H4, 
                              datetime.now() - timedelta(days=730), 
                              datetime.now())
        result = engine.run_backtest(strategy)
        
        # Full validation
        if (result.p_value < 0.05 and result.total_trades >= 30 and 
            result.sharpe_ratio >= 1.0 and result.win_rate >= 0.35 and 
            result.max_drawdown_pct <= 25):
            validated.append(result)
            console.print(f"[green]✅ {strategy.name}: Sharpe {result.sharpe_ratio:.2f} VALIDATED![/green]")
        elif result.sharpe_ratio > 1.5 and result.total_trades >= 20:
            promising.append(result)
            console.print(f"[yellow]⭐ {strategy.name}: Sharpe {result.sharpe_ratio:.2f} ({result.total_trades} trades)[/yellow]")
        
    except Exception as e:
        console.print(f"[red]{strategy.name}: {str(e)}[/red]")

console.print(f"\n[bold]RESULTS:[/bold]")
console.print(f"Tested: {len(strategies)}")
console.print(f"Validated: {len(validated)}")
console.print(f"Promising: {len(promising)}")

if validated:
    console.print(f"\n[bold green]VALIDATED:[/bold green]")
    for r in sorted(validated, key=lambda x: x.sharpe_ratio, reverse=True):
        console.print(f"  🏆 {r.strategy_name}: Sharpe {r.sharpe_ratio:.2f}")
