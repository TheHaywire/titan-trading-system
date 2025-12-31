
import sys
import os
import pandas as pd
from datetime import datetime

sys.path.append(os.getcwd())
try:
    from titan_system.integrations.google_sheets import TitanSheets
except ImportError:
    print("❌ Failed to import TitanSheets")
    exit()

def verify_system_state():
    print("🕵️  TITAN SYSTEM AUDIT")
    print("="*40)
    
    sheets = TitanSheets()
    if not sheets.enabled:
        print("❌ Google Sheets NOT CONNECTED. Cannot verify.")
        return

    # 1. Verify Regime Log
    print("\n1. MARKET REGIME (Last 5 Entries)")
    try:
        ws = sheets.sheet.worksheet("REGIME LOG")
        data = ws.get_all_values()
        if len(data) > 1:
            df = pd.DataFrame(data[1:], columns=data[0])
            print(df.tail(5).to_string(index=False))
        else:
            print("⚠️  No data in REGIME LOG")
    except Exception as e:
        print(f"❌ Error reading Regime Log: {e}")

    # 2. Verify Exposure
    print("\n2. CURRENCY EXPOSURE")
    try:
        ws = sheets.sheet.worksheet("EXPOSURE")
        data = ws.get_all_values()
        if len(data) > 1:
            print(pd.DataFrame(data[1:], columns=data[0]).to_string(index=False))
        else:
            print("⚠️  No EXPOSURE data (No open trades?)")
    except Exception as e:
        print(f"❌ Error reading Exposure: {e}")

    # 3. Verify Dashboard Status
    print("\n3. SYSTEM HEARTBEAT")
    try:
        ws = sheets.sheet.worksheet("COMMAND DECK")
        status_row = ws.row_values(2) # Row 2 is status
        market_row = ws.row_values(5) # Row 5 is market data
        print(f"   Status: {status_row}")
        print(f"   Market: {market_row}")
    except Exception as e:
        print(f"❌ Error reading Dashboard: {e}")

if __name__ == "__main__":
    verify_system_state()
