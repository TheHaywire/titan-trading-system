"""
MISSION CONTROLLER v1.0
=======================
Parses Titanium Alpha Mission Reports (Markdown) into actionable JSON.
Enables the bridge from AI Strategic Intel to Autonomous Execution.
"""

import os
import re
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [MISSION] %(message)s')
logger = logging.getLogger("MissionController")

class MissionController:
    def __init__(self, mission_dir="analysis/titan_alpha", config_path="config/active_missions.json"):
        self.mission_dir = mission_dir
        self.config_path = config_path
        
    def get_latest_mission(self, symbol="GOLD"):
        """Find the most recent mission report for a symbol."""
        if not os.path.exists(self.mission_dir):
            return None
        
        files = [f for f in os.listdir(self.mission_dir) if symbol in f and f.endswith(".md")]
        if not files:
            return None
        
        # Sort by filename (which includes timestamp)
        files.sort(reverse=True)
        return os.path.join(self.mission_dir, files[0])

    def parse_report(self, file_path):
        """Extract Execution Parameters from Markdown table."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find the Execution Parameters table
            # Looking for | Parameter | Value | and the following rows
            table_match = re.search(r"### 🎯 EXECUTION PARAMETERS\n\| Parameter \| Value \|\n\|.*?\|.*?\|\n((?:\|.*?\|.*?\|\n)+)", content)
            
            if not table_match:
                logger.warning(f"No execution table found in {file_path}")
                return None
            
            table_body = table_match.group(1)
            params = {}
            
            for line in table_body.strip().split("\n"):
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    key = parts[0].replace("**", "")
                    value = parts[1]
                    params[key] = value
            
            def extract_first_number(text):
                """Helper to get the first float from a string like '91250 - 91350' or '$4290.00'."""
                match = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
                return float(match.group(1)) if match else 0.0

            # Clean and typeset values
            mission = {
                "symbol": os.path.basename(file_path).split("_")[0],
                "direction": params.get("Direction", "UNKNOWN"),
                "entry": extract_first_number(params.get("Entry Zone", "0")),
                "sl": extract_first_number(params.get("Stop Loss", "0")),
                "tp1": extract_first_number(params.get("Take Profit 1", "0")),
                "tp2": extract_first_number(params.get("Take Profit 2", "0")),
                "risk_mult": extract_first_number(params.get("Risk Multiplier", "1.0")),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "source": os.path.basename(file_path)
            }
            
            # Additional metadata (Status)
            status_match = re.search(r"\*\*Status\*\*: (.*)", content)
            if status_match:
                mission["status_desc"] = status_match.group(1).strip()
                
            return mission
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}")
            return None

    def update_active_missions(self, symbol="GOLD"):
        """Main entry point: scan, parse, and save."""
        report_path = self.get_latest_mission(symbol)
        if not report_path:
            logger.info(f"No mission reports found for {symbol}")
            return False
            
        logger.info(f"Processing latest mission: {report_path}")
        mission_data = self.parse_report(report_path)
        
        if not mission_data:
            return False
            
        # Load existing missions
        missions = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    missions = json.load(f)
            except:
                pass
        
        # Update with new mission
        missions[symbol] = mission_data
        
        # Save back
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(missions, f, indent=4)
            
    def update_all_missions(self):
        """Scan the entire mission directory and update all active missions."""
        if not os.path.exists(self.mission_dir):
            return
            
        files = [f for f in os.listdir(self.mission_dir) if f.endswith(".md") and "_MISSION_REPORT_" in f]
        symbols = set([f.split("_")[0] for f in files])
        
        logger.info(f"Scanning for all missions... Found {len(symbols)} unique symbols")
        
        for symbol in symbols:
            self.update_active_missions(symbol)

if __name__ == "__main__":
    controller = MissionController()
    controller.update_all_missions()
