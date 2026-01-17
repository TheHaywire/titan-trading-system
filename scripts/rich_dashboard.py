import os
import time
import sys
import threading
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.console import Console
from rich import box
from rich.progress import SpinnerColumn, Progress, TextColumn

# Import internal modules
sys.path.append(os.getcwd())
try:
    from scripts.risk_monte_carlo import get_monte_carlo_results
    from scripts.pattern_recognition_engine import PatternEngine
except ImportError:
    # Fallback for relative paths
    from risk_monte_carlo import get_monte_carlo_results
    from pattern_recognition_engine import PatternEngine

WATCHLIST = ["ETHUSD", "SILVER", "GOLD", "US100Cash", "BTCUSD"]
pattern_engine = PatternEngine()

# SHARED STATE
SHARED_DATA = {
    "mc_results": {},
    "scanner_results": {},
    "last_update": "Never",
    "status": "Initializing...",
    "error": "None",
    "heartbeat": 0
}

def data_fetcher():
    """Background thread to fetch heavy data without blocking UI."""
    while True:
        try:
            if not mt5.initialize():
                SHARED_DATA["status"] = "🔴 MT5 CONNECTION ERROR"
                time.sleep(2)
                continue
            
            # Simple check
            acct = mt5.account_info()
            if not acct:
                SHARED_DATA["status"] = "🔴 ACCOUNT INFO LOAD ERROR"
                time.sleep(2)
                continue

            # Heavy Calculation: Monte Carlo
            SHARED_DATA["status"] = "🎲 Calc Monte Carlo (10k)..."
            mc = get_monte_carlo_results(standalone=False)
            if mc is not None:
                SHARED_DATA["mc_results"] = mc
            
            # Alpha Scan
            SHARED_DATA["status"] = "📡 Scanning Alpha Radar..."
            new_scanner = {}
            for sym in WATCHLIST:
                rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 100)
                if rates is not None:
                    df = pd.DataFrame(rates)
                    patterns = pattern_engine.analyze(df)
                    sma20 = df['close'].rolling(20).mean().iloc[-1]
                    sma50 = df['close'].rolling(50).mean().iloc[-1]
                    trend = "🟢 BULL" if sma20 > sma50 else "🔴 BEAR"
                    new_scanner[sym] = {"trend": trend, "patterns": patterns}
                else:
                    new_scanner[sym] = {"trend": "ERROR", "patterns": ["No Data"]}
            
            SHARED_DATA["scanner_results"] = new_scanner
            SHARED_DATA["last_update"] = datetime.now().strftime('%H:%M:%S')
            SHARED_DATA["status"] = "🟢 ONLINE"
            SHARED_DATA["error"] = "None"
            
            time.sleep(2) 
        except Exception as e:
            SHARED_DATA["error"] = str(e)
            SHARED_DATA["status"] = "❌ THREAD CRASHED"
            time.sleep(5)

def make_layout() -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="main", ratio=1),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="account", ratio=1),
        Layout(name="status", ratio=2),
    )
    layout["status"].split(
        Layout(name="positions", ratio=1),
        Layout(name="scanner", ratio=1),
    )
    return layout

def get_positions_table():
    positions = mt5.positions_get()
    mc_data = SHARED_DATA["mc_results"]
    
    table = Table(title="✈️ Active Flight Deck", box=box.ROUNDED, expand=True)
    table.add_column("Ticket")
    table.add_column("Symbol")
    table.add_column("Type")
    table.add_column("PnL")
    table.add_column("MC Win %", style="bold yellow")
    
    if positions:
        for p in positions:
            type_str = "BUY" if p.type == 0 else "SELL"
            pnl_style = "green" if p.profit >= 0 else "red"
            mc_info = mc_data.get(p.ticket if p.ticket in mc_data else str(p.ticket), {})
            mc_win = mc_info.get("win_prob", "...")
            if mc_win != "...": mc_win = f"{mc_win}%"
                
            table.add_row(
                str(p.ticket), p.symbol, type_str, 
                f"[{pnl_style}]${p.profit:,.2f}[/]", 
                str(mc_win)
            )
    else:
        table.add_row("-", "No Positions found", "-", "-", "-")
    return table

