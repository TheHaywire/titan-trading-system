
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging
import datetime
import threading
import time
from typing import Dict, Any, List

logger = logging.getLogger("Titan.Sheets")

class TitanSheets:
    """
    Real-time Google Sheets Logger ("Flight Recorder").
    Handles authentication, reconnection, and batched writing.
    """
    SCOPES = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    
    def __init__(self, key_file: str = "google_credentials.json", sheet_name: str = "Titan Trading Dashboard"):
        self.key_file = key_file
        self.sheet_name = sheet_name
        self.client = None
        self.sheet = None
        self.enabled = False
        
        # Buffers for async writing
        self.trade_queue = []
        self.log_queue = []
        
        self._connect()
        
    def _connect(self):
        """Authenticates with Google API."""
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.key_file, self.SCOPES)
            self.client = gspread.authorize(creds)
            
            # HARDCODED ID from User (More robust than searching by name)
            SHEET_ID = "13VgLHEVviSml8D8g3PHx2sA9FwjSRfgw3l5Sz22G8oY"
            
            try:
                # Try opening by Key first (most reliable)
                self.sheet = self.client.open_by_key(SHEET_ID)
                logger.info(f"✅ Opened Sheet by ID: {SHEET_ID}")
            except Exception:
                # Fallback to name
                logger.info(f"Could not open by ID, trying name '{self.sheet_name}'...")
                self.sheet = self.client.open(self.sheet_name)

            # Initialize Tabs
            self._init_tabs()

            self.enabled = True
            logger.info("✅ Connected to Google Sheets")
            
        except FileNotFoundError:
            logger.warning(f"❌ Google Credentials file '{self.key_file}' not found. Cloud logging disabled.")
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.enabled = False

    def _init_tabs(self):
        """Creates the necessary worksheets if they don't exist."""
        required_tabs = {
            "LANDING": ["ID", "TAB NAME", "DESCRIPTION", "LAST UPDATE", "STATUS"],
            "COMMAND DECK": ["METRIC", "VALUE", "CHANGE", "STATUS", "NOTES"],
            "SYSTEM CHECKLIST": ["CATEGORY", "ITEM", "STATUS", "LAST VERIFIED", "VERIFIED BY", "NOTES"],
            "EXPOSURE": ["CURRENCY", "NET LOTS", "NOTIONAL VALUE $", "% OF EQUITY", "CORRELATION GROUP", "RISK STATUS"],
            "STRATEGY LOGIC": ["STRATEGY", "COMPONENT", "PARAMETER", "VALUE", "DESCRIPTION", "LAST OPTIMIZED"],
            "REGIME LOG": ["TIME", "SYMBOL", "REGIME", "ADX", "ATR", "H1 TREND", "M15 TREND", "ACTION"],
            "CORRELATION MATRIX": ["SYMBOL"] + ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "US30"],
            "PRD OBJECTIVES": ["OBJECTIVE", "KEY RESULT", "CURRENT", "TARGET", "PROGRESS", "STATUS"],
            "PROJECT PLAN": ["PHASE", "TASK", "OWNER", "PRIORITY", "STATUS", "ETA", "NOTES"],
            "PERFORMANCE": ["METRIC", "VALUE", "DESCRIPTION"],
            "TRADE JOURNAL": ["TICKET", "OPEN TIME", "SYMBOL", "TYPE", "LOTS", "ENTRY", "SL", "TP", "CLOSE TIME", "CLOSE", "GROSS PNL", "COMMISSION", "SWAP", "NET PNL", "STRATEGY TAG", "EXIT REASON", "REGIME"],
            "RISK AUDIT": ["SCENARIO", "PROBABILITY", "SEVERITY", "MITIGATION", "STATUS"],
            "LESSONS LEARNED": ["DATE", "EVENT", "ROOT CAUSE", "FIX", "PREVENTED RECURRENCE?"],
            "RAW LOGS": ["TIME", "LEVEL", "COMPONENT", "MESSAGE"],
            "SYMBOL DATABASE": ["SYMBOL", "PATH", "SPREAD", "DIGITS", "CONTRACT SIZE", "MIN LOT", "SWAP LONG", "SWAP SHORT", "TRADE MODE"],
            "TCA ANALYSIS": ["TICKET", "TIME", "SYMBOL", "SIDE", "EXPECTED PRICE", "FILL PRICE", "SLIPPAGE (pips)", "EXPECTED SPREAD", "ACTUAL SPREAD", "LATENCY (ms)", "STATUS"]
        }
        
        for name, headers in required_tabs.items():
            try:
                ws = self.sheet.worksheet(name)
            except gspread.WorksheetNotFound:
                ws = self.sheet.add_worksheet(title=name, rows=2000, cols=10)
                ws.append_row(headers)

    def update_landing_page(self):
        """Updates the Landing Page (TOC) with GIDs and Links."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet("LANDING")
            ws.clear()
            ws.append_row(["ID", "TAB NAME", "DESCRIPTION", "LAST UPDATE", "STATUS"])
            
            # Metadata for Landing Page
            descriptions = {
                "LANDING": "Map of the System",
                "COMMAND DECK": "Live Dashboard (PnL, Equity, Health)",
                "SYSTEM CHECKLIST": "Daily Flight Prep & Go/No-Go",
                "EXPOSURE": "Real-time Currency Risk Map",
                "STRATEGY LOGIC": "Rules of Engagement & Constitution",
                "REGIME LOG": "Market Weather Report (Trend/Range)",
                "CORRELATION MATRIX": "Asset Co-movement Risk",
                "PRD OBJECTIVES": "Business Goals & OKRs",
                "PROJECT PLAN": "Development Roadmap",
                "PERFORMANCE": "Key Performance Indicators",
                "TRADE JOURNAL": "The Ledger of Truth",
                "RISK AUDIT": "Scenario Analysis & Fail-safes",
                "LESSONS LEARNED": "Operational Improvements Log",
                "RAW LOGS": "System Debug Stream"
            }
            
            rows = []
            worksheets = self.sheet.worksheets()
            
            for i, sheet in enumerate(worksheets):
                name = sheet.title
                desc = descriptions.get(name, "System Tab")
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
                # Formula for Hyperlink
                link_formula = f'=HYPERLINK("#gid={sheet.id}", "{name}")'
                
                rows.append([
                    i, 
                    link_formula, 
                    desc, 
                    now, 
                    "🟢 ONLINE"
                ])
            
            # Write Raw Data First (Gspread handles formulas if string starts with =)
            # We must use value_input_option='USER_ENTERED' for formulas to parse
            ws.append_rows(rows, value_input_option='USER_ENTERED')
            
            self.format_tab("LANDING")
            
        except Exception as e:
            logger.error(f"Landing Update Failed: {e}")

    def format_tab(self, tab_name: str):
        """Applies professional formatting to a tab (Bold Headers, Frozen Row, Auto-Width)."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet(tab_name)
            
            # 1. Format Header Row (Bold, Blue Background, White Text)
            ws.format('A1:Z1', {
                "textFormat": {"bold": True, "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0}},
                "backgroundColor": {"red": 0.1, "green": 0.2, "blue": 0.4}, # Navy Blue
                "horizontalAlignment": "CENTER"
            })
            
            # 2. Freeze Header
            ws.freeze(rows=1)
            
            # 3. Set Column Widths (Approximation)
            ws.set_column_width(0, 150) # Col A
            ws.set_column_width(1, 200) # Col B
            ws.set_column_width(2, 120) # Col C
            ws.set_column_width(3, 120) # Col D
            ws.set_column_width(4, 300) # Col E (Notes/Description)
            
        except Exception as e:
            logger.error(f"Formatting failed for {tab_name}: {e}")

    def update_toc(self):
        """Updates the Table of Contents."""
        if not self.enabled: return
        try:
            toc_data = [
                ["1", "COMMAND DECK", "Live System Status & Equity", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "🟢 ONLINE"],
                ["2", "TRADE JOURNAL", "Log of all executed trades", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "🟢 ACTIVE"],
                ["3", "REGIME LOG", "Market Condition Analysis (ADX/Regime)", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "🟢 STREAMING"],
                ["4", "EXPOSURE", "Real-time Currency Risk Exposure", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "🟢 UPDATING"],
                ["5", "PROJECT PLAN", "Development Roadmap & Status", datetime.datetime.now().strftime("%Y-%m-%d"), "ℹ️ STATIC"],
                ["6", "STRATEGY LOGIC", "Detailed Trading Rules & Parameters", datetime.datetime.now().strftime("%Y-%m-%d"), "ℹ️ STATIC"],
                ["7", "PRD", "Objectives & Key Results (OKRs)", datetime.datetime.now().strftime("%Y-%m-%d"), "ℹ️ STATIC"],
                ["8", "SYSTEM CHECKLIST", "Daily Operational Health Check", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "⚠️ CHECK DAILY"],
                ["9", "RISK AUDIT", "Failure Scenarios & Mitigations", datetime.datetime.now().strftime("%Y-%m-%d"), "ℹ️ STATIC"],
                ["10", "LESSONS LEARNED", "Post-Mortem & Improvements", datetime.datetime.now().strftime("%Y-%m-%d"), "write-only"],
            ]
            self.update_documentation("TOC", toc_data)
            self.format_tab("TOC")
        except Exception as e:
            logger.error(f"TOC Update Failed: {e}")

    def update_documentation(self, tab_name: str, data: List[List[str]]):
        """Generic method to update documentation tabs completely."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet(tab_name)
            ws.clear()
            # Restore Header
            headers = {
                "TOC": ["Index", "Sheet Name", "Description", "Last Updated", "Status"],
                "PROJECT PLAN": ["Phase", "Task", "Status", "Priority", "Owner", "Notes"],
                "STRATEGY LOGIC": ["Component", "Rule", "Parameter", "Value", "Edge Case / Exception", "Description"],
                "PRD": ["Objective", "Key Result", "Current Value", "Target", "Timeframe", "Status"],
                "SYSTEM CHECKLIST": ["Category", "Check Item", "Status", "Last Verified", "Action Required"],
                "RISK AUDIT": ["Scenario", "Probability", "Impact", "Mitigation Strategy", "Status"],
                "LESSONS LEARNED": ["Date", "Event/Trade", "What Went Wrong", "What Went Right", "Action Item"]
            }
            ws.append_row(headers.get(tab_name, ["Column 1", "Column 2"]))
            ws.append_rows(data)
            
            # Auto-Format after update
            self.format_tab(tab_name)
            
        except Exception as e:
            logger.error(f"Failed to update {tab_name}: {e}")

    def log_regime(self, symbol: str, regime_data: Dict[str, Any]):
        """Logs market regime changes."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet("REGIME LOG")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [
                now,
                symbol,
                regime_data.get('regime', 'UNKNOWN'),
                f"{regime_data.get('adx', 0):.2f}",
                f"{regime_data.get('atr', 0):.5f}",
                "TRADING" if regime_data.get('trade_scalping') else "PAUSED"
            ]
            ws.append_row(row)
        except Exception as e:
            logger.error(f"Failed to log regime: {e}")

    def update_exposure(self, exposure_data: Dict[str, Any]):
        """Updates the EXPOSURE tab with current currency risks."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet("EXPOSURE")
            ws.clear()
            ws.append_row(["Currency", "Net Exposure (Lots)", "Notional Value", "% of Equity", "Risk Status"])
            
            rows = []
            for currency, data in exposure_data.items():
                rows.append([
                    currency,
                    f"{data.get('volume', 0):.2f}",
                    f"${data.get('value', 0):.2f}",
                    f"{data.get('equity_pct', 0):.1f}%",
                    data.get('status', 'OK')
                ])
            ws.append_rows(rows)
        except Exception as e:
            logger.error(f"Failed to update exposure: {e}")

    def update_performance(self, metrics: Dict[str, Any]):
        """Updates the PERFORMANCE tab."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet("PERFORMANCE")
            ws.clear()
            ws.append_row(["Metric", "Value", "Description"])
            
            rows = []
            for key, val in metrics.items():
                rows.append([key, str(val), ""])
            ws.append_rows(rows)
        except Exception as e:
            logger.error(f"Failed to update performance: {e}")

    def update_dashboard(self, state: Dict[str, Any]):
        """Updates the 'COMMAND DECK' tab."""
        if not self.enabled: return
        
        try:
            ws = self.sheet.worksheet("COMMAND DECK")
            
            # Timestamp
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Row 2: SYSTEM STATUS
            status_row = [
                "RUNNING" if state.get("running") else "STOPPED",
                state.get("equity", 0),
                state.get("balance", 0),
                state.get("profit_today", 0.0),
                state.get("strategy_name", "Multi"),
                now
            ]
            ws.update('A2:F2', [status_row])
            
            # Row 5: LIVE MARKET
            market_row = [
                state.get("symbol", "N/A"),
                state.get("price", 0),
                state.get("trend", "N/A"),
                state.get("ai_signal", "WAIT"),
                f"{state.get('confidence', 0):.2f}",
                state.get("action", "-")
            ]
            ws.update('A5:F5', [market_row])
            
        except Exception as e:
            logger.error(f"Sheet Update Failed: {e}")
            if "401" in str(e):
                self._connect()
    
    def log_trade(self, trade: Dict[str, Any]):
        """Appends a trade to the 'TRADE JOURNAL' tab."""
        if not self.enabled: return
        
        try:
            ws = self.sheet.worksheet("TRADE JOURNAL")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row = [
                now,
                trade.get("symbol"),
                trade.get("type"),
                trade.get("price"), # Entry
                trade.get("close_price", ""), # Exit
                trade.get("volume"),
                trade.get("strategy", "Unknown"),
                trade.get("profit", ""),
                trade.get("comment", "")
            ]
            
            ws.append_row(row)
            
        except Exception as e:
            logger.error(f"Sheet Trade Log Failed: {e}")

    def log_system_event(self, level: str, component: str, message: str):
        """Appends to Logs tab (for Warnings/Errors)."""
        if not self.enabled: return
        try:
            ws = self.sheet.worksheet("Logs")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            row = [now, level, component, str(message)]
            ws.append_row(row)
        except Exception:
            pass
            
    # Keep existing helper methods for Cockpit/Strategy Board
    def update_planning_board(self, options: List[Dict[str, str]]):
        if not self.enabled: return
        try:
            try:
                ws = self.sheet.worksheet("Strategy Board")
                ws.clear()
            except gspread.WorksheetNotFound:
                ws = self.sheet.add_worksheet(title="Strategy Board", rows=100, cols=10)
            ws.append_row(["SELECT", "STRATEGY NAME", "SIMPLE EXPLANATION", "RISK LEVEL", "POTENTIAL REWARD"])
            rows = []
            for opt in options:
                rows.append(["[ ]", opt['name'], opt['description'], opt['risk'], opt['reward']])
            ws.append_rows(rows)
            ws.append_row(["", "", "", "", ""])
            ws.append_row(["INSTRUCTIONS:", "Mark an 'X' in the first column next to the strategy you want to build.", "", "", ""])
        except Exception as e:
            logger.error(f"Failed to update Strategy Board: {e}")

    def log_reasoning(self, context: str, decision: str, evidence: str):
        if not self.enabled: return
        try:
            try:
                ws = self.sheet.worksheet("Glass Box")
            except gspread.WorksheetNotFound:
                ws = self.sheet.add_worksheet(title="Glass Box", rows=1000, cols=5)
                ws.append_row(["Time", "Context", "Decision", "Evidence/Reasoning"])
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ws.append_row([now, context, decision, evidence])
        except Exception as e:
            logger.error(f"Failed to log reasoning: {e}")

    def read_selected_strategy(self) -> str:
        if not self.enabled: return None
        try:
            ws = self.sheet.worksheet("Strategy Board")
            rows = ws.get_all_values()
            for i, row in enumerate(rows[1:], start=1):
                if len(row) > 0 and (row[0].strip().upper() == 'X' or row[0].strip() == '[X]'):
                    return row[1]
            return None
        except Exception as e:
            logger.error(f"Failed to read selection: {e}")
            return None

    def read_cockpit_settings(self) -> Dict[str, Any]:
        if not self.enabled: return {}
        settings = {}
        try:
            ws = self.sheet.worksheet("COCKPIT")
            rows = ws.get_all_values()
            for row in rows[1:]:
                if len(row) >= 2:
                    key = row[0].strip()
                    val_str = row[1].strip().upper()
                    if val_str == "TRUE": val = True
                    elif val_str == "FALSE": val = False
                    elif val_str.replace('.', '', 1).isdigit():
                        val = float(val_str)
                    else:
                        val = val_str
                    if key:
                        settings[key] = val
            return settings
        except Exception as e:
            logger.error(f"Failed to read Cockpit: {e}")
            return {}
