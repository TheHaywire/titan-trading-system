---
name: Alpha Research & Validation Lab
description: Institutional-grade strategy validation, walk-forward analysis, and regime-aware testing.
---

# Alpha Research Skill

This skill provides the "Truth Layer" for all trading strategies. Follow these protocols to move any strategy from "Idea" to "Production":

### 1. The WFA Protocol (Walk-Forward Analysis)
No strategy is considered institutional if it only works on historical "backtest" data.
- **5-Fold split**: Every strategy must be tested across at least 5 walk-forward windows.
- **IS/OOS Ratio**: Use 80% In-Sample (IS) for optimization and 20% Out-Of-Sample (OOS) for validation.
- **Robustness Score**: A strategy passes if its OOS performance (Profit Factor/Sharpe) is within 20% of its IS performance.

### 2. Sensitivity Protocol
- Call `scripts/sensitivity_analyzer.py` to stress-test parameters.
- **The "Dead Zone" Check**: If shifting a parameter (e.g., Moving Average period) by +/- 1 period causes the strategy to fail, it is curve-fitted and must be REJECTED.

### 3. Regime Awareness
- Every alpha must specify its "Natural Regime" (Trending, Mean-Reverting, or Volatility-Expansion).
- Call `Regime Scout` (Sub-skill) to verify the strategy only runs during its alpha-positive window.

## Core Tools:
- `scripts/wfa_engine.py`: Multi-fold Walk-Forward validator.
- `scripts/sensitivity_analyzer.py`: Parameter stress-tester.
- `scripts/regime_scout.py`: HMM-based market state classifier.
