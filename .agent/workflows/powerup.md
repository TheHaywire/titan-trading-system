---
description: Power Up the Titan AI Institutional Stack (Sentinel, Intel, & Risk Engine)
---
1. **Activate Data Fabric (Intel)**
   Start the background intelligence service to monitor widespreads and news.
   `python titan_system/core/comprehensive_intel.py daemon`

2. **Activate Connectivity (API)**
   Start the API service for dashboard integration and external connectivity.
   `python scripts/api_service.py`

3. **Engage Autonomous Sentinel (AI Commander)**
   Launch the main AI trading loop. This activates the Institutional Feature Engine, Half-Kelly Risk Manager, and Automatic Pyramiding.
   `python scripts/autonomous_sentinel.py`

4. **Verify Brain State (Audit)**
   Run a one-time audit to confirm quantitative metrics (Hurst, OFI, Z-Scores) are live.
   `python scripts/debug_features.py`
