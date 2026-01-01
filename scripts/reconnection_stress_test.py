"""
Reconnection Stress Tester (EPIC-05)
Simulates continuous disconnection and reconnection to MT5 
to verify bridge robustness and error recovery.
"""

import MetaTrader5 as mt5
import time
import sys
import os

def stress_test(iterations=10):
    print(f"🔄 Starting Reconnection Stress Test ({iterations} cycles)...")
    
    success_count = 0
    
    for i in range(iterations):
        print(f"\n[Cycle {i+1}/{iterations}]")
        
        # 1. Initialize
        if mt5.initialize():
            print(" - Connected ✅")
            
            # 2. Verify account access
            acc = mt5.account_info()
            if acc:
                print(f" - Account Verified ({acc.login}) ✅")
                
                # 3. Shutdown
                mt5.shutdown()
                print(" - Shutdown Sent ✅")
                
                # Verify shutdown
                if not mt5.terminal_info():
                    success_count += 1
                    print(" - Terminal Disconnected ✅")
                else:
                    print(" - ⚠️ Terminal still reporting info after shutdown!")
            else:
                print(" - ❌ Failed to get account info")
                mt5.shutdown()
        else:
            print(" - ❌ Initialization Failed")
            
        time.sleep(1) # Wait between cycles

    print("\n📊 [STRESS TEST RESULTS]")
    print(f"- Total Cycles: {iterations}")
    print(f"- Successful Reconnections: {success_count}")
    
    if success_count == iterations:
        print("\n✅ SUCCESS: Reconnection bridge is 100% robust.")
    else:
        print(f"\n⚠️ WARNING: {iterations - success_count} failure(s) detected. Check terminal logs.")

if __name__ == "__main__":
    stress_test(10) # 10 for quick validation, institutional docs suggest 50
