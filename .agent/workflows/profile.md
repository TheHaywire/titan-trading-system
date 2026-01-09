---
description: Generate institutional-grade intelligence report on any symbol
---

# Symbol Intelligence Profiler

Generate comprehensive deep-dive analysis on any symbol with historical stats, time patterns, volatility profiling, and trading intelligence.

## Usage

```
/profile [SYMBOL]
```

**Examples:**
- `/profile GOLD` - Complete intelligence report on GOLD
- `/profile BTCUSD` - Full analysis of Bitcoin
- `/profile EURUSD` - Forex pair deep-dive

## What It Does

Comprehensive symbol analysis:

✅ **Price History Analysis**
- All-time high/low
- Distance from ATH
- YTD performance
- Maximum drawdown
- Average daily range

✅ **Time-Based Pattern Analysis**
- Best/worst hours to trade (UTC)
- Best/worst days of week
- Hourly return statistics
- Optimal trading windows

✅ **Volatility Profiling**
- ATR analysis (average & current)
- Volatility regime classification
- High/low volatility periods
- Risk recommendations

✅ **Trading Intelligence**
- Optimal stop loss %
- Recommended take profit multiplier
- Best timeframe for this symbol
- Actionable trading recommendations

## How to Run

// turbo
1. Generate complete symbol profile
```bash
python scripts/symbol_profiler.py GOLD
```

Output: `intelligence/GOLD_PROFILE_YYYYMMDD_HHMMSS.md`

## Example Output

```markdown
# 📊 COMPLETE SYMBOL PROFILE: GOLD

## Executive Summary
- **Current Price**: $4,472.52
- **Avg Daily Range**: 1.21%
- **Volatility State**: NORMAL
- **Recommended SL**: 2.0%
- **Best Timeframe**: 4H

## 📈 Price History
- **All-Time High**: $4,549.94
- **Distance from ATH**: -1.70%
- **YTD Return**: +31.15%
- **Max Drawdown**: -15.32%

## ⏰ Time-Based Patterns
**Best Hours** (UTC):
- 13:00 - Avg: +0.052% (NY open)
- 08:00 - Avg: +0.048% (London open)
- 14:00 - Avg: +0.041%

**Best Day**: Wednesday
**Worst Day**: Sunday

## 🎯 Trading Intelligence
✅ Normal volatility - Standard stops OK (2% SL)
📈 Near all-time high - Watch for resistance/continuation

**Optimal Strategy**:
- Stop Loss: 2.0%
- Take Profit: 3.0x Risk
- Best Timeframe: 4H
```

## Use Cases

### Pre-Trade Research
Before trading a new symbol, run `/profile` to understand:
- Historical behavior
- Best times to trade
- Appropriate risk parameters
- Optimal timeframe

### Portfolio Selection
Compare profiles of multiple symbols to find:
- Most predictable instruments
- Best risk/reward opportunities
- Symbols matching your schedule

### Strategy Optimization
Use profiler data to:
- Set appropriate stop losses per symbol
- Identify best trading hours
- Optimize timeframe selection

## Advanced Features

The profiler analyzes:
- **1 year of daily data** for long-term trends
- **1000 hours of 1H data** for intraday patterns
- **Statistical significance** in time patterns
- **Volatility regimes** for risk management

## Tips

- Run `/profile` monthly to update intelligence
- Compare profiles across asset classes  
- Use time patterns to avoid low-probability hours
- Adjust risk based on volatility state
- Trust the recommended timeframe for each symbol
