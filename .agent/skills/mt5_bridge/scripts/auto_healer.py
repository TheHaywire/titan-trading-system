"""
AUTO HEALER
===========
Autonomous recovery system for MT5 infrastructure.
Attempts to restore connectivity when Heartbeat fails.
"""

import MetaTrader5 as mt5
import time
import json
import os
import subprocess
from datetime import datetime

def attempt_recovery():
    print(f"[{datetime.now().isoformat()}] AUTO-HEAL: Initiating recovery sequence...")
    
    # 1. Clean Shutdown
    mt5.shutdown()
    time.sleep(2)
    
    # 2. Re-initialize
    success = mt5.initialize()
    
    if not success:
        # 3. Process Check (Is the exe even running?)
        # On Windows, we can use tasklist to check for Metatrader
        try:
            output = subprocess.check_output('tasklist /FI "IMAGENAME eq metatester64.exe" /FI "IMAGENAME eq terminal64.exe"', shell=True).decode()
            if "terminal64.exe" not in output:
                return {
                    "recovery_status": "FAILED",
                    "reason": "MT5 Terminal Process (terminal64.exe) is not running.",
                    "action_required": "Please restart the MetaTrader 5 terminal manually."
                }
        except:
            pass
            
        return {
            "recovery_status": "FAILED",
            "reason": "Initialization failed even with process running."
        }
    
    # 4. Refresh Cache & Sync
    # Trigger a dummy copy to force cache refresh
    mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M1, 0, 1)
    
    acc = mt5.account_info()
    return {
        "recovery_status": "SUCCESS",
        "timestamp": datetime.now().isoformat(),
        "account": acc.login,
        "server": acc.server
    }

if __name__ == "__main__":
    # Simulate a check before healing
    from heartbeat_monitor import check_heartbeat
    pulse = check_heartbeat()
    
    if pulse["status"] != "HEALTHY":
        print(f"Pulse: {pulse['status']} - Attempting Heal...")
        recovery = attempt_recovery()
        print(json.dumps(recovery, indent=2))
    else:
        print("System Healthy. No healing required.")
    mt5.shutdown()
