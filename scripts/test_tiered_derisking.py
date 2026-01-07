import sys
import os
import MetaTrader5 as mt5
from datetime import datetime, timedelta
sys.path.append(os.getcwd())

import pandas as pd
import numpy as np
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_remaining import RSI_Divergence_MACD_Strategy
from titan_system.backtest.managed_strategy import ManagedStrategy
from rich.console import Console
from rich.table import Table

console = Console()

def run_comparison(symbol="GOLD", timeframe_str="H4"):
    # Map timeframe string to MT5 constant
    tf_map = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1
    }
    timeframe = tf_map.get(timeframe_str, mt5.TIMEFRAME_H4)
    
    console.print(f"[bold cyan]🚀 RUNNING TIERED DE-RISKING COMPARISON FOR {symbol} ({timeframe_str})[/bold cyan]")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=60) # Increased to 60 days for more trades
    
    engine = BacktestEngine(symbol=symbol, timeframe=timeframe, start_date=start_date, end_date=end_date)
    
    # 1. Baseline Strategy
    baseline_strat = RSI_Divergence_MACD_Strategy()
    console.print(f"Running Baseline: {baseline_strat.name}...")
    baseline_result = engine.run_backtest(baseline_strat)
    
    # 2. Managed Strategy
    managed_strat = ManagedStrategy(RSI_Divergence_MACD_Strategy())
    console.print(f"Running Managed: {managed_strat.name}...")
    managed_result = engine.run_backtest(managed_strat)
    
    # --- DISPLAY RESULTS ---
    table = Table(title=f"Tiered De-Risking Impact: {symbol} {timeframe}")
    table.add_column("Metric", style="cyan")
    table.add_column("Baseline", style="white")
    table.add_column("Managed", style="green")
    table.add_column("Improvement", style="bold yellow")
    
    def get_improvement(val_b, val_m, higher_is_better=True):
        if val_b == 0: return "N/A"
        imp = ((val_m - val_b) / abs(val_b)) * 100
        if not higher_is_better: imp = -imp
        color = "green" if imp > 0 else "red"
        return f"[{color}]{imp:+.1f}%[/{color}]"

    table.add_row("Total Trades", str(baseline_result.total_trades), str(managed_result.total_trades), "")
    table.add_row("Win Rate", f"{baseline_result.win_rate:.1f}%", f"{managed_result.win_rate:.1f}%", get_improvement(baseline_result.win_rate, managed_result.win_rate))
    table.add_row("Return %", f"{baseline_result.total_return_pct:.1f}%", f"{managed_result.total_return_pct:.1f}%", get_improvement(baseline_result.total_return_pct, managed_result.total_return_pct))
    table.add_row("Sharpe", f"{baseline_result.sharpe_ratio:.2f}", f"{managed_result.sharpe_ratio:.2f}", get_improvement(baseline_result.sharpe_ratio, managed_result.sharpe_ratio))
    table.add_row("Max DD %", f"{baseline_result.max_drawdown_pct:.1f}%", f"{managed_result.max_drawdown_pct:.1f}%", get_improvement(baseline_result.max_drawdown_pct, managed_result.max_drawdown_pct, False))
    table.add_row("Profit Factor", f"{baseline_result.profit_factor:.2f}", f"{managed_result.profit_factor:.2f}", get_improvement(baseline_result.profit_factor, managed_result.profit_factor))

    console.print(table)
    
    # Detailed Analysis of "Heartbreak" prevention
    b_avg_loss = baseline_result.avg_loss
    m_avg_loss = managed_result.avg_loss
    console.print(f"\n[bold]Avg Loss Reduction:[/bold] Baseline: ${b_avg_loss:.2f} -> Managed: ${m_avg_loss:.2f} ({get_improvement(b_avg_loss, m_avg_loss, False)})")

    return {
        "baseline": baseline_result.__dict__,
        "managed": managed_result.__dict__,
        "improvement": {
            "sharpe": get_improvement(baseline_result.sharpe_ratio, managed_result.sharpe_ratio),
            "max_dd": get_improvement(baseline_result.max_drawdown_pct, managed_result.max_drawdown_pct, False)
        }
    }

if __name__ == "__main__":
    import json
    results = {}
    results["GOLD"] = run_comparison("GOLD", "H4")
    results["USDCAD"] = run_comparison("USDCAD", "H4")
    
    with open("backtest_comparison.json", "w") as f:
        # Filter out non-serializable objects (trades, equity_curve)
        for asset in results:
            for k in ["baseline", "managed"]:
                results[asset][k].pop("trades", None)
                results[asset][k].pop("equity_curve", None)
        json.dump(results, f, indent=4)
    console.print(f"\n[bold green]✅ Results saved to backtest_comparison.json[/bold green]")
