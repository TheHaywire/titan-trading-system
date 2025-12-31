
import sys
import os
sys.path.append(os.getcwd())

from titan_system.integrations.google_sheets import TitanSheets

print("🚀 Pushing Strategic Options to Command Center...")

sheets = TitanSheets("google_credentials.json")
if not sheets.enabled:
    print("❌ Critical: Could not connect to sheets.")
    sys.exit(1)

# The 3 Options for a "Beginner" (Plain English)
options = [
    {
        "name": "Option 1: The AI Scalper",
        "description": "I will use Artificial Intelligence to look at the last 100 prices. If the AI sees a pattern (like a 'W' shape) that humans miss, I will buy. I hold for 5 minutes only.",
        "risk": "Medium (Many small trades)",
        "reward": "Consistent Growth"
    },
    {
        "name": "Option 2: The Sniper (Liquidity)",
        "description": "I will wait for other traders to lose money (Stop Loss Hunt). When price fakes them out, I will bet the opposite way. I trade less often, but only when I am very sure.",
        "risk": "Low (High accuracy)",
        "reward": "High (Sniper entries)"
    },
    {
        "name": "Option 3: The Surfer (Volatility)",
        "description": "I wait for the big wave. If Gold starts moving fast (News or US Open), I jump on the board and ride it until it stops. I might lose small amounts trying to catch the wave, but the ride pays for it.",
        "risk": "High (False signals)",
        "reward": "Very High (Jackpot days)"
    }
]

sheets.update_planning_board(options)

print("✅ Strategy Board Updated.")
print("👉 Go to your Google Sheet tab 'Strategy Board' and mark an 'X' next to your choice.")
