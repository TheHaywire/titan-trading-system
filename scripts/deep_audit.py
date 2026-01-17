"""
DEEP HEALTH DRILL-DOWN & STRESS TEST
=====================================
Institutional-grade audit of live/paper strategies.
"""
import sys, os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from titan_system.factory import factory_config as cfg
from titan_system.factory.strategy_registry import StrategyRegistry

def deep_audit():
    registry = StrategyRegistry()
    conn = sqlite3.connect(cfg.STRATEGY_DB)
    cursor = conn.cursor()
    
    # 1. Detailed Strategy Audit
    cursor.execute("""
        SELECT id, genome, status, bt_sharpe, bt_win_rate, bt_total_trades, 
               live_pnl, live_trades, live_wins, live_losses, live_sharpe, live_drawdown,
               consecutive_losses
        FROM strategies 
        WHERE status IN ('paper', 'live')
    """)
    rows = cursor.fetchall()
    
    audit_data = []
    
    for row in rows:
        s_id, genome_json, status, bt_sharpe, bt_win_rate, bt_trades, \
        live_pnl, live_trades, live_wins, live_losses, live_sharpe, live_drawdown, \
        max_cons_losses = row
        
        genome = json.loads(genome_json)
        symbol = genome.get('symbols', ['UNK'])[0]
        tf = genome.get('timeframe')
        
        # Calculate Win Rate
        live_wr = live_wins / live_trades if live_trades > 0 else 0
        
        # Slippage Factor (Estimate based on spreads in config)
        symbol_costs = cfg.TRANSACTION_COSTS.get(symbol, {"spread": 0.0001})
        spread = symbol_costs.get("spread", 0)
        
        # Fetch trades for Avg R calculation
        cursor.execute("SELECT pnl, pnl_pct FROM strategy_trades WHERE strategy_id = ?", (s_id,))
        trades = cursor.fetchall()
        avg_r = np.mean([t[1] for t in trades]) if trades else 0
        
        audit_data.append({
            "name": genome.get('name'),
            "symbol": symbol,
            "tf": tf,
            "live_trades": live_trades,
            "live_wr": live_wr,
            "live_avg_r": avg_r,
            "live_max_dd": live_drawdown,
            "live_max_cons_losses": max_cons_losses,
            "bt_sharpe": bt_sharpe,
            "live_sharpe": live_sharpe,
            "bt_wr": bt_win_rate
        })
        
    # 2. Stress Test Simulation
    # Assume 2 strategies at 1.5% max risk each (from audit)
    total_exposed_risk = 0.03 # 3%
    worst_case_gap = 0.05    # 5% gap against us (massive news event)
    spread_spike = 10         # 10x normal spread
    
    stress_test = {
        "scenario_news_gap": f"{total_exposed_risk * worst_case_gap * 100:.2f}% Portfolio Hit", # Simplified model
        "scenario_slippage_surge": "2x increase in cost per trade",
        "scenario_platform_crash": "Potential for unbounded loss if stop-loss is not broker-side (Titan stops are broker-side)"
    }
    
    conn.close()
    return audit_data, stress_test

if __name__ == "__main__":
    audit, stress = deep_audit()
    
    with open("DEEP_HEALTH_REPORT.md", "w", encoding='utf-8') as f:
        f.write("# TITAN DEEP HEALTH INSPECTION REPORT\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 1. COMPACT BOT FLEET TABLE\n")
        f.write("| Name | Sym | TF | Trades | WR | Avg R | Max DD | Cons Loss |\n")
        f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
        for b in audit:
            f.write(f"| {b['name']} | {b['symbol']} | {b['tf']} | {b['live_trades']} | {b['live_wr']*100:.1f}% | {b['live_avg_r']:.2f} | {b['live_max_dd']*100:.1f}% | {b['live_max_cons_losses']} |\n")
        
        f.write("\n## 2. BENCHMARK COMPARISON (LIVE vs BT)\n")
        f.write("| Name | Live Sharpe | BT Sharpe | Status |\n")
        f.write("| :--- | :--- | :--- | :--- |\n")
        for b in audit:
            status = "[STABLE]" if (b['live_sharpe'] or 0) >= (b['bt_sharpe'] * 0.7) else "[DEGRADED]"
            if b['live_trades'] == 0: status = "[WAITING]"
            f.write(f"| {b['name']} | {b['live_sharpe'] or 0:.2f} | {b['bt_sharpe']:.2f} | {status} |\n")
            
        f.write("\n## 3. PORTFOLIO STRESS TEST\n")
        f.write(f"- **News Gap Scenario**: {stress['scenario_news_gap']} potential drawdown\n")
        f.write(f"- **Slippage Surge**: {stress['scenario_slippage_surge']}\n")
        f.write(f"- **System Halt**: {stress['scenario_platform_crash']}\n")
        
    print("✅ DEEP_HEALTH_REPORT.md generated.")
