"""
PORTFOLIO FLEET DASHBOARD
=========================
A premium real-time overview of the Strategy Factory fleet.
Displays status, performance metrics, and lifecycle stages of all bots.
"""
import sys, os
import time
import json
import sqlite3
from datetime import datetime

# Add project root to path
sys.path.insert(0, '.')

from titan_system.factory import factory_config as cfg
from titan_system.factory.strategy_registry import StrategyRegistry

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def format_currency(value):
    return f"${value:,.2f}"

def get_color_for_status(status):
    colors = {
        "candidate": "\033[94m", # Blue
        "validated": "\033[92m", # Green
        "paper": "\033[93m",     # Yellow
        "live": "\033[91m",      # Red (Danger/Active)
        "retired": "\033[90m"    # Grey
    }
    return colors.get(status, "\033[0m")

def print_dashboard():
    registry = StrategyRegistry()
    metrics = registry.get_portfolio_metrics()
    
    clear_screen()
    print("\033[1m" + "=" * 80)
    print(f" TITAN STRATEGY FACTORY | FLEET DASHBOARD | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\033[0m")
    
    # Portfolio Overview
    print(f"\n[PORTFOLIO OVERVIEW]")
    print(f"  Total Strategies: {metrics['total_strategies']:<10} | Paper Bots: {metrics['paper_count']:<10} | Live Bots: {metrics['live_count']}")
    print(f"  Total PnL:       {format_currency(metrics['total_pnl']):<10} | Avg Sharpe: {metrics['avg_sharpe']:<10.2f} | Max DD:     {metrics['max_drawdown']*100:>5.1f}%")
    
    # Active Fleet Table
    print(f"\n[ACTIVE FLEET (PAPER/LIVE)]")
    print("-" * 80)
    print(f"{'ID':<10} | {'NAME':<30} | {'STATUS':<10} | {'TRADES':<7} | {'SHARPE':<7} | {'PNL'}")
    print("-" * 80)
    
    conn = sqlite3.connect(cfg.STRATEGY_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, genome, status, live_trades, live_sharpe, live_pnl FROM strategies WHERE status IN ('paper', 'live') ORDER BY status DESC")
    active_rows = cursor.fetchall()
    
    if not active_rows:
        print("  - No active strategies in fleet -")
    else:
        for row in active_rows:
            s_id, genome_json, status, trades, sharpe, pnl = row
            name = json.loads(genome_json).get("name", "Unknown")
            color = get_color_for_status(status)
            reset = "\033[0m"
            
            sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
            pnl_str = format_currency(pnl)
            
            print(f"{s_id[:8]:<10} | {name[:30]:<30} | {color}{status:<10}{reset} | {trades:<7} | {sharpe_str:<7} | {pnl_str}")

    # Discovery Funnel (Candidates & Validated)
    print(f"\n[DISCOVERY FUNNEL]")
    cursor.execute("SELECT status, COUNT(*) FROM strategies WHERE status IN ('candidate', 'validated') GROUP BY status")
    funnel = dict(cursor.fetchall())
    print(f"  Candidates: {funnel.get('candidate', 0):<10} | Validated (Pending Deploy): {funnel.get('validated', 0)}")
    
    # Recent Log Output (Last 3 lines of factory log if exists)
    print(f"\n[SYSTEM LOGS]")
    if os.path.exists("logs/strategy_factory.log"):
        with open("logs/strategy_factory.log", "r") as f:
            lines = f.readlines()
            for line in lines[-3:]:
                print(f"  > {line.strip()}")
    else:
        print("  Waiting for factory logs...")
        
    print("\n" + "=" * 80)
    print(" Press Ctrl+C to exit dashboard mode.")
    conn.close()

if __name__ == "__main__":
    try:
        while True:
            print_dashboard()
            time.sleep(10) # Update every 10 seconds
    except KeyboardInterrupt:
        print("\nExiting dashboard...")
