---
description: Backtest identified setups to validate the scoring system
---

# Setup Backtesting Engine

Test how identified setups would have performed historically to validate the quality scoring and analysis.

## Usage

```
/backtest [SYMBOL] [DAYS]
```

**Examples:**
- `/backtest GOLD 30` - Test GOLD setups over last 30 days
- `/backtest BTCUSD 90` - Test Bitcoin setups over 3 months
- `/backtest ALL 60` - Test all symbols over 2 months

## What It Does

Historical validation:

✅ **Analyzes Past Price Data** using same algorithm
✅ **Identifies Historical Setups** that would've been generated
✅ **Simulates Trades** with exact entry/SL/TP
✅ **Calculates Outcomes** (win/loss, P&L, R:R achieved)
✅ **Win Rate by Score** (validates scoring system)
✅ **Sharpe Ratio** and drawdown metrics
✅ **Best/Worst Setups** analysis
✅ **Generates Report** with statistics

## How to Run

// turbo
1. Run backtest for a symbol
```bash
python scripts/backtest_setups.py GOLD 30
```

Output: `backtest/GOLD_30days_YYYYMMDD.md`

## Backtest Report

```
📊 BACKTEST RESULTS: GOLD (30 Days)
Period: 2025-12-09 to 2026-01-09

Setup Statistics:
- Total Setups Identified: 23
- Setups Traded: 23
- Winners: 16 (69.6%)
- Losers: 7 (30.4%)
- Break-even: 0

Performance Metrics:
- Total P&L: +387 pips
- Avg Win: +42 pips
- Avg Loss: -28 pips
- Win/Loss Ratio: 1.5:1
- Avg R:R Achieved: 2.3:1
- Max Drawdown: -56 pips
- Sharpe Ratio: 1.85

By Quality Score:
8-10/10: 85% win rate (7 setups) ⭐
6-7/10: 67% win rate (12 setups)
4-5/10: 25% win rate (4 setups)

Validation: ✅ Scoring system is predictive!
```

## Analysis Features

### Setup Distribution
Shows when setups formed:
- Time of day
- Day of week  
- Market conditions

### Entry Quality
Analyzes entry execution:
- Slippage from ideal entry
- Fill rates
- Time to hit TP/SL

### False Signals
Identifies:
- Setups that didn't trigger
- Stopped out immediately
- Wrong direction

## Configuration

Edit `config/backtest.json`:
```json
{
  "commission_pips": 0.5,
  "slippage_pips": 0.2,
  "risk_per_trade_pct": 1.0,
  "starting_capital": 10000,
  "min_score": 5.0
}
```

## Validation Tests

### Score Validation
```bash
python scripts/backtest_setups.py --validate-scoring
```

Tests if higher scores → higher win rates.

### Pattern Validation
```bash
python scripts/backtest_setups.py --validate-patterns
```

Tests which patterns perform best.

### Timeframe Validation
```bash
python scripts/backtest_setups.py --validate-timeframes
```

Tests best timeframe combinations.

## Tips

- Run monthly to validate system
- Minimum 30 days for statistical significance
- Compare vs random entries (baseline)
- Use to calibrate score thresholds
- Identify best market conditions
