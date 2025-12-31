# Assumption Audit: Data vs. "Expert" Generalizations

This document cross-checks my initial assumptions (generic trading knowledge) against the actual **180-day audit of GOLD (XAUUSD)**.

### 🚩 Discovered Discrepancies

| Assumption | My Initial Claim | Data Reality (180-Day XAUUSD) | Verdict |
| :--- | :--- | :--- | :--- |
| **Tokyo Session** | "Usually Quiet / Range-bound" | **00:00 UTC (05:30 IST)**: 34.4 Pips (Highest of Day) | **WRONG**. Tokyo Open is a major power spike for Gold. |
| **London Open** | "Often the Big Fake-out / Volatile" | **08:00 UTC (13:30 IST)**: 11.4 Pips (Below Average) | **WEAK**. London open is surprisingly tame compared to Asian open. |
| **NY Open** | "The Real Move / Heavy Volatility" | **13:00 UTC (18:30 IST)**: 10.2 Pips (Low Volatility) | **DELAYED**. The move starts later (15:00 UTC / 20:30 IST). |
| **"Death Zone"** | *I assumed 23:00 was just quiet.* | **23:00 UTC (04:30 IST)**: 7.0 Pips (Absolute Floor) | **CONFIRMED**. It is statistically the worst time to trade. |

### 🛠️ Strategic Corrections
1.  **Pivoting the "Power Hours"**: We will move the "High Priority" scanning window to **00:00 UTC (05:30 IST)** to catch the real Gold movers.
2.  **London/NY Slump**: We will avoid over-aggressiveness at the 13:00 NY open and wait for the **15:00 UTC** acceleration.
3.  **Dynamic Filtering**: The bot will no longer rely on my "Session Labels." It will use the **Hourly Volatility Map** directly to determine if a score should be penalized.

**Conclusion**: The data proves that Gold is an "Asian Session Beast," contradicting several generic Forex assumptions.
