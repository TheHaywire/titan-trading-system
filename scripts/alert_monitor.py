"""
Institutional Dynamic Alert Monitor
Monitors price levels and institutional patterns in real-time.
Usage:
  python scripts/alert_monitor.py add GOLD > 2650
  python scripts/alert_monitor.py add BTCUSD < 90000
  python scripts/alert_monitor.py smart GOLD "HAMMER" 1H
  python scripts/alert_monitor.py list
  python scripts/alert_monitor.py run
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd
import MetaTrader5 as mt5

# Add project root to path
sys.path.append(os.getcwd())

from scripts.technical_patterns import get_all_patterns

ALERTS_FILE = Path("data/alerts.json")

class AlertMonitor:
    def __init__(self):
        self.alerts = self._load_alerts()
        self.initialize_mt5()
        
    def _load_alerts(self):
        if ALERTS_FILE.exists():
            with open(ALERTS_FILE, "r") as f:
                return json.load(f)
        return {"price_alerts": [], "smart_alerts": []}
        
    def _save_alerts(self):
        ALERTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ALERTS_FILE, "w") as f:
            json.dump(self.alerts, f, indent=4)
            
    def initialize_mt5(self):
        if not mt5.initialize():
            print("❌ MT5 Initialization Failed")
            sys.exit(1)
            
    def add_price_alert(self, symbol, condition, level):
        alert = {
            "id": int(time.time()),
            "symbol": symbol.upper(),
            "condition": condition, # ">" or "<"
            "level": float(level),
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        self.alerts["price_alerts"].append(alert)
        self._save_alerts()
        print(f"✅ Price Alert Added: {symbol} {condition} {level}")
        
    def add_smart_alert(self, symbol, pattern, timeframe):
        # Map human-readable timeframe to MT5
        tf_map = {
            "1M": mt5.TIMEFRAME_M1, "5M": mt5.TIMEFRAME_M5, "15M": mt5.TIMEFRAME_M15,
            "30M": mt5.TIMEFRAME_M30, "1H": mt5.TIMEFRAME_H1, "4H": mt5.TIMEFRAME_H4,
            "1D": mt5.TIMEFRAME_D1, "1W": mt5.TIMEFRAME_W1
        }
        
        if timeframe not in tf_map:
            print(f"❌ Invalid Timeframe: {timeframe}")
            return
            
        alert = {
            "id": int(time.time()),
            "symbol": symbol.upper(),
            "pattern": pattern.upper(),
            "timeframe": timeframe,
            "tf_val": tf_map[timeframe],
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        self.alerts["smart_alerts"].append(alert)
        self._save_alerts()
        print(f"✅ Smart Alert Added: {symbol} {pattern} ({timeframe})")
        
    def list_alerts(self):
        print("\n🔔 ACTIVE ALERTS")
        print("-" * 50)
        
        if not self.alerts["price_alerts"] and not self.alerts["smart_alerts"]:
            print("No active alerts.")
            return
            
        if self.alerts["price_alerts"]:
            print("\n📈 Price Levels:")
            for a in self.alerts["price_alerts"]:
                status = "Triggered" if a["triggered"] else "Active"
                print(f"  [{a['id']}] {a['symbol']} {a['condition']} {a['level']} ({status})")
                
        if self.alerts["smart_alerts"]:
            print("\n🧠 Smart Patterns:")
            for a in self.alerts["smart_alerts"]:
                status = "Triggered" if a["triggered"] else "Active"
                print(f"  [{a['id']}] {a['symbol']} - {a['pattern']} on {a['timeframe']} ({status})")
        print("-" * 50 + "\n")

    def remove_alert(self, alert_id):
        alert_id = int(alert_id)
        found = False
        
        new_price = [a for a in self.alerts["price_alerts"] if a["id"] != alert_id]
        if len(new_price) != len(self.alerts["price_alerts"]): found = True
        self.alerts["price_alerts"] = new_price
        
        new_smart = [a for a in self.alerts["smart_alerts"] if a["id"] != alert_id]
        if len(new_smart) != len(self.alerts["smart_alerts"]): found = True
        self.alerts["smart_alerts"] = new_smart
        
        if found:
            self._save_alerts()
            print(f"🗑️ Alert {alert_id} removed.")
        else:
            print(f"⚠️ Alert {alert_id} not found.")

    def run_monitor(self):
        print("🚀 Alert Monitor Started. Polling market...")
        try:
            while True:
                self._check_price_alerts()
                self._check_smart_alerts()
                time.sleep(30) # Poll every 30 seconds
        except KeyboardInterrupt:
            print("\nStopping Alert Monitor...")

    def _check_price_alerts(self):
        for alert in self.alerts["price_alerts"]:
            if alert["triggered"]: continue
            
            tick = mt5.symbol_info_tick(alert["symbol"])
            if not tick: continue
            
            price = tick.bid
            triggered = False
            
            if alert["condition"] == ">" and price > alert["level"]:
                triggered = True
            elif alert["condition"] == "<" and price < alert["level"]:
                triggered = True
                
            if triggered:
                self._notify(f"🎯 PRICE TRIGGER: {alert['symbol']} is now {alert['condition']} {alert['level']} (Current: {price:.5f})")
                alert["triggered"] = True
                self._save_alerts()

    def _check_smart_alerts(self):
        for alert in self.alerts["smart_alerts"]:
            if alert["triggered"]: continue
            
            # Fetch data
            rates = mt5.copy_rates_from_pos(alert["symbol"], alert["tf_val"], 0, 100)
            if rates is None or len(rates) < 2: continue
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Add RSI for divergence detection
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            patterns = get_all_patterns(df)
            
            # Check if target pattern is in detected patterns
            found_patterns = [p for p in patterns if alert["pattern"] in p.upper()]
            
            if found_patterns:
                self._notify(f"🧠 SMART TRIGGER: {alert['pattern']} found on {alert['symbol']} ({alert['timeframe']})")
                alert["triggered"] = True
                self._save_alerts()

    def _notify(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\n🔔 [{timestamp}] {message}")
        # Could add sound, email, or telegram here later

def main():
    monitor = AlertMonitor()
    
    parser = argparse.ArgumentParser(description="Titan Alert Monitor")
    subparsers = parser.add_subparsers(dest="command")
    
    # Add Price Alert
    add_parser = subparsers.add_parser("add")
    add_parser.add_argument("symbol")
    add_parser.add_argument("condition", choices=[">", "<"])
    add_parser.add_argument("level", type=float)
    
    # Add Smart Alert
    smart_parser = subparsers.add_parser("smart")
    smart_parser.add_argument("symbol")
    smart_parser.add_argument("pattern")
    smart_parser.add_argument("timeframe", default="1H")
    
    # List Alerts
    subparsers.add_parser("list")
    
    # Remove Alert
    remove_parser = subparsers.add_parser("remove")
    remove_parser.add_argument("id")
    
    # Run Monitor
    subparsers.add_parser("run")
    
    args = parser.parse_args()
    
    if args.command == "add":
        monitor.add_price_alert(args.symbol, args.condition, args.level)
    elif args.command == "smart":
        monitor.add_smart_alert(args.symbol, args.pattern, args.timeframe)
    elif args.command == "list":
        monitor.list_alerts()
    elif args.command == "remove":
        monitor.remove_alert(args.id)
    elif args.command == "run":
        monitor.run_monitor()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
