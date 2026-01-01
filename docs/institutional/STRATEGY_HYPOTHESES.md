# 🧠 Strategy Hypotheses & Methodology (EPIC-06)

This document defines the core hypotheses and multi-agent architecture for the Titan system.

## 1. Active Strategy Hypotheses

### [H-01] Institutional GOLD Momentum
- **Hypothesis**: Gold (XAUUSD) exhibits strong multi-timeframe trend persistence during London/New York overlap.
- **Logic**: Use H4 Bias -> H1 Zones -> M15 Trigger.
- **Expected R:R**: 3:1
- **Validation**: Backtest shows >60% win rate on 1:1, dropping to 35% on 3:1.

### [H-02] Mean Reversion (Book Style)
- **Hypothesis**: High-liquidity assets (EURUSD, US100) revert to the 200-period EMA after a 2.5 Standard Deviation stretch.
- **Logic**: Bollinger Band breakout with RSI confirmation.
- **Expected R:R**: 1.5:1
- **Validation**: Verified against Ernest Chan's momentum/mean-reversion principles.

---

## 2. Multi-Agent Architecture Design

To scale to institutional capital, the system is moving towards an **Agentic Split**:

### 🛰️ Prediction Agent (Brain)
- **Role**: Analyzes technical and sentimental data.
- **Output**: Directional Bias (-1 to +1) and Confidence Score.

### 🛡️ Allocation Agent (Risk Manager)
- **Role**: Receives Bias from Prediction Agent.
- **Logic**: Calculates optimal lot size based on **Kelly Criterion** and current **Value at Risk (VaR)**.
- **Safety**: Can override Prediction Agent if account exposure is >5%.

### ⚡ Execution Agent (The Arm)
- **Role**: Executes orders with IOC (Immediate or Cancel) filling mode.
- **TCA**: Logs slippage and latency for post-trade analysis.
