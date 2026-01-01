# Dual Momentum Strategy (Gary Antonacci)

## Category
**Momentum & Trend Following**

## Status
- Research: ✅ Complete
- Backtest: ⏳ Not Started
- Paper Trade: ⏳ Not Started
- Demo: ⏳ Not Started
- Live: ⏳ Not Started

## Hypothesis
**Assets exhibiting strong momentum (12-month returns > 0) tend to continue outperforming in the near term due to behavioral biases (under-reaction to news) and momentum cascades.**

## Edge Explanation
### Behavioral Finance Basis
- **Under-reaction**: Investors slowly incorporate new information
- **Herding**: Momentum attracts more buyers, creating self-fulfilling prophecy
- **Risk Premium**: Compensation for holding volatile trending assets

### Empirical Evidence
- Works across ALL asset classes (stocks, commodities, FX, crypto)
- 100+ years of data showing persistence
- AQR research: Sharpe ~0.7 per asset, >1.5 when diversified

## Instruments
### Primary (Best Suited)
- **XAUUSD** (Gold) - Strong trend persistence
- **BTCUSD** (Bitcoin) - Momentum beast
- **US500** (S&P 500) - Index momentum
- **NAS100** (Nasdaq) - Tech momentum

### Secondary
- Major FX pairs (EUR, GBP, JPY)
- Commodities (Silver, Oil, Copper)
- Individual growth stocks

### Avoid
- Range-bound currencies (EURCHF)
- Very low volatility assets
- Markets with>5% annual cost of carry

## Entry Rules
### Absolute Momentum (Signal 1)
1. Calculate 12-month CAGR: `(Current Price / Price_12mo_ago)^(12/12) - 1`
2. **Enter LONG** if 12-month return > 0%
3. **Exit to cash** if 12-month return ≤ 0%

### Relative Momentum (Signal 2 - Optional)
1. Compare asset's 12-month return vs S&P 500 (or cash equivalent)
2. **Hold asset** if it outperforms benchmark
3. **Switch to benchmark** if underperforms

### Dual Momentum (Combined)
**BUY** if:
- Asset 12-month return > 0% (Absolute) AND
- Asset 12-month return > Benchmark return (Relative)

**Action**: Go long with position sized based on recent volatility

## Exit Rules
### Primary Exit
- **Monthly Review**: Recalculate momentum score on last trading day of month
- **Exit Signal**: 12-month return turns negative
- **Action**: Close position, move to cash or next-ranked asset

### Stop Loss (Optional)
- 20% trailing stop from peak (for drawdown protection)
- ATR-based stop: Entry - (3 × ATR_20)

### Time-Based
- Minimum holding period: 1 month (avoid whipsaws)
- Maximum holding period: None (ride trends indefinitely)

## Position Sizing
### Base Allocation
- **Risk per trade**: 2% of account equity
- **Max position**: 50% of account in single asset

### Volatility Scaling
```python
target_volatility = 0.15  # 15% annualized
realized_vol = asset.std(252) * sqrt(252)
volatility_scalar = target_volatility / realized_vol
position_size = base_allocation * volatility_scalar
```

###Portfolio Approach
- Hold top 3 momentum assets (diversification)
- Equal weight or momentum-weighted
- Rebalance monthly

## Expected Performance
### Historical Backtests (Antonacci, 2014)
- **Win Rate**: ~45-50% (low, but...)
- **Avg R:R**: >2.5:1 (winners run far)
- **Sharpe Ratio**: 0.85 (single asset), 1.3 (diversified)
- **Max Drawdown**: 20-30% (acceptable for long-term)
- **Expectancy**: +12-15% CAGR over decades

### Target Metrics (Titan System)
- **Sharpe Target**: >1.0
- **Expectancy**: $150+ per trade
- **Max DD**: <25%
- **Win Rate**: >40%

## Research References
### Academic
- Antonacci, Gary (2014). *Dual Momentum Investing*. McGraw-Hill
- Jegadeesh & Titman (1993). "Returns to Buying Winners and Selling Losers"
- Moskowitz, Ooi, Pedersen (2012). "Time Series Momentum"

### Industry
- AQR Capital: "A Century of Evidence on Trend-Following Investing"
- Two Sigma: "Momentum Strategies Across Asset Classes"

### Books
- *Dual Momentum Investing* - Gary Antonacci (primary source)
- *Quantitative Momentum* - Wes Gray & Jack Vogel

## Implementation Notes
### Code Location
- `titan_system/strategies/dual_momentum.py`

### Dependencies
```python
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
```

### Data Requirements
- 12 months of historical daily prices minimum
- Monthly rebalancing calendar
- Benchmark data (S&P 500 or cash rate)

### Complexity
**Low** - Simple calculation, low turnover, easy to implement

### Pseudo-code
```python
def calculate_momentum(prices, lookback=252):
    if len(prices) < lookback:
        return None
    return_252d = (prices[-1] / prices[-lookback]) - 1
    return return_252d

def dual_momentum_signal(asset_prices, benchmark_prices):
    asset_mom = calculate_momentum(asset_prices)
    bench_mom = calculate_momentum(benchmark_prices)
    
    if asset_mom >0 and asset_mom > bench_mom:
        return "BUY"
    else:
        return "HOLD_CASH"
```

## Backtest Plan
### Data Period
- **Historical**: 2015-01-01 to 2024-12-31 (10 years)
- **Walk-Forward**: 2025-01-01 onwards (live data)

### Universe
- Gold (XAUUSD)
- Bitcoin (BTCUSD)
- S&P 500 (US500)
- Nasdaq (NAS100)

### Lookback
- Minimum: 252 trading days (12 months)
- Warm-up period: 300 days

### Benchmarks
- Buy & Hold Gold
- Buy & Hold S&P 500
- 60/40 Stock/Bond portfolio

### Metrics to Track
-Total Return, CAGR, Sharpe, Sortino, Max DD
- Monthly returns distribution
- Win/loss streaks
- Turnover rate

## Risk Considerations
### Market Regime Dependency
- **Works best**: Trending markets (2013-2021)
- **Struggles**: Choppy sideways markets (2022)
- **Solution**: Use absolute momentum to go to cash

### Liquidity Requirements
- **Monthly rebalancing**: Low turnover, execution straightforward
- **Slippage**: Minimal on major assets

### Slippage Sensitivity
- **Low**: Monthly exits mean you're not chasing ticks
- **Execution**: Can use limit orders

### Known Failure Modes
1. **Whipsaw**: Market trends reverse just after entry
   - *Mitigation*: Minimum 1-month hold, ATR filter
2. **Late to the party**: Enters after majority of move
   - *Mitigation*: This is a feature (avoiding false starts)
3. **Drawdowns during reversals**: 20-30% possible
   - *Mitigation*: Diversify across uncorrelated assets

### Psychological Challenges
- **Patience**: Can be out of market for months
- **Regret**: May miss first 20% of trend
- **Acceptance**: Drawdowns are part of the game

## Status Log
| Date | Update |
|------|--------|
| 2026-01-01 | Strategy documented, ready for backtest implementation |
| TBD | Backtest on Gold/BTC/SPX |
| TBD | Paper trade validation |

---

**Next Steps**: 
1. Implement `dual_momentum.py` strategy class
2. Create backtest script `scripts/backtests/backtest_dual_momentum.py`
3. Run 10-year backtest on 4 major assets
4. Review results and optimize if needed
5. Paper trade for 1 month before live deployment
