"""Quick Batch 2 Test"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_indicators_batch2 import *

console = Console()
symbol = "GOLD"
timeframes = [(mt5.TIMEFRAME_H4, "H4")]
days_back = 730
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

strategies = [cls() for cls in BATCH2_STRATEGIES]
console.print(f"\n[cyan]Batch 2: {len(strategies)} strategies[/cyan]\n")

for strategy in strategies:
    try:
        console.print(f"  {strategy.name}...", end=" ")
        engine = BacktestEngine(symbol, mt5.TIMEFRAME_H4, start_date, end_date)
        result = engine.run_backtest(strategy)
        console.print(f"Sharpe: {result.sharpe_ratio:.2f} ({result.total_trades} trades)")
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")

console.print("\n[green]✓ Batch 2 complete[/green]")
console.print(f"[dim]Total tested: {56 + len(strategies)}/180[/dim]\n")
