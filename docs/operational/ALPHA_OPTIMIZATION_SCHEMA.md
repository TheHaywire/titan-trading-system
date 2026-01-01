# Institutional Performance Optimization (Growth Architecture)

This document outlines how the system is aligned to prioritize account growth and capital preservation through the `AlphaOptimizer` and `AllocationAgent`.

## 1. Dynamic Regime Alignment
The system no longer forces a single strategy. Instead, it analyzes the market heartbeat and selects the "Strategy of Best Fit":

| Market Regime | Detection Metric | Strategy Assigned | Objective |
| :--- | :--- | :--- | :--- |
| **Strong Trend** | ADX > 25, Price > EMA | InstitutionalGold / TrendSurfer | Ride the momentum for max pips. |
| **Mean Reversion** | RSI < 30 or > 70 | MeanReversion / MomentumScalper | Harvest volatility on over-extensions. |
| **High Volatility** | BB Width > Mean | LiquidityHunter / RegressionSurfer | Capture liquidity sweeps and arb gaps. |
| **Low Volatility** | Score < Threshold | **HOLD (No Trade)** | Preserving capital in "Death Zones". |

## 2. The Scaling Multiplier (Account Growth Use Case)
To achieve aggressive account growth, the system implements a "Winner-Scaling" logic in the `AllocationAgent`:

- **Initial Risk**: Base risk (e.g. 1.5%) scaled by Signal Confidence.
- **Scaling Trigger**: If a symbol's historical performance in the `trades` database shows an **Expectancy > $200**, the allocation is boosted by **1.5x**.
- **The Result**: The system automatically funnels more capital into symbols and strategies that are proven winners on the live broker account.

## 3. Preservation Safeguards
- **Circuit Breaker**: Active drawdown monitoring to stop the engine if loss thresholds are hit.
- **Kill Switch**: Institutional-grade safety for news events and black-swan events.
- **Self-Audit**: Automatic 4-hour audit that blacklists any symbol with a negative expectancy (Account Killers).

**Focus**: Growth through statistical edge, not luck.
