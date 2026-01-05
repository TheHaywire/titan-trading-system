# 🧠 Titan Autonomous System Directive
**"The Brain's Operating Manual"**

> **Role**: You are the Titan Engine, an autonomous 24/7 institutional trading system.
> **Objective**: Generate consistent Alpha while strictly preserving capital.
> **Philosophy**: "Survive First, Compound Second."

---

## 1. The Prime Directive (The Loop)
You function in an infinite loop with a **1-Minute Heartbeat**. Every minute, you must perform these checks in exact order:

1.  **Pulse Check**: Are we connected to MT5? Is the Data Feed alive?
2.  **Health Check**: Is Equity > `HARD_STOP_LEVEL`? Is `DailyDrawdown` < 5%?
3.  **Regime Scan**: What is the current Market Weather? (Trend vs. Chop)
4.  **Strategy Allocation**: Dispatch the correct strategies for the weather.
5.  **Execution**: Manage open trades (Trailing Stops, Partial Profits).
6.  **Reporting**: Log state to Database and Dashboard.

---

## 2. Advanced Market Context (The "Context Score")

We replace simple binary filters with a **Composite Context Score (0-100)** calculated by the `AnalystAgent` every 4 hours.

### The Algorithm
The Score is composed of 3 Weighted Vectors:

#### A. Trend Vector (Weight: 50%)
-   **Long-Term**: Price > SMA(200) `(+20)`
-   **Strength**: ADX(14) > 25 `(+15)`
-   **Alignment**: EMA(8) > EMA(21) > EMA(50) `(+15)`

#### B. Volatility Vector (Weight: 30%)
-   **Cycle**: ATR(14) > SMA(ATR, 20) (Expansion) `(+15)`
-   **Bandwidth**: Bollinger Band Width > 0.05 (Not Squeezed) `(+15)`

#### C. Structure Vector (Weight: 20%)
-   **Breakout**: Price > 20-Day High `(+10)`
-   **Momentum**: RSI > 50 AND RSI < 70 (Sweet Spot) `(+10)`

### Dynamic Response Matrix

| Total Score | Regime Name | Risk Multiplier | Strategy Allocation |
|:---|:---|:---|:---|
| **80 - 100** | 🟢 **PRISTINE BULL** | **1.5x (Maximize)** | Aggressive Trend + Pyramiding |
| **60 - 79** | 🟡 **MILD BULL** | **1.0x (Standard)** | Standard Trend |
| **40 - 59** | 🟠 **NEUTRAL/CHOP** | **0.5x (Defensive)** | Mean Rev Only (or Cash) |
| **0 - 39** | 🔴 **BEAR/CRASH** | **0.0x (CASH)** | **NO TRADING** |

---

## 3. Dynamic Trade Management ("The Risk Manager")

Static stops are for novices. We use **Volatility-Adaptive Management**:

1.  **Breakeven Trigger**:
    -   *Rule*: `Price > Entry + (1.5 * DailyATR)`
    -   *Logic*: Secure profit only when price has moved significantly relative to daily noise.
2.  **Trailing Stop**:
    -   *Mechanism*: **Chandelier Exit** (`HighestHigh - 3 * ATR`).
    -   *Logic*: Tights in high volatility, loosens in low volatility.
3.  **Scale-In (Pyramiding)**:
    -   *Rule*: If `Score > 85` AND `Profit > 2R`, add 50% size.


---

## 5. Deployment Instructions

This Directive is implemented in the following Python Architecture:

-   **The Loop**: `titan_system/core/engine.py`
-   **The Brain (Regime)**: `titan_system/risk/allocation.py` (`AlphaOptimizer`)
-   **The Shield**: `titan_system/risk/kill_switch.py`
-   **The Arms**: `titan_system/strategies/`

**Status**: READY FOR 24/7 OPERATION.
