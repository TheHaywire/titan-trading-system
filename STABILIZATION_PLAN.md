
# 🛠️ System Stabilization & Encoding Fix Plan

## 1. Issue Analysis: The `charmap` Error
**Symtoms**: Run-time crashes with `UnicodeEncodeError: 'charmap' codec...`
**Cause**: The Windows Command Prompt default encoding (often `cp1252`) crashes when trying to print modern emojis (🚀, 💰, 🛑) used in our "Rich" logging.
**Impact**: It blinds us to the system status and can crash the runner loop.

## 2. Proposed Solution
We will implement a 3-layer fix to ensure the system is "Emoji Safe" and stable on Windows:

### Layer 1: Global Encoding Enforcer
We will modify the entry points (`unified_runner.py` and `backend/app.py`) to forcibly reconfigure standard output to UTF-8 at startup.
```python
import sys
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
```

### Layer 2: Logger Configuration
Update `titan_system/core/engine.py` logging configuration to explicitly using `FileHandler(..., encoding='utf-8')` to prevent log file corruption.

### Layer 3: "Safe Mode" Printing
Create a utility function `safe_print()` that strips emojis if the terminal doesn't support them, ensuring the bot never crashes just because it tried to look cool.

---

## 3. Implementation Steps

### Step 1: Fix Entry Points
- [ ] Modify `unified_runner.py`
- [ ] Modify `backend/app.py`
- [ ] Modify `scripts/status_report.py` (Finalize)

### Step 2: System Health Check
- [ ] Run `status_report.py` (successfully this time) to confirm:
    1.  Net Profit Today (Did we make money after the cleanup?)
    2.  Active Positions (Is the new "Aggressive" strategy firing?)

### Step 3: Verify "Aggressive" Growth
- [ ] Check `titan_system/strategies/institutional_gold.py` logs to see if it triggers.
- [ ] If no trades yet, verify `Check Today's Trades` to ensuring we aren't missing signals due to data feed lag.

## 4. User Deliverable
A clean, crashing-free "Status Report" showing exactly how much PnL we realized today including the cleanup costs.
