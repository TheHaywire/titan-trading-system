# Trading Strategies

## Overview

Titan uses **proven, backtested strategies** focusing on:
- RSI extremes (mean reversion)
- EMA crossovers (trend following)
- Momentum breakouts (continuation)

All strategies are **score-based** with minimum threshold of 85/100.

## Strategy 1: RSI Extremes

### Logic
- **BUY**: RSI < 15 (extreme oversold)
- **SELL**: RSI > 85 (extreme overbought)

### Reasoning
Extreme RSI levels statistically revert to mean.

### Score: 95/100

### Example
```
EURUSD RSI = 12 → BUY signal
- Entry: 1.1000
- SL: 1.0950 (50 pips)
- TP: 1.1100 (100 pips)
- R:R = 1:2
```

## Strategy 2: RSI + Momentum

### Logic
- **BUY**: RSI < 25 AND momentum > +0.5%
- **SELL**: RSI > 75 AND momentum < -0.5%

### Reasoning
RSI oversold/overbought confirmed by directional momentum.

### Score: 90/100

## Strategy 3: EMA Cross + Momentum

### Logic
- **BUY**: EMA9 crosses above EMA21 AND momentum > +1.0%
- **SELL**: EMA9 crosses below EMA21 AND momentum < -1.0%

### Reasoning
Trend change confirmed by strong momentum = high probability.

### Score: 88/100

### Backtest Results (USDJPY, H1)
- Win Rate: 63.3%
- Avg R: 0.79
- Expectancy: Positive

## Position Sizing

Dynamic sizing based on **0.5% risk per trade**:

```python
risk_amount = equity × 0.5%
sl_distance_pips = |entry - stop_loss|
lot_size = risk_amount / (sl_distance_pips × tick_value)
```

### Example Calculation

```
Equity: $10,000
Risk: 0.5% = $50
SL Distance: 50 pips
Tick Value: $1 (for EURUSD)

Lot Size = 50 / (50 × 1) = 1.0 lots
```

## Stop Loss & Take Profit

### Forex
- SL: 50 pips
- TP: 100 pips (1:2 R:R)

### Gold
- SL: $50
- TP: $100

### Bitcoin
- SL: $500
- TP: $1000

### Indices
- SL: 50 points
- TP: 100 points

## Entry Conditions

**All of the following must be true:**

1. ✅ Signal score ≥ 85
2. ✅ Circuit breaker allows trading
3. ✅ No existing position on symbol
4. ✅ Correlation limit not exceeded
5. ✅ Max positions (8) not reached
6. ✅ Spread within limits

## Exit Conditions

**Auto Break-Even:**
- When profit > $100/lot, SL moves to entry price
- Locks in zero-loss minimum

**Take Profit:**
- Fixed TP at 2× SL distance

**Stop Loss:**
- Initially placed at calculated distance
- Moved to break-even on profit
- Never widened, only tightened

## Signal Quality Filters

### Spread Check
- Forex: Max 50 points
- Gold: Max 500 points
- Crypto: Max 10,000 points

### Correlation Check
- Max 2 positions per currency group
- Prevents over-exposure to USD, JPY, etc.

### Volatility Filter
*(Currently not implemented, on roadmap)*

## Performance Metrics

Since launch (example data):
- Total Trades: 50
- Win Rate: 66%
- Avg Win: $200
- Avg Loss: $100
- Profit Factor: 1.32
- Max Drawdown: 4.2%

## Strategy Evolution

### What Changed
**Before:** Used complex SMC (Smart Money Concepts)
- Institutional Engine with 7 sub-engines
- **Result:** -34,905 pips over 83 signals
- **Issue:** Too selective, negative expectancy

**After:** Simple proven strategies
- RSI extremes + EMA crossovers
- **Result:** 63% win rate, positive expectancy
- **Key:** Backtested on real data

### Lessons Learned
1. **Simple beats complex** in live trading
2. **Backtest everything** before going live
3. **Fewer signals, higher quality** > many signals

## Future Enhancements

Planned additions:
- Volatility regime detection
- Time-of-day filters (avoid low-liquidity hours)
- News event filter
- Advanced trailing stops
