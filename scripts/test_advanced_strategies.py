"""
GOLD EXPANDED TEST - Testing 5 new advanced strategies
=======================================================
Adding: Ichimoku, VWAP, Pivot Points, Supertrend, RSI+MACD
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel

from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_advanced import *

console = Console()

# Test configuration
symbol = "GOLD"
timeframes = [(mt5.TIMEFRAME_H1, "H1"), (mt5.TIMEFRAME_H4, "H4")]
days_back = 730  # 2 years
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

strategies = [
    Ichimoku_Strategy(),
    VWAP_Strategy(),
    PivotPoints_Strategy(),
    Supertrend_Strategy(),
    RSI_MACD_Confluence()
]

console.print(Panel.fit(
    f"[bold]Testing 5 NEW Strategies on GOLD[/bold]\n"
    f"Strategies: {len(strategies)}\n"
    f"Timeframes: {len(timeframes)}\n"
    f"Total tests: {len(strategies) * len(timeframes)}",
    border_style="green"
))

results = []
for tf, tf_name in timeframes:
    for strategy in strategies:
        try:
            console.print(f"[yellow]Testing {strategy.name} on {symbol} {tf_name}...[/yellow]")
            engine = BacktestEngine(symbol, tf, start_date, end_date)
            result = engine.run_backtest(strategy)
            results.append(result)
        except Exception as e:
            console.print(f"[red]Error: {strategy.name}: {str(e)}[/red]")

console.print("\n[green]✓ Testing complete![/green]\n")

# Show results
validated = [r for r in results if r.p_value < 0.05 and r.total_trades >= 30 and r.sharpe_ratio >= 1.0]

console.print(f"[bold]Results:[/bold]")
console.print(f"Total tests: {len(results)}")
console.print(f"Validated (p<0.05, trades>=30, Sharpe>=1.0): {len(validated)}\n")

if validated:
    console.print("[green]✅ NEW WINNERS FOUND:[/green]\n")
    for r in sorted(validated, key=lambda x: x.sharpe_ratio, reverse=True):
        console.print(f"  {r.strategy_name} ({r.timeframe}): Sharpe {r.sharpe_ratio:.2f}, Trades {r.total_trades}")
else:
    console.print("[yellow]⚠️  No new winners in this batch[/yellow]")
    console.print("[dim]Best performers:[/dim]\n")
    for r in sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)[:3]:
        console.print(f"  {r.strategy_name} ({r.timeframe}): Sharpe {r.sharpe_ratio:.2f}, Trades {r.total_trades}")
