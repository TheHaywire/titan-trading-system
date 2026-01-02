# Phase 4 Deployment Guide: Titan Autonomous Engine

## 🚀 Mission Status: READY FOR LAUNCH
The **Titan System** has transitioned from Research to **Autonomous Execution**.
The "Brain" (`launch.py`) is live and operational in Paper Mode.

### 1. Launch Protocol
To activate the 24/7 Autonomous Engine:

```powershell
python scripts/launch.py --mode=paper
```

> [!NOTE]
> Ensure your MT5 Terminal is open and "Allow WebRequest" is enabled for news/calendar (optional).

### 2. The Command Center (Dashboard)
The terminal will transform into a Real-Time UI:

-   **Alpha Intelligence (Left Panel)**:
    -   **Context Score (0-100)**: The "Expert Opinion" of the market.
        -   `> 80`: **PRISTINE BULL** (Aggressive Accumulation)
        -   `40 - 79`: **NEUTRAL/MILD** (Standard/Defensive)
        -   `< 40`: **BEAR/CHOP** (Cash/Flat)
    -   **Regime**: The current classification (Trend vs Chop).

-   **Risk Manager (Right Panel)**:
    -   Real-time Equity, Balance, and Open Speculative Positions.

### 3. Strategy Arsenal (UNIVERSE MODE)
The Engine now scans **1500+ Symbols** every 4 hours to find the "Top 50 In-Play Lists".

1.  **Forex/Crypto**:
    -   **Strategy**: `LiveCryptoTrend` (Generic Trend)
    -   **Logic**: Applied to any pair (EURUSD, BTCUSD, etc.) showing strong ADX trends.

2.  **Commodities/Indices**:
    -   **Strategy**: `LiveGoldBreakout` (Generic Breakout)
    -   **Logic**: Applied to Gold, Silver, Nasdaq, etc. during volatility expansion.

**Universe Scanner**:
-   **Gatekeeper**: Filters 1500 -> 50 based on Volume, Spreads, and Daily % Move.
-   **Active Watchlist**: Displayed in the Dashboard header.


### 4. Verification Checklist (First 1 Hour)
- [ ] **Heartbeat**: Does the dashboard update every 60 seconds?
- [ ] **Data Flow**: Are scores calculated (not 50/Neutral)?
- [ ] **Regime**: Does the regime match your visual assessment?
- [ ] **Orders**: If signals trigger, are they visible in "Open Positions"?

---

> [!IMPORTANT]
> To stop the engine, press `Ctrl+C` in the terminal.
> For full logs, check `data/titan_engine.log`.
