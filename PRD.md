# Product Requirements Document (PRD)
## Project Name: TITAN QUANTITATIVE TRADING SYSTEM (v2.0)
**Date:** 2025-12-09
**Status:** DRAFT
**Author:** Antigravity (AI System Architect)

---

## 1. Product Vision
To build a **professional-grade, semi-automated trading system** that bridges the gap between discretionary institutional trading and quantitative automation. The system will eliminate emotional decision-making, enforce strict risk management, and provide clear, "Glass Box" visibility into why trades are taken.

**It is NOT:** A "Black Box" money printer.
**It IS:** A sophisticated toolset for a serious trader to execute high-probability setups with consistency.

---

## 2. User Persona
**The User:** A sophisticated retail trader recovering from significant losses.
**Goals:**
*   Consistent, compounding growth (Target: 5-10% monthly).
*   Absolute protection of capital (Risk of Ruin ~ 0%).
*   Understanding the "Why" behind every trade.
**Pain Points:**
*   Complexity of managing multiple timeframes (H4/H1/M5).
*   Emotional trading during volatility.
*   "Black Box" confusion (not knowing what the bot is doing).

---

## 3. Core Philosophy: "The Hierarchy of Truth"
The system will be architected around a strict hierarchical decision model, not random indicators.
1.  **Strategic Layer (H4)**: Determines BIAS (Long/Short/Neutral).
2.  **Tactical Layer (H1)**: Identifies ZONES (Liquidity Pools, Supply/Demand).
3.  **Execution Layer (M5/M15)**: Identifies TRIGGERS (Price Action, Order Flow).

*Rule: Detailed execution only occurs when Strategic and Tactical layers align.*

---

## 4. Functional Requirements

### 4.1. The Data Engine
*   **Real-time Feed:** Connect to MT5 for tick-by-tick data on GOLD (XAUUSD).
*   **Data Validation:** Check for stale ticks or connection drops.
*   **Multi-Timeframe Sync:** Maintain synchronized buffers for M5, M15, H1, H4.

### 4.2. The Analytic Engine (Alpha Models)
*   **Module A: Smart Money Concepts (SMC)**
    *   Detect Liquidity Sweeps (High/Low of prev day/week).
    *   Detect Order Blocks & FVGs.
*   **Module B: Statistical Mean Reversion**
    *   Linear Regression Channel (Z-Score).
    *   VWAP Deviations.
*   **Synthesis:** Combine A & B. (e.g., "A Sweep of Liquidity [A] occurring at 2.0 Sigma Deviation [B]").

### 4.3. The Execution Engine
*   **Trade Management:**
    *   Auto-calculation of Lot Size based on % Risk (Kelly Criterion).
    *   Auto-placement of Hard Stop Loss and Take Profit.
    *   **Trait:** "Breakeven Protocol" (Move SL to entry after X points).
*   **Modes:**
    *   *Fully Auto:* specific setups (e.g., Night Scalping).
    *   *Semi Auto:* User approves signal via Telegram/Email.

### 4.4. Risk Management (The "Circuit Breaker")
*   **Account Level:**
    *   Daily Loss Limit (Hard stop at -3%).
    *   Max Drawdown Limit.
*   **Trade Level:**
    *   Risk per trade capped at 1.0% (Configurable).
    *   Max Open Positions: 1 (Focus).

---

## 5. Non-Functional Requirements
*   **Transparency:** Every signal must generate a "Trade Card" explaining:
    *   "Why I am entering" (Narrative).
    *   "Where I am wrong" (Stop Loss Rationale).
*   **Reliability:** System must auto-recover from crashes.
*   **Latency:** Analysis to Execution < 1 second.

---

## 6. Development Roadmap

### Phase 1: Foundation Clean-up (Current-Next 48h)
*   **Archive:** Move all old/failed scripts to `legacy/`.
*   **Structure:** Create pure `src/` directory with clean architecture.
*   **Driver:** Build the `TitanService` class (The main daemon).

### Phase 2: The "Glass Box" Dashboard
*   Build a simple Localhost Web Dashboard (Streamlit or Flask).
*   Visualize the "Hierarchy of Truth" (H4 Bias, H1 Zones) in real-time.
*   User can see the "Brain" thinking.

### Phase 3: Live Testing
*   Deploy "Module A" (Liquidity Sweeps) on Minimum size (0.01).
*   Verify execution speed and logging.

### Phase 4: Scaling
*   Increase lot size based on performance metrics (Sharpe Ratio > 1.5).

---

## 7. Metrics for Success
*   **Profit Factor:** > 1.5
*   **Max Drawdown:** < 5%
*   **User Confidence:** User stops asking "what is it doing?"

---
*Approved by:* _________________ (User)
