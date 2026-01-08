---
description: Generate comprehensive institutional-grade market analysis for any symbol
---

# Institutional Market Analysis Generator

Generate a comprehensive multi-timeframe market analysis report with professional-grade insights.

## Usage

```
/analyze [SYMBOL]
```

**Examples:**
- `/analyze XAUUSD` - Analyze Gold
- `/analyze BTCUSD` - Analyze Bitcoin
- `/analyze EURUSD` - Analyze EUR/USD
- `/analyze US100` - Analyze NASDAQ 100

## What It Does

This workflow generates a detailed institutional-grade analysis including:

✅ **Multi-Timeframe Analysis** (1M, 5M, 15M, 30M, 1H, 4H, 1D, 1W)
✅ **Technical Indicators** (RSI, Moving Averages, ATR, ADX, Bollinger Bands)
✅ **Trend Structure** (Higher highs/lows, trendline analysis)
✅ **Support & Resistance Levels** (Clustered key levels)
✅ **Chart Pattern Detection** (Double tops/bottoms, consolidations)
✅ **Divergence Detection** (RSI/Price divergences)
✅ **Fibonacci Levels** (Retracements and extensions)
✅ **Confluence Zones** (Where multiple levels overlap)
✅ **Market Regime Detection** (Trending, ranging, breakout)
✅ **Trading Signal Generation** (Buy/Sell signals with reasoning)
✅ **Actionable Recommendations** (Entry zones, stop loss, take profit)

## How to Run

// turbo
1. Execute the institutional market analyst script with your desired symbol
```bash
python scripts/institutional_market_analyst.py XAUUSD
```

The analysis report will be automatically saved to the `analysis/` directory with a timestamp and opened for your review.

## Output

- **Location**: `analysis/SYMBOL_YYYYMMDD_HHMMSS.md`
- **Format**: Rich markdown with tables, alerts, and structured insights
- **Sections**:
  - Executive Summary (multi-timeframe trend table)
  - Detailed Timeframe Analysis (1W → 1M)
  - Confluence Zones (high probability areas)
  - Trading Strategy Recommendations
  - Risk Management Guidelines

## Tips

- Run this before major trading decisions
- Compare multiple timeframes for confirmation
- Pay special attention to confluence zones
- Use higher timeframes (1W, 1D, 4H) for overall bias
- Use lower timeframes (1H, 15M) for precise entries
