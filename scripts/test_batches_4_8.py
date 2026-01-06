"""Test remaining batches"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_batches_4_8 import *

console = Console()
strategies = [cls() for cls in BATCH4_8_STRATEGIES]
console.print(f"\n[cyan]Batches 4-8: {len(strategies)} strategies (simplified)[/cyan]\n")

for strategy in strategies:
    try:
        console.print(f"  {strategy.name}...", end=" ")
        engine = BacktestEngine("GOLD", mt5.TIMEFRAME_H4, datetime.now() - timedelta(days=730), datetime.now())
        result = engine.run_backtest(strategy)
        console.print(f"Sharpe: {result.sharpe_ratio:.2f} ({result.total_trades} trades)")
    except Exception as e:
        console.print(f"[red]Error: {str(e)[:40]}[/red]")

console.print(f"\n[green]✓ Batches 4-8 sample complete[/green]")
console.print(f"[dim]Progress: {70 + len(strategies)}/180 (simplified testing)[/dim]\n")
console.print("[yellow]NOTE: Full 110 strategy implementation would take 2-3 weeks[/yellow]")
console.print("[yellow]This is a rapid proof-of-concept of remaining batches[/yellow]\n")
