"""
FULL VALIDATION - Strong Candidates
====================================
Professional 5-step validation for Statistical Momentum & OBV
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_batches_4_8 import StatisticalMomentum_Strategy
from titan_system.backtest.strategies_volume import OnBalanceVolume_Strategy

console = Console()

# Test setup
symbol = "GOLD"
days_back = 730
end_date = datetime.now()
start_date = end_date - timedelta(days=days_back)

# Strategies to validate
strategies = [
    StatisticalMomentum_Strategy(),
    OnBalanceVolume_Strategy()
]

console.print(Panel.fit(
    "[bold yellow]PROFESSIONAL VALIDATION[/bold yellow]\n"
    "Applying 5-step critic filter:\n"
    "1. p-value < 0.05 ✓\n"
    "2. Trades >= 30 ✓\n"
    "3. Sharpe >= 1.0 ✓\n"
    "4. Win Rate >= 35% ✓\n"
    "5. Max DD <= 25% ✓",
    border_style="yellow"
))

console.print("\n[cyan]Testing on GOLD H4 (24 months)[/cyan]\n")

results = []
for strategy in strategies:
    try:
        console.print(f"[yellow]Validating {strategy.name}...[/yellow]")
        engine = BacktestEngine(symbol, mt5.TIMEFRAME_H4, start_date, end_date)
        result = engine.run_backtest(strategy)
        results.append(result)
        
        console.print(f"  Sharpe: {result.sharpe_ratio:.2f}")
        console.print(f"  Trades: {result.total_trades}")
        console.print(f"  Win Rate: {result.win_rate*100:.1f}%")
        console.print(f"  Max DD: {result.max_drawdown_pct:.1f}%")
        console.print(f"  p-value: {result.p_value:.4f}")
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]\n")

# Apply validation
console.print("\n[bold]VALIDATION RESULTS:[/bold]\n")

validated = []
for r in results:
    passes = True
    reasons = []
    
    # Check 1: p-value
    if r.p_value >= 0.05:
        passes = False
        reasons.append(f"p-value {r.p_value:.4f} >= 0.05")
    
    # Check 2: Sample size
    if r.total_trades < 30:
        passes = False
        reasons.append(f"Only {r.total_trades} trades < 30 minimum")
    
    # Check 3: Sharpe
    if r.sharpe_ratio < 1.0:
        passes = False
        reasons.append(f"Sharpe {r.sharpe_ratio:.2f} < 1.0")
    
    # Check 4: Win rate
    if r.win_rate < 0.35:
        passes = False
        reasons.append(f"Win rate {r.win_rate*100:.1f}% < 35%")
    
    # Check 5: Drawdown
    if r.max_drawdown_pct > 25:
        passes = False
        reasons.append(f"Max DD {r.max_drawdown_pct:.1f}% > 25%")
    
    if passes:
        validated.append(r)
        console.print(f"[bold green]✅ {r.strategy_name} VALIDATED![/bold green]")
        console.print(f"  All 5 criteria passed")
        console.print(f"  Sharpe: {r.sharpe_ratio:.2f} | Trades: {r.total_trades} | Win: {r.win_rate*100:.1f}%")
        console.print(f"  Return: +{r.total_return_pct:.1f}% | DD: {r.max_drawdown_pct:.1f}%\n")
    else:
        console.print(f"[yellow]⚠️  {r.strategy_name} - FAILED VALIDATION[/yellow]")
        for reason in reasons:
            console.print(f"  ❌ {reason}")
        console.print()

# Summary
console.print(Panel.fit(
    f"[bold]VALIDATION SUMMARY[/bold]\n"
    f"Tested: {len(results)}\n"
    f"Validated: {len(validated)}\n"
    f"Failed: {len(results) - len(validated)}",
    border_style="green" if len(validated) > 0 else "red"
))

if len(validated) > 0:
    console.print("\n[bold green]NEW VALIDATED CHAMPIONS:[/bold green]")
    for r in validated:
        console.print(f"  🏆 {r.strategy_name}")
        console.print(f"     Sharpe: {r.sharpe_ratio:.2f} | Return: +{r.total_return_pct:.1f}%")

console.print("\n[dim]Proceeding to test remaining strategies...[/dim]\n")
