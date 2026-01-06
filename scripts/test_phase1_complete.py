"""
COMPLETE PHASE 1 TEST - All 11 Pattern Strategies
==================================================
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_patterns import *

console = Console()

symbol = "GOLD"
timeframes = [(mt5.TIMEFRAME_H1, "H1"), (mt5.TIMEFRAME_H4, "H4"), (mt5.TIMEFRAME_D1, "D1")]
days_back = 730
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

strategies = [cls() for cls in PATTERN_STRATEGIES]

console.print(f"\n[bold cyan]Testing {len(strategies)} Pattern Strategies on GOLD[/bold cyan]\n")

results = []
for tf, tf_name in timeframes:
    for strategy in strategies:
        try:
            console.print(f"  {strategy.name} {tf_name}...", end=" ")
            engine = BacktestEngine(symbol, tf, start_date, end_date)
            result = engine.run_backtest(strategy)
            results.append(result)
            sharpe_color = "green" if result.sharpe_ratio > 0 else "red"
            console.print(f"[{sharpe_color}]Sharpe: {result.sharpe_ratio:.2f}[/{sharpe_color}] ({result.total_trades} trades)")
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")

console.print(f"\n[green]✓ Phase 1 Complete: {len(results)} backtests[/green]")

# Quick summary
validated = [r for r in results if r.p_value < 0.05 and r.total_trades >= 30 and r.sharpe_ratio >= 1.0]
console.print(f"Validated: {len(validated)}")

if validated:
    console.print("\n[bold]Winners:[/bold]")
    for r in sorted(validated, key=lambda x: x.sharpe_ratio, reverse=True):
        console.print(f"  {r.strategy_name} ({r.timeframe}): Sharpe {r.sharpe_ratio:.2f}")

# Export
import pandas as pd
data = [{
    'strategy': r.strategy_name,
    'tf': r.timeframe,
    'sharpe': r.sharpe_ratio,
    'trades': r.total_trades,
    'win_rate': r.win_rate,
    'p_value': r.p_value
} for r in results]
pd.DataFrame(data).to_csv(f"phase1_complete_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)

console.print(f"\n[dim]Continuing to Phase 2...[/dim]\n")
