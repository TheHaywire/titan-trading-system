---
name: Execution Excellence & TCA
description: Minimizing slippage, benchmarking fills, and detecting toxic flow.
---

# Execution Excellence Skill

This skill provides the "Trading Desk" logic for the Titan system. Follow these protocols to ensure every pip of profit is captured:

### 1. The Execution Quality (TCA) Protocol
Trade signals are useless if lost to poor execution.
- Call `scripts/execution_quality_tca.py` after every session close.
- **Slippage Benchmark**: Compare the FILLED price vs the REQUESTED price.
- **Toxic Flow Check**: If the market immediately moves against the position by > 50% of ATR within 1 minute of fill, flag the broker for "Toxic Liquidity".

### 2. Adaptive Exit Protocol
- Use `scripts/adaptive_exit.py` to manage active positions.
- **Multi-Stage Scaling**: Never close a winner all at once. Scale-out at predefined RR (Risk-Reward) levels.
- **Vol-Trailing**: Trailing stops must expand during high-volatility news events to avoid "stop-hunting".

## Core Tools:
- `scripts/execution_quality_tca.py`: Fill quality auditor.
- `scripts/adaptive_exit.py`: Volatility-weighted trade manager.
- `scripts/liquidity_router.py`: Smart order slicing logic.
