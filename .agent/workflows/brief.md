---
description: Generate a synthesized Institutional Daily Brief (Macro + Forensics + Technicals)
---

This workflow provides a high-level executive summary of the trading day.

### Steps:

1. **Trade Audit**: The system runs `scripts/trade_auditor.py` to get the latest performance data.
2. **Strategy Sync**: The system runs `scripts/daily_brief_generator.py` to identify the Top 3 Matrix Focus assets.
// turbo
3. **Macro Synthesis**: The AI researches today's top market-moving news (CPI, Retail Sales, Fed) and correlates it with symbol volatility.
4. **Final Report**: The AI generates a professional debrief in a markdown artifact and notifies the user.

### Usage:
- `python scripts/daily_brief_generator.py` : Generic Brief (Matrix Focus + Performance)
- `python scripts/daily_brief_generator.py GOLD`: Institutional Intelligence Brief for Gold (Regime/OFI/Imbalance)
