"""
COMPREHENSIVE MULTI-TIMEFRAME TESTING
====================================
Test ALL 125 strategies on M15, H1, H4, D1
Find optimal timeframe for each strategy
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
import pandas as pd

from titan_system.backtest.engine import BacktestEngine

# Import ALL strategy files
from titan_system.backtest.strategies_momentum import *
from titan_system.backtest.strategies_patterns import *
from titan_system.backtest.strategies_momentum_extended import *
from titan_system.backtest.strategies_volume import *
from titan_system.backtest.strategies_batches_4_8 import *
from titan_system.backtest.strategies_remaining import *
from titan_system.backtest.strategies_final_batch import *
from titan_system.backtest.strategies_professional_batch1 import *
from titan_system.backtest.strategies_professional_batch3 import *
from titan_system.backtest.strategies_professional_batch4 import *
from titan_system.backtest.strategies_professional_batch5 import *

console = Console()

# Collect ALL strategy classes
ALL_STRATEGIES = []

# From each module, collect strategy classes
import inspect

def get_strategies_from_module(module):
    strategies = []
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and hasattr(obj, 'analyze') and name.endswith('_Strategy'):
            try:
                strategies.append(obj())
            except:
                pass
    return strategies

# Get all strategies
console.print("[yellow]Collecting all strategies...[/yellow]")
modules = [
    sys.modules['titan_system.backtest.strategies_momentum'],
    sys.modules['titan_system.backtest.strategies_patterns'],
    sys.modules['titan_system.backtest.strategies_momentum_extended'],
    sys.modules['titan_system.backtest.strategies_volume'],
    sys.modules['titan_system.backtest.strategies_batches_4_8'],
    sys.modules['titan_system.backtest.strategies_remaining'],
    sys.modules['titan_system.backtest.strategies_final_batch'],
    sys.modules['titan_system.backtest.strategies_professional_batch1'],
    sys.modules['titan_system.backtest.strategies_professional_batch3'],
    sys.modules['titan_system.backtest.strategies_professional_batch4'],
    sys.modules['titan_system.backtest.strategies_professional_batch5'],
]

for mod in modules:
    ALL_STRATEGIES.extend(get_strategies_from_module(mod))

console.print(f"[green]Found {len(ALL_STRATEGIES)} strategies[/green]\n")

# Timeframes to test
TIMEFRAMES = {
    'M15': mt5.TIMEFRAME_M15,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
}

# Results storage
all_results = []

# Test each strategy on each timeframe
console.print(f"[bold cyan]COMPREHENSIVE MULTI-TIMEFRAME TESTING[/bold cyan]")
console.print(f"[yellow]Testing {len(ALL_STRATEGIES)} strategies × 4 timeframes = {len(ALL_STRATEGIES) * 4} backtests[/yellow]\n")

with Progress() as progress:
    task = progress.add_task(
        f"[cyan]Testing all strategies...", 
        total=len(ALL_STRATEGIES) * len(TIMEFRAMES)
    )
    
    for strategy in ALL_STRATEGIES:
        for tf_name, tf_value in TIMEFRAMES.items():
            try:
                engine = BacktestEngine(
                    "GOLD", 
                    tf_value,
                    datetime.now() - timedelta(days=730),
                    datetime.now()
                )
                result = engine.run_backtest(strategy)
                
                # Store result
                all_results.append({
                    'strategy': strategy.name,
                    'timeframe': tf_name,
                    'sharpe': result.sharpe_ratio,
                    'return': result.total_return_pct,
                    'trades': result.total_trades,
                    'win_rate': result.win_rate * 100,
                    'max_dd': result.max_drawdown_pct,
                    'p_value': result.p_value,
                    'validated': (
                        result.p_value < 0.05 and
                        result.total_trades >= 30 and
                        result.sharpe_ratio >= 1.0 and
                        result.win_rate >= 0.35 and
                        result.max_drawdown_pct <= 25
                    )
                })
                
                # Show if validated
                if all_results[-1]['validated']:
                    console.print(
                        f"[green]✅ {strategy.name} on {tf_name}: "
                        f"Sharpe {result.sharpe_ratio:.2f}[/green]"
                    )
                
            except Exception as e:
                all_results.append({
                    'strategy': strategy.name,
                    'timeframe': tf_name,
                    'sharpe': 0,
                    'return': 0,
                    'trades': 0,
                    'win_rate': 0,
                    'max_dd': 0,
                    'p_value': 1,
                    'validated': False,
                    'error': str(e)[:50]
                })
            
            progress.update(task, advance=1)

# Save to CSV
df = pd.DataFrame(all_results)
df.to_csv('gold_multi_timeframe_results.csv', index=False)
console.print(f"\n[green]Results saved to gold_multi_timeframe_results.csv[/green]")

# Analysis
console.print(f"\n[bold cyan]═══ MULTI-TIMEFRAME ANALYSIS ═══[/bold cyan]\n")

validated = df[df['validated'] == True]
console.print(f"[bold]Total Validated Champions: {len(validated)}[/bold]")

# Best by timeframe
console.print(f"\n[bold yellow]Validated by Timeframe:[/bold yellow]")
for tf in ['M15', 'H1', 'H4', 'D1']:
    tf_validated = validated[validated['timeframe'] == tf]
    console.print(f"  {tf}: {len(tf_validated)} strategies")

# Top 20 overall
console.print(f"\n[bold green]TOP 20 STRATEGIES (Any Timeframe):[/bold green]")
top20 = validated.nlargest(20, 'sharpe')

table = Table(title="Top 20 Champions")
table.add_column("Rank", style="cyan")
table.add_column("Strategy", style="yellow")
table.add_column("TF", style="magenta")
table.add_column("Sharpe", justify="right", style="green")
table.add_column("Trades", justify="right")

for idx, row in top20.iterrows():
    table.add_row(
        str(len(table.rows) + 1),
        row['strategy'][:40],
        row['timeframe'],
        f"{row['sharpe']:.2f}",
        str(int(row['trades']))
    )

console.print(table)

# Best timeframe per strategy
console.print(f"\n[bold]Finding optimal timeframe per strategy...[/bold]")
best_per_strategy = df.loc[df.groupby('strategy')['sharpe'].idxmax()]
best_validated = best_per_strategy[best_per_strategy['validated'] == True]

console.print(f"\n[bold green]Strategies with validated timeframe: {len(best_validated)}[/bold green]")

console.print(f"\n[bold cyan]Complete results in: gold_multi_timeframe_results.csv[/bold cyan]")
