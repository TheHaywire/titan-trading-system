---
name: Alpha Forensics & Decay Scout
description: Institutional-grade monitoring of alpha exhaustion, execution capacity, and regime drift.
---

# Alpha Forensics & Decay Scout Skill

When this skill is active, you should follow these protocols to provide hedge-fund level insights:

### 1. Alpha Decay Protocol
Use `scripts/alpha_decay_monitor.py` to audit trade history.
- **Look for TTP (Time-to-Profit) Expansion**: If trades are taking longer to hit targets than during backtests, warn the user about "Alpha Exhaustion."
- **Excursion Analysis**: Analyze MFE (Max Favorable Excursion) vs MAE (Max Adverse Excursion). If trades frequently go deep into MAE before hitting TP, the stop-loss is "loose" and the edge is inefficient.

### 2. Execution Quality Protocol
Use `scripts/capacity_analyzer.py` to analyze symbol liquidity.
- **Slippage Forecasting**: Before the user deploys larger capital, run a capacity check to see when slippage will start "eating" the Alpha.
- **Toxic Flow Detection**: Compare MT5 fills against the mid-price at execution time.

### 3. Regime Drift Protocol
- If a strategy stops performing, do not just suggest "turning it off."
- Research if the underlying market regime (ADX/ATR) has drifted away from the strategy's "Golden Zone."

## Core Tools:
- `scripts/alpha_decay_monitor.py`: Forensic trade analysis.
- `scripts/capacity_analyzer.py`: LOB liquidity and slippage modeling.
