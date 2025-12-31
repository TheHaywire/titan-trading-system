
import sys
import os
sys.path.append(os.getcwd())

from titan_system.integrations.google_sheets import TitanSheets

print("📡 Connecting to Command Center...")
sheets = TitanSheets("google_credentials.json")

if not sheets.enabled:
    print("❌ Critical: Could not connect to sheets.")
    sys.exit(1)

print("📖 Reading Strategy Board...")
selection = sheets.read_selected_strategy()

if selection:
    print(f"\n✅ USER SELECTED: {selection}")
    print("------------------------------------------------")
    print("Initiating build sequence for this strategy...")
else:
    print("\n⚠️ NO SELECTION FOUND.")
    print("Please go to the 'Strategy Board' tab and mark an 'X' in the first column next to your choice.")
