---
name: Factor Risk & Adversarial Simulator
description: Institutional-grade management of systemic risk, hidden correlations, and black-swan stress testing.
---

# Portfolio Risk Skill

This skill is the "Shield" of the Titan system. Its only job is SURVIVAL. Follow these protocols for every active portfolio:

### 1. The Dynamic Sizing Protocol
Institutional sizing is never static.
- Call `scripts/dynamic_kelly_allocator.py` whenever a new alpha signal is received.
- **Correlation Penalty**: If the new symbol has a correlation > 0.7 with active positions, REDUCE the suggested volume by 50%.
- **Equity Kill-Switch**: If the daily drawdown exceeds 5%, BLOCK all new entries regardless of alpha strength.

### 2. Adversarial Protocol
- Call `scripts/adversarial_simulator.py` weekly.
- **Monte Carlo Chaos**: Randomize execution slippage, latency, and spreads to see if the strategy remains profitable under "Worst Case" conditions.
- **Black Swan Shocks**: Simulate events like the 2015 SNB Crash or 2020 Covid Gap on current positions.

## Core Tools:
- `scripts/factor_exposure_auditor.py`: PCA-based correlation auditor (DONE).
- `scripts/black_swan_tester.py`: Historical shock simulator (DONE).
- `scripts/dynamic_kelly_allocator.py`: Correlation-adjusted sizing logic.
- `scripts/adversarial_simulator.py`: Monte Carlo chaos engine.
