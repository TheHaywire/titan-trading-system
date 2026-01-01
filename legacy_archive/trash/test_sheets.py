
import sys
import os
sys.path.append(os.getcwd())

from titan_system.integrations.google_sheets import TitanSheets
import time
import logging

# Configure logging to stdout
logging.basicConfig(level=logging.INFO)

print("🧪 Testing Google Sheets Connection...")
try:
    sheets = TitanSheets("google_credentials.json")
    if sheets.enabled:
        print("✅ Connection Successful!")
        print(f"📄 Sheet Name: {sheets.sheet_name}")
        
        print("📝 Writing Test Data...")
        sheets.update_dashboard({
            "equity": 10000,
            "balance": 10000,
            "open_positions": 0,
            "running": True,
            "strategy_name": "TEST_CONNECTION"
        })
        print("✅ Dashboard Updated.")
        
        sheets.log_system_event("INFO", "TestScript", "Connectivity Check Passed")
        print("✅ Log Entry Added.")
        
    else:
        print("❌ Connection Failed (sheets.enabled is False)")
except Exception as e:
    print(f"❌ Exception: {e}")
