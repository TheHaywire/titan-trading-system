"""
💉 ALPHA INJECTOR
================
Moves validated backtest winners into the production Alpha Registry.
"""

import pandas as pd
import json
import os
import logging
from datetime import datetime
from rich.console import Console

console = Console()
REGISTRY_PATH = "config/alpha_registry.json"
RESULTS_PATH = "data/global_alpha_results.csv"

def inject_alphas(min_sharpe=1.5):
    if not os.path.exists(RESULTS_PATH):
        console.print(f"[red]Error: {RESULTS_PATH} not found. Run global_alpha_scanner.py first.[/red]")
        return

    # 1. Load Results
    df = pd.read_csv(RESULTS_PATH)
    
    # 2. Filter for Triple-A
    triple_a = df[df['Sharpe'] >= min_sharpe].copy()
    
    if triple_a.empty:
        console.print("[yellow]No Triple-A Alphas found to inject.[/yellow]")
        return

    # 3. Format for Registry
    new_alphas = []
    for _, row in triple_a.iterrows():
        new_alphas.append({
            "symbol": row['Symbol'],
            "strategy": row['Strategy'],
            "tf": row['TF'],
            "metrics": {
                "sharpe": row['Sharpe'],
                "win_rate": row['WinRate'],
                "return": row['Return']
            },
            "last_validated": datetime.now().strftime("%Y-%m-%d")
        })

    # 4. Update Registry
    registry = {
        "version": "1.0",
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "alphas": new_alphas
    }

    with open(REGISTRY_PATH, 'w') as f:
        json.dump(registry, f, indent=4)

    console.print(f"✅ Successfully injected [bold]{len(new_alphas)}[/bold] Alphas into [bold]{REGISTRY_PATH}[/bold]")
    
    # Display top 5
    console.print("\n🔥 [bold]Top Injected Alphas:[/bold]")
    for a in new_alphas[:5]:
        console.print(f" - {a['symbol']} ({a['strategy']} @ {a['tf']}) | Sharpe: {a['metrics']['sharpe']}")

if __name__ == "__main__":
    inject_alphas()
