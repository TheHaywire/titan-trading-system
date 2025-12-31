
import sys
import os
sys.path.append(os.getcwd())

from titan_system.integrations.google_sheets import TitanSheets

print("🤖 AGENT AUTO-SELECTION: Liquidity Hunter")
print("---------------------------------------")

sheets = TitanSheets("google_credentials.json")
if not sheets.enabled:
    print("❌ Fatal: No connection.")
    sys.exit(1)

try:
    ws = sheets.sheet.worksheet("STRATEGY BOARD")
    
    # 1. Clear previous selections (Column A)
    # 2. Mark Row 3 (Index match for Liquidity Hunter)
    # Based on build_command_center.py order: 
    # Row 2 = Neural
    # Row 3 = Liquidity
    # Row 4 = Volatility
    
    # Uncheck all
    ws.update("A2:A4", [[""], [""], [""]])
    
    # Check Liquidity Hunter (Row 3)
    ws.update_cell(3, 1, "[X]")
    ws.update_cell(3, 6, "ACTIVE") # Status Column
    
    print("✅ Selected: Liquidity Hunter")
    
except Exception as e:
    print(f"❌ Selection Failed: {e}")
