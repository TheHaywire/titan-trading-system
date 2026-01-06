"""Test Batch 3"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_volume import *

console = Console()
strategies = [cls() for cls in BATCH3_STRATEGIES]
console.print(f"\n[cyan]Batch 3: {len(strategies)} Volume strategies[/cyan]\n")

for strategy in strategies:
    try:
        console.print(f"  {strategy.name}...", end=" ")
        engine = BacktestEngine("GOLD", mt5.TIMEFRAME_H4, datetime.now() - timedelta(days=730), datetime.now())
        result = engine.run_backtest(strategy)
        console.print(f"Sharpe: {result.sharpe_ratio:.2f} ({result.total_trades} trades)")
    except Exception as e:
        console.print(f"[red]Error: {str(e)[:50]}[/red]")

console.print(f"\n[green]✓ Batch 3 complete[/green]")
console.print(f"[dim]Progress: {61 + len(strategies)}/180[/dim]\n")
