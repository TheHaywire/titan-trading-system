"""Test remaining batch"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import track
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_remaining import *

console = Console()
strategies = [cls() for cls in REMAINING_STRATEGIES]

console.print(f"\n[bold cyan]Testing {len(strategies)} remaining strategies[/bold cyan]")
console.print(f"[dim](Representative sample of 102 total)[/dim]\n")

validated = []
for strategy in track(strategies, description="Testing..."):
    try:
        engine = BacktestEngine("GOLD", mt5.TIMEFRAME_H4, datetime.now() - timedelta(days=730), datetime.now())
        result = engine.run_backtest(strategy)
        
        # Quick validation check
        if (result.p_value < 0.05 and result.total_trades >= 30 and 
            result.sharpe_ratio >= 1.0 and result.win_rate >= 0.35 and 
            result.max_drawdown_pct <= 25):
            validated.append(result)
            console.print(f"[green]✅ {strategy.name}: Sharpe {result.sharpe_ratio:.2f} VALIDATED![/green]")
        elif result.sharpe_ratio > 2.0:
            console.print(f"[yellow]⭐ {strategy.name}: Sharpe {result.sharpe_ratio:.2f} ({result.total_trades} trades)[/yellow]")
        
    except Exception as e:
        console.print(f"[red]{strategy.name}: Error[/red]")

console.print(f"\n[bold]Results:[/bold]")
console.print(f"Tested: {len(strategies)}")
console.print(f"Validated: {len(validated)}")
console.print(f"\n[dim]Total progress: {78 + len(strategies)}/180[/dim]")

if validated:
    console.print(f"\n[bold green]NEW CHAMPIONS:[/bold green]")
    for r in validated:
        console.print(f"  🏆 {r.strategy_name}: Sharpe {r.sharpe_ratio:.2f}")
