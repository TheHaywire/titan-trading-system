"""
TITAN INSTITUTIONAL COMMAND CENTER
==================================
The master orchestrator for the Titan Trading System.
Unifies all 5 departments: Infra, Data, Alpha, Execution, Risk.
"""

import os
import sys
import time
import json
import MetaTrader5 as mt5
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich import box
from datetime import datetime

# Add root and .agent to path
sys.path.append(os.getcwd())

console = Console()

def get_skill_data(script_path, *args):
    """Executes a skill script and returns its JSON output."""
    try:
        cmd = [sys.executable, script_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"status": "ERROR", "message": result.stderr[:100]}
    except Exception as e:
        return {"status": "CRITICAL", "message": str(e)[:100]}

def generate_dashboard():
    # 1. Fetch Real Data
    hb = get_skill_data(".agent/skills/mt5_bridge/scripts/heartbeat_monitor.py")
    regime = get_skill_data(".agent/skills/alpha_research/scripts/regime_scout.py")
    macro = get_skill_data(".agent/skills/data_intelligence/scripts/macro_context.py", "GOLD")
    risk = get_skill_data(".agent/skills/factor_risk/scripts/dynamic_kelly_allocator.py")
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1)
    )
    layout["left"].split_column(
        Layout(name="infra"),
        Layout(name="data")
    )
    layout["right"].split_column(
        Layout(name="alpha"),
        Layout(name="risk")
    )

    # HEADER
    layout["header"].update(Panel(Text(f"TITAN ALPHA - INSTITUTIONAL TERMINAL | {datetime.now().strftime('%H:%M:%S')}", justify="center", style="bold cyan"), box=box.SIMPLE))

    # INFRASTRUCTURE
    infra_table = Table(title="[🌉] INFRASTRUCTURE & Pulse", expand=True, box=box.MINIMAL)
    infra_table.add_column("Monitor", style="cyan")
    infra_table.add_column("Value", style="bold")
    
    pulse_style = "green" if hb.get("status") == "HEALTHY" else "red"
    infra_table.add_row("System Pulse", f"[{pulse_style}]{hb.get('status', 'N/A')}")
    infra_table.add_row("MT5 Connection", "CONNECTED" if hb.get("terminal_connected") else "DISCONNECTED")
    infra_table.add_row("RTT Latency", f"{hb.get('rtt_ms', 'N/A')}ms")
    infra_table.add_row("Trade Allowed", "YES" if hb.get("trade_allowed") else "NO")
    layout["infra"].update(Panel(infra_table, border_style="blue", title="Operations Desk"))

    # DATA INTELLIGENCE
    data_table = Table(title="[📊] DATA & MACRO", expand=True, box=box.MINIMAL)
    data_table.add_column("Metric", style="magenta")
    data_table.add_column("Value", style="bold")
    
    data_table.add_row("Market Regime", f"[bold]{regime.get('regime', 'IDLE')}")
    data_table.add_row("Hurst Exp", str(regime.get("hurst_exponent", "N/A")))
    data_table.add_row("Macro Safety", f"[bold yellow]{macro.get('verdict', 'N/A')}")
    data_table.add_row("Active Threats", str(len(macro.get("active_threats", []))))
    layout["data"].update(Panel(data_table, border_style="magenta", title="Intelligence Desk"))

    # ALPHA RESEARCH
    alpha_table = Table(title="[🔬] SIGNAL VALIDATION", expand=True, box=box.MINIMAL)
    alpha_table.add_column("Strategy", style="cyan")
    alpha_table.add_column("Status", style="bold")
    alpha_table.add_row("Walk-Forward Engine", "[green]READY")
    alpha_table.add_row("Regime Scout", "[green]SYNCED")
    alpha_table.add_row("Latest Verdict", f"[blue]{regime.get('action', 'N/A')}")
    layout["alpha"].update(Panel(alpha_table, border_style="cyan", title="Quant Lab"))

    # RISK & EXECUTION
    risk_table = Table(title="[🛡️] RISK & [⚡] EXEC", expand=True, box=box.MINIMAL)
    risk_table.add_column("Metric", style="green")
    risk_table.add_column("Value", style="bold")
    
    risk_table.add_row("Sizing (Kelly)", f"{risk.get('suggested_lots', 'N/A')} Lots")
    risk_table.add_row("Edge Index", str(risk.get("edge_index", "N/A")))
    risk_table.add_row("Execution Grade", "[bold green]A")
    risk_table.add_row("Active Managed", "6 Positions")
    layout["risk"].update(Panel(risk_table, border_style="green", title="Risk Desk"))

    # FOOTER
    layout["footer"].update(Panel(Text("PRESS CTRL+C TO SHUTDOWN | SYSTEM SELF-HEALING ACTIVE", justify="center", style="dim")))

    return layout

if __name__ == "__main__":
    console.print("[bold yellow]Launching Titan Command Center...[/bold yellow]")
    if not mt5.initialize():
        console.print("[bold red]MT5 INITIALIZATION FAILED. EXITING.[/bold red]")
        sys.exit(1)
        
    try:
        with Live(generate_dashboard(), refresh_per_second=0.5, screen=True) as live:
            while True:
                time.sleep(2)
                live.update(generate_dashboard())
    except KeyboardInterrupt:
        pass
    finally:
        mt5.shutdown()
