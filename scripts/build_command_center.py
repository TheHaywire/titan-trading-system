
import sys
import os
import time
sys.path.append(os.getcwd())

from titan_system.integrations.google_sheets import TitanSheets
import gspread

print("🏗️ TITAN COMMAND CENTER: Initialization Protocol")
print("-----------------------------------------------")

# 1. Connect
try:
    sheets = TitanSheets("google_credentials.json")
    if not sheets.enabled:
        print("❌ Fatal: Could not connect to Google Sheets.")
        sys.exit(1)
    
    ss = sheets.sheet # The Spreadsheet object
    print(f"✅ Connected to: {ss.title}")
except Exception as e:
    print(f"❌ Connection Error: {e}")
    sys.exit(1)

# 2. Define Schema
SCHEMA = {
    "COMMAND DECK": {
        "index": 0,
        "rows": 100,
        "cols": 10,
        "headers": [
            ["SYSTEM STATUS", "", "", "", "", "LAST UPDATE"],
            ["STATUS", "EQUITY", "BALANCE", "ODAY PnL", "ACTIVE STRATEGY", "TIMESTAMP"], # Row 2
            ["", "", "", "", "", ""], # Spacer
            ["LIVE MARKET MONITOR", "", "", "", "", ""],
            ["SYMBOL", "PRICE", "TREND", "AI SIGNAL", "CONFIDENCE", "ACTION"]
        ],
        "frozen_rows": 2
    },
    "STRATEGY BOARD": {
        "index": 1,
        "rows": 50,
        "cols": 6,
        "headers": [
            ["SELECT (X)", "STRATEGY NAME", "DESCRIPTION", "RISK PROFILE", "REWARD", "STATUS"]
        ],
        "frozen_rows": 1
    },
    "COCKPIT": {
        "index": 2,
        "rows": 50,
        "cols": 4,
        "headers": [
            ["SETTING_KEY", "VALUE", "DESCRIPTION", "LAST_SYNC"]
        ],
        "frozen_rows": 1
    },
    "TRADE JOURNAL": {
        "index": 3,
        "rows": 1000,
        "cols": 9,
        "headers": [
            ["TIME", "SYMBOL", "TYPE", "ENTRY", "EXIT", "LOTS", "STRATEGY", "PNL", "NOTES"]
        ],
        "frozen_rows": 1
    },
    "GLASS BOX": {
        "index": 4,
        "rows": 2000,
        "cols": 5,
        "headers": [
            ["TIME", "CONTEXT", "DECISION", "EVIDENCE / REASONING", "AI CONFIDENCE"]
        ],
        "frozen_rows": 1
    }
}

# 3. Wipe and Rebuild
print("⚠️  Wiping existing tabs...")

# We need at least one tab to exist to delete others.
# Create a temp tab first.
try:
    temp = ss.add_worksheet(title="TEMP_BUILD", rows=1, cols=1)
except:
    temp = ss.worksheet("TEMP_BUILD")

# Delete all other tabs
for ws in ss.worksheets():
    if ws.title != "TEMP_BUILD":
        print(f"   - Deleting {ws.title}")
        try:
            ss.del_worksheet(ws)
            time.sleep(1.0) # Rate limit safety
        except Exception as e:
            print(f"     ! Retry delete {ws.title}: {e}")

# Create New Tabs
print("🔨  Constructing Command Center...")
for name, config in SCHEMA.items():
    print(f"   + Creating '{name}'")
    try:
        ws = ss.add_worksheet(title=name, rows=config['rows'], cols=config['cols'])
        
        # Write Headers
        ws.insert_rows(config['headers'], row=1)
        
        # Data Population (Defaults)
        if name == "COCKPIT":
            defaults = [
                ["TRADING_ENABLED", "TRUE", "Master Switch (TRUE/FALSE)", ""],
                ["RISK_PER_TRADE", "1.0", "Percentage of Equity per trade", ""],
                ["MAX_DAILY_LOSS", "3.0", "Hard Stop Loss % for the day", ""],
                ["TELEGRAM_ALERTS", "TRUE", "Send alerts to phone", ""],
                ["AI_MODE", "HYBRID", "PURE_AI vs HYBRID (Rules+AI)", ""]
            ]
            ws.insert_rows(defaults, row=2)
            
        elif name == "STRATEGY BOARD":
            # Re-push options
            options = [
                ["", "Neural Scalper", "AI predicts next 5 candles. High Tech.", "Medium", "Consistent Growth", "PENDING"],
                ["", "Liquidity Hunter", "Trades Stop Hunts & Fakeouts.", "Low (Sniper)", "High Accuracy", "PENDING"],
                ["", "Volatility Surfer", "Ride the big breakouts.", "High (Drawdown)", "Jackpot Wins", "PENDING"]
            ]
            ws.insert_rows(options, row=2)
            
    except Exception as e:
        print(f"   ❌ Failed to create {name}: {e}")

# Delete temp
try:
    ss.del_worksheet(temp)
except:
    pass

print("✨  Formatting Complete.")
print("✅  COMMAND CENTER READY.")
