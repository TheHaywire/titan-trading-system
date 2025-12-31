# Titan Institutional Trading Playbook

This document defines the official "Rules of Engagement" for the Titan Trading System. The code is built to strictly follow this Playbook.

## Setup A: The Trend Surfer (Momentum Confluence)
*This is our primary edge. We look for established trends that are pausing before a second leg.*

### 1. Market Selection (The Grid)
*   **Symbols**: GOLD, EURUSD, BTCUSD, GBPUSD, USDJPY.
*   **Timeframes**: H4 (Master Trend), H1 (Trigger).

### 2. Entry Conditions (The Checklist)
For a **BUY** order, all of the following must be TRUE:
1.  **H4 Bias**: 20-period SMA is above 50-period SMA (The "Big Money" is buying).
2.  **H1 Trigger**: 10-period SMA crosses above 20-period SMA (The "Entry leg" has started).
3.  **Trend Power**: ADX is above 25 (The market is not ranging/choppy).
4.  **Momentum**: RSI is between 50 and 70 (Strong momentum, but not overbought).

### 3. Risk Management (The Fortress)
*   **Position Sizing**: 0.01 lots per $1,000 equity (Fixed for now).
*   **Stop Loss (SL)**: 50 pips (Set below the recent swing low).
*   **Take Profit (TP)**: 100 pips (2:1 Reward-to-Risk ratio).
*   **Daily Limit**: Maximum 2% total account drawdown. If hit, the bot shuts down for 24 hours.

### 4. Exit Rules
*   Exit on **Stop Loss** or **Take Profit**.
*   **Manual Override**: Exit immediately if the H4 trend flips (SMA Fast < SMA Slow).

## Setup B: Market Context (The Climate Filter)
*We do not trade just because a trend exists. We only trade when the "Data Heatmap" confirms the market is active.*

### 1. Power Hours (Actual 180-Day Data)
*   **Primary Power Hour**: 00:00 UTC (05:30 IST).
*   **Secondary Power Window**: 15:00 - 17:00 UTC (20:30 - 22:30 IST).
*   **The "Death Zone" (Statistically Worst)**: 23:00 UTC (04:30 IST). **No trades allowed.**

### 2. Volatility Speed (Relative Strength)
*   **Active**: Market must moving at >1.0x its 24-hour average speed.
*   **Thin/Slow**: If speed is <0.8x, the Score is slashed by 30%.

---

## The "Scanner" Workflow
Every hour, the System performs the following:
1.  **Context Audit**: Check current UTC hour against the **Power Hour Map**.
2.  **Scan**: Evaluate all symbols against the **Technical checklist**.
3.  **Score**: Apply **Context Penalties** (Death Zone / Low Volume).
4.  **Commit**: Execute ONLY for symbols with a **Score >= 80**.
