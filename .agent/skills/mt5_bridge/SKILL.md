---
name: MT5 Bridge & Connectivity
description: Foundation layer for identity verification, noise filtering, and environment awareness.
---

# MT5 Bridge Skill

This is my **mandatory foundation layer**. Use this protocol before calling any other trading skill (`alpha_forensics`, `factor_risk`, etc.).

### 1. Identity Verification Protocol
Before performing any analysis:
- Call `scripts/connectivity_manager.py`.
- Confirm `Login`, `Server`, and `TradeMode` (Demo/Live).
- **If the account doesn't match the user's expected context, ALERT the user before proceeding.**

### 2. The "Institutional Filter" Protocol
To prevent "Data Pollution":
- Always use `scripts/history_cleaner.py` to isolate institutional trades.
- **Ignore Magic 0 (Manual)** trades unless explicitly asked to audit them.
- Focus on `Magic 888888` (Fleet) and `Magic 999000+` (Titan Alpha).

### 3. Resilience & Pulse Protocol
Before long-running operations or high-frequency execution:
- Call `scripts/heartbeat_monitor.py` to verify RTT latency is < 200ms.
- If status is `CRITICAL`, call `scripts/auto_healer.py` to attempt session restoration.
- **NEVER** execute a trade if the Pulse is not `HEALTHY`.

### 4. Data Layer Sentinel Protocol
To ensure data durability and auditability:
- Call `scripts/db_sentinel.py` daily to audit schema integrity and perform vacuuming.
- Log **EVERY** significant event using `scripts/audit_trail_manager.py`. The "details" field should be a rich JSON for forensic playback.
- **NEVER** overwrite database files directly; use the Sentinel for schema updates.

## Core Tools:
- `scripts/connectivity_manager.py`: Status and Identity check.
- `scripts/history_cleaner.py`: Noise reduction for trade history.
- `scripts/heartbeat_monitor.py`: Pulse and Latency check.
- `scripts/auto_healer.py`: Automated connection recovery.
- `scripts/db_sentinel.py`: Database maintenance.
- `scripts/audit_trail_manager.py`: Institutional execution ledger.
