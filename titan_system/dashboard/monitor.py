import os
import sys
import time
import json
import sqlite3
from datetime import datetime

from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.console import Console
from rich.align import Align

# Path Hack to find titan_system if run from root
sys.path.append(os.getcwd())

class TitanMonitor:
    def __init__(self, db_path="titan_system/titan.db", state_path="titan_system/dashboard/state.json"):
        self.db_path = db_path
        self.state_path = state_path
        self.console = Console()
        
    def get_layout(self) -> Layout:
        layout = Layout()
        
        # Split: Header (Top), Body (Middle), Footer (Bottom)
        layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=10)
        )
        
        # Split Main: Left (AI Pulse), Right (Trades)
        layout["main"].split_row(
            Layout(name="ai_pulse", ratio=1),
            Layout(name="trades", ratio=2),
        )
        
        return layout

    def get_header(self, state):
        timestamp = datetime.fromtimestamp(state.get('timestamp', time.time())).strftime('%H:%M:%S')
        equity = state.get('equity', 0)
        balance = state.get('balance', 0)
        active = state.get('open_positions', 0)
        
        # Color logic
        eq_color = "green" if equity >= balance else "red"
        
        text = Text(f"TITAN QUANT SYSTEM | {timestamp} | Equity: ${equity:,.2f} | Active Trades: {active}", style="bold white on blue", justify="center")
        return Panel(text, border_style="blue")
    
    def get_ai_pulse(self):
        # In a real scenario, we'd read this from state.json specifically populated by the AI
        # For now, placeholder or read logs
        return Panel(
            Align.center(
                Text("\n\n🧠 AI BRAIN ACTIVE\n\nMetric: Institutional Flow\nConfidence: 87.4%\nPrediction: BULLISH", style="bold green")
            ),
            title="AI Pulse", border_style="green"
        )
        
    def get_trades_table(self):
        table = Table(expand=True, border_style="dim")
        table.add_column("Symbol")
        table.add_column("Type")
        table.add_column("Profit")
        table.add_column("Time")
        
        try:
            if not os.path.exists(self.db_path):
                table.add_row("No data yet", "", "", "")
                return Panel(table, title="Recent Trades")
                
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT symbol, type, profit, open_time FROM trades ORDER BY open_time DESC LIMIT 5")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                table.add_row("No trades yet", "", "", "")
            else:
                for r in rows:
                    profit_color = "green" if r[2] >= 0 else "red"
                    table.add_row(r[0], r[1], Text(f"${r[2]:.2f}", style=profit_color), str(r[3]))
                
        except Exception as e:
            table.add_row(f"Waiting for data...", "", "", "")
            
        return Panel(table, title="Recent Trades")

    def get_logs(self):
        # Tailing logs from DB
        try:
            if not os.path.exists(self.db_path):
                return Panel("Waiting for system logs...", title="System Logs", border_style="white")
                
            conn = sqlite3.connect(self.db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute("SELECT timestamp, component, message FROM logs ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return Panel("No logs yet", title="System Logs", border_style="white")
            
            log_text = Text()
            for r in rows:
                try:
                    t = datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S").strftime("%H:%M:%S")
                except Exception:
                    t = str(r[0])[:8]
                log_text.append(f"[{t}] {r[1].ljust(10)} | {r[2]}\n")
                
            return Panel(log_text, title="System Logs", border_style="white")
            
        except Exception as e:
            return Panel("Initializing...", title="System Logs")

    def run(self):
        layout = self.get_layout()
        
        with Live(layout, refresh_per_second=1, screen=True):
            while True:
                # Load State
                try:
                    if os.path.exists(self.state_path):
                        with open(self.state_path, 'r') as f:
                            state = json.load(f)
                    else:
                        state = {}
                except Exception:
                    state = {}
                
                layout["header"].update(self.get_header(state))
                layout["ai_pulse"].update(self.get_ai_pulse())
                layout["trades"].update(self.get_trades_table())
                layout["footer"].update(self.get_logs())
                
                time.sleep(1)

if __name__ == "__main__":
    monitor = TitanMonitor()
    try:
        monitor.run()
    except KeyboardInterrupt:
        pass
