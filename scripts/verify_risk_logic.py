
import sys
import os
sys.path.append(os.getcwd())

from titan_system.risk.position_sizer import KellyPositionSizer

print("🛡️ Verifying Risk Management Logic (Fixed Fractional 1%)...")

sizer = KellyPositionSizer()
equity = 10000.0
risk_pct = 1.0 # $100 Risk

# Case 1: XAUUSD (Gold)
# Entry: 2000, SL: 1998 (Diff $2.0)
# Loss per Lot (100oz) on $2 move = $200
# Expected Lots = $100 Risk / $200 Loss = 0.5 Lots
lots_gold = sizer.calculate_position_size(equity, "XAUUSD", 2000.0, 1998.0, risk_pct)
print(f"XAUUSD ($2.0 SL): {lots_gold} Lots (Expected: 0.5)")

if lots_gold == 0.5:
    print("✅ Gold Logic: PASSED")
else:
    print(f"❌ Gold Logic: FAILED (Got {lots_gold})")

# Case 2: EURUSD
# Entry: 1.1000, SL: 1.0990 (10 Pips)
# Loss per Lot (100k) on 10 pips = $100
# Expected Lots = $100 Risk / $100 Loss = 1.0 Lots
lots_euro = sizer.calculate_position_size(equity, "EURUSD", 1.1000, 1.0990, risk_pct)
print(f"EURUSD (10 Pip SL): {lots_euro} Lots (Expected: 1.0)")

if lots_euro == 1.0:
    print("✅ Euro Logic: PASSED")
else:
    print(f"❌ Euro Logic: FAILED (Got {lots_euro})")
