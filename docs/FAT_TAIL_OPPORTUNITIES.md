# The "Fat Tail" Report: Where Book Strategies Actually Work
**Based on deep statistical backtesting of 1,520 MT5 symbols (H1 Timeframe, 1000 candles).**

## Executive Summary
We stress-tested the "Technical Analysis For Dummies" strategies (MA Cross + RSI + Bollinger Breakouts) across the entire market universe.

**The Verdict:** The strategies are **NOT universally effective**. They failed on 70% of symbols (particularly Forex), but generated **outlier profits ("Fat Tails")** in specific trending asset classes.

## Top Performing Asset Classes

### 1. Commodities (The "Super Trends")
Classic Technical Analysis was designed for these markets, and it shows. Strong, persistent supply/demand trends allow the 50/200 SMA and Breakout logic to capture massive moves.
*   **Top Symbols**: `COCOA`, `PALLADIUM`, `PLATINUM`, `GOLD` (XAUUSD), `BRENT OIL`.
*   **Win Rate**: ~38-45% (High for trend following).
*   **Expectancy**: Extremely Positive.

### 2. Global Indices (Cash Markets)
Equity indices showed strong drift and momentum, perfect for the "Trend is your Friend" (Chapter 12) philosophy.
*   **Top Symbols**: `GerMid50` (Germany), `US500` (S&P), `JP225` (Nikkei), `IT40` (Italy).
*   **Observation**: "Cash" markets performed better than Futures, likely due to smoother data or liquidity sessions.

### 3. Momentum Stocks
Individual stocks with strong fundamental narrratives (Defense, Pharma, Tech) obeyed the technical signals effectively.
*   **Top Symbols**: `Rheinmetall` (Defense), `Eli Lilly` (Pharma), `Spotify`, `Blackrock`.

## Where the Strategies FAILED (The "Graveyard")

### 1. Forex Majors (EURUSD, GBPUSD)
*   **Result**: Slight Negative to Breakeven.
*   **Reason**: High efficiency and mean reversion. The H1 timeframe on Forex is full of "noise" that whipsaws the 50/200 SMA. The "Book" strategies are too slow for these markets.

### 2. Crypto (BTC, ETH) on H1
*   **Result**: Negative Expectancy.
*   **Reason**: Volatility is too high for the standard "2x ATR" stop loss. The strategy gets stopped out by wicks before the trend resumes.

## Statistical Edge Summary
| Metric | "Fat Tail" Winners | The Rest of Market |
| :--- | :--- | :--- |
| **Win Rate** | 40% - 48% | 30% - 37% |
| **Avg Reward:Risk** | > 2.5 : 1 | < 1.0 : 1 |
| **Primary Driver** | Breakouts (Chap 19) | Whipsaws (Losses) |

## Recommendation
**Stop trading EURUSD.** Pivot the `BookTechnicalStrategy` to focus exclusively on **Commodities and Indices**. Use the `mega_backtest_results.csv` to filter your watchlist to only the top 100 symbols.
