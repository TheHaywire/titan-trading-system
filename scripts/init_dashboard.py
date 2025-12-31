
import sys
import os
import logging

# Setup Logging
logging.basicConfig(level=logging.INFO)

sys.path.append(os.getcwd())
try:
    from titan_system.integrations.google_sheets import TitanSheets
except ImportError as e:
    print(f"Import Error: {e}")
    exit()

def init_dashboard():
    print("🚀 Initializing Institutional Dashboard...")
    try:
        sheets = TitanSheets()
        if sheets.enabled:
            print("✅ Connection Successful!")
            print("📊 Verifying Tabs...")
            # Constructor calls _init_tabs() automatically
            print("✅ Tabs 'REGIME LOG', 'EXPOSURE', 'PERFORMANCE' should be created.")
            
            # Test Write
            print("📝 Testing Write Permissions...")
            sheets.log_system_event("INFO", "Setup", "Institutional Dashboard Initialized")
            sheets.log_regime("TEST", {"regime": "INIT", "adx": 0, "atr": 0, "trade_scalping": True})
            print("✅ Test Write Successful!")
        else:
            print("❌ Connection Failed: Sheets disabled.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    init_dashboard()
