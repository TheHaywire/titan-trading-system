"""
TRADING SYSTEM HEALTH INSPECTOR
===============================
Extracts all metrics, logs, and config for a full system audit.
"""
import sys, os
import json
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, '.')

from titan_system.factory import factory_config as cfg
from titan_system.factory.strategy_registry import StrategyRegistry

def get_health_report():
    registry = StrategyRegistry()
    conn = sqlite3.connect(cfg.STRATEGY_DB)
    
    # 1. Get Active Portfolio Stats
    metrics = registry.get_portfolio_metrics()
    
    report = {
        "portfolio_summary": metrics,
        "strategies": []
    }
    
    # 2. Get Details for Active Strategies (Paper/Live)
    cursor = conn.cursor()
    cursor.execute("SELECT id, genome, status, bt_sharpe, bt_total_trades, live_pnl, live_trades, live_sharpe, live_drawdown FROM strategies WHERE status IN ('paper', 'live')")
    active_rows = cursor.fetchall()
    
    for row in active_rows:
        s_id, genome_json, status, bt_sharpe, bt_trades, live_pnl, live_trades, live_sharpe, live_drawdown = row
        genome = json.loads(genome_json)
        
        # Fetch Trades
        cursor.execute("SELECT symbol, direction, entry_time, exit_time, entry_price, exit_price, sl_price, tp_price, size, pnl, exit_reason FROM strategy_trades WHERE strategy_id = ? ORDER BY entry_time DESC", (s_id,))
        trades = cursor.fetchall()
        
        trade_logs = []
        for t in trades:
            trade_logs.append({
                "symbol": t[0], "dir": t[1], "entry": t[2], "exit": t[3],
                "entry_p": t[4], "exit_p": t[5], "sl": t[6], "tp": t[7],
                "size": t[8], "pnl": t[9], "reason": t[10]
            })
            
        # Calculate Risk Metrics from Trades if available
        pnl_series = [t[9] for t in trades if t[9] is not None]
        
        # Stats
        win_rate = 0
        pf = 0
        avg_r = 0
        if len(pnl_series) > 0:
            wins = [p for p in pnl_series if p > 0]
            losses = [p for p in pnl_series if p < 0]
            win_rate = len(wins) / len(pnl_series) if pnl_series else 0
            pf = abs(sum(wins) / sum(losses)) if losses and sum(losses) != 0 else float('inf')
            
        report["strategies"].append({
            "id": s_id,
            "name": genome.get("name"),
            "status": status,
            "config": {
                "symbols": genome.get("symbols"),
                "tf": genome.get("timeframe"),
                "type": genome.get("type"),
                "risk_per_trade": genome.get("parameters", {}).get("risk_per_trade"),
                "exit_rules": genome.get("exit_rules")
            },
            "backtest": {
                "sharpe": bt_sharpe,
                "trades": bt_trades
            },
            "live": {
                "pnl": live_pnl,
                "trades": live_trades,
                "sharpe": live_sharpe,
                "drawdown": live_drawdown,
                "win_rate": win_rate,
                "profit_factor": pf
            },
            "recent_trades": trade_logs[:10]  # Last 10
        })
        
    conn.close()
    return report

if __name__ == "__main__":
    report = get_health_report()
    print(json.dumps(report, indent=2))
