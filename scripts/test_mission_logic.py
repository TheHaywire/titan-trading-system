"""
UNIT TEST: Mission-Aware Analysis
=================================
Verifies that the bot correctly identifies a Mission mandate for GOLD.
"""

import sys, os
import pandas as pd
import numpy as np
from datetime import datetime

# Mock MT5
class MockMT5:
    def TIMEFRAME_M5(self): return 5
    def TIMEFRAME_H1(self): return 60

# Import Bot
sys.path.insert(0, os.getcwd())
from scripts.autonomous_bot import AutonomousTradingBot

def test_mission_detection():
    print("--- [TEST] Mission Detection ---")
    bot = AutonomousTradingBot()
    
    # Check if missions are loaded
    print(f"Missions loaded: {list(bot.active_missions.keys())}")
    
    if "GOLD" not in bot.active_missions:
        print("FAIL: GOLD mission not found in active_missions.json")
        return

    # Create a mock dataframe
    # Case 1: Price far from entry
    df_far = pd.DataFrame({
        'close': [4509.0, 4510.0, 4509.06],
        'high': [4515.0, 4516.0, 4515.0],
        'low': [4500.0, 4501.0, 4500.0]
    })
    
    print("\n[Case 1] Price far from entry (4290.0 vs 4509.06)")
    result_far = bot.analyze_symbol("GOLD", df_far)
    if result_far is None:
        print("PASS: No immediate signal (waiting for entry)")
    else:
        print(f"FAIL: Signal triggered prematurely: {result_far['direction']}")

    # Case 2: Price at entry zone
    df_at_entry = pd.DataFrame({
        'close': [4295.0, 4292.0, 4290.5],
        'high': [4300.0, 4298.0, 4295.0],
        'low': [4285.0, 4280.0, 4288.0]
    })
    
    print("\n[Case 2] Price at entry zone (4290.0 vs 4290.5)")
    result_at = bot.analyze_symbol("GOLD", df_at_entry)
    
    if result_at and result_at.get("is_mission"):
        print(f"PASS: Mission Signal Detected!")
        print(f"Direction: {result_at['direction']}")
        print(f"Entry: {result_at['price']}")
        print(f"SL: {result_at['sl']}")
        print(f"TP: {result_at['tp']}")
    else:
        print("FAIL: Mission signal not detected at entry zone")

if __name__ == "__main__":
    test_mission_detection()