def get_scanner_table():
    table = Table(title="📡 Alpha Radar (Council Consensus)", box=box.ROUNDED, expand=True)
    table.add_column("Symbol")
    table.add_column("Trend")
    table.add_column("Pattern (FinViz)")
    table.add_column("Win Prob", justify="right")
    table.add_column("Council Sentiment", style="italic")
    
    scanner_results = SHARED_DATA.get("scanner_results", {})
    
    for sym in WATCHLIST:
        if sym not in scanner_results:
            table.add_row(sym, "[yellow]Syncing...[/]", "...", "...", "...")
            continue
            
        res = scanner_results[sym]
        trend = res["trend"]
        pats = res["patterns"]
        pat_str = pats[0] if pats else "Neutral"
        
        # Simple probability calc
        prob_val = 50
        if "BULL" in trend: prob_val += 5
        if "BEAR" in trend: prob_val += 5
        if "Channel" in pat_str: prob_val += 10
        if "Wedge" in pat_str: prob_val += 15
        
        # Council Sentiment logic
        sentiment = "NEUTRAL"
        if "BULL" in trend and "Wedge Down" in pat_str: sentiment = "BULLISH (Alpha Hunter)"
        elif "BEAR" in trend and "Wedge Up" in pat_str: sentiment = "BEARISH (Inducement Hunter)"
        elif prob_val > 60: sentiment = "ACCUMULATING (Scaling Architect)"
        
        table.add_row(sym, trend, pat_str, f"{prob_val}%", sentiment)
        
    return table

def get_topology_panel():
    acct = mt5.account_info()
    st = SHARED_DATA["status"]
    rm = os.getenv("TITAN_RISK_MODE", "CONSERVATIVE")
    
    text = f"🌐 [bold cyan]SYSTEM TOPOLOGY[/]\n"
    text += f"├─ [yellow]MT5 Bridge:[/] {'🟢 ONLINE' if acct else '🔴 OFFLINE'}\n"
    text += f"├─ [yellow]Engine Status:[/] {st}\n"
    text += f"├─ [yellow]Risk Mode:[/] {rm}\n"
    text += f"├─ [yellow]Heartbeat:[/] {SHARED_DATA['heartbeat']}\n"
    text += f"└─ [yellow]Last MC Sync:[/] {SHARED_DATA['last_update']}"
    
    if SHARED_DATA["error"] != "None":
        text += f"\n\n[red]ERR: {SHARED_DATA['error']}[/]"
        
    return Panel(text, box=box.ROUNDED)

def run_dashboard():
    if not mt5.initialize():
        print("Initial MT5 Connection Failed.")
        return

    # Background thread
    t = threading.Thread(target=data_fetcher, daemon=True)
    t.start()

    layout = make_layout()
    with Live(layout, refresh_per_second=2, screen=True) as live:
        try:
            while True:
                SHARED_DATA["heartbeat"] += 1
                layout["header"].update(Panel(f"🏛️ TITAN COMMAND CENTER | {datetime.now().strftime('%H:%M:%S')} | MODE: PILOT ACTIVE", style="bold blue"))
                layout["account"].update(get_topology_panel())
                layout["positions"].update(get_positions_table())
                layout["scanner"].update(get_scanner_table())
                layout["footer"].update(Panel(f"Running... Check 'Engine Status' in Topology for updates. Status: {SHARED_DATA['status']}", style="dim"))
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    if "--test-headless" in sys.argv:
        # Just run one cycle and print success to verify functions exist
        if not mt5.initialize():
            print("MT5 Init Failed")
            sys.exit(1)
        try:
            l = make_layout()
            p = get_positions_table()
            s = get_scanner_table()
            t = get_topology_panel()
            print("DASHBOARD CODE VALIDATED")
            mt5.shutdown()
            sys.exit(0)
        except Exception as e:
            print(f"VALIDATION FAILED: {str(e)}")
            sys.exit(1)
            
    try:
        run_dashboard()
    except KeyboardInterrupt:
        mt5.shutdown()
