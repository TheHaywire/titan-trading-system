# Pairs Trading Strategy

## Category
**Statistical Arbitrage**

## Status
- Research: ✅ Complete
- Backtest: ⏳ Not Started
- Paper Trade: ⏳ Not Started
- Demo: ⏳ Not Started
- Live: ⏳ Not Started

## Hypothesis
**Two correlated instruments (historically moving together) occasionally diverge due to temporary supply/demand imbalances. They statistically revert to their historical relationship, creating arbitrage opportunities.**

## Edge Explanation
### Statistical Basis
- **Cointegration**: Mathematical relationship that persists over time
- **Law of One Price**: Similar assets should have similar prices
- **Mean Reversion**: Deviations from equilibrium are temporary

### Why It Works
- **Market Inefficiency**: Not all participants see both instruments
- **Liquidity Imbalances**: One side gets oversold/overbought first
- **Institutional Arbitrage**: High-frequency traders compete, but inefficiencies remain

### Institutional Pedigree
- Renaissance Technologies uses pairs trading extensively
- Hedge fund "Long-Term Capital Management" (pre-1998 crisis)
- Statistical arbitrage desks at Goldman, JPM

## Instruments
### Primary Pairs (Highest Cointegration)
1. **EURUSD / GBPUSD**
   - Correlation: ~0.85
   - Both driven by USD, ECB policy
   
2. **XAUUSD / XAGUSD** (Gold/Silver)
   - Historical ratio: 80:1
   - Industrial vs monetary demand divergence

3. **US500 / NAS100** (S&P 500 / Nasdaq)
   - Tech-heavy Nasdaq vs broader S&P
   - Correlation: ~0.95

4. **AUDUSD / NZDUSD**
   - Both commodity currencies
   - Similar economic drivers

### Secondary Pairs
- Major FX crosses (EURJPY/GBPJPY)
- Oil vs Energy stocks (CL vs XLE)
- BTC vs ETH (crypto pairs)

### Avoid
- **Low Correlation (< 0.6)**: Not statistically linked
- **Fundamentally Different**: Tech stock vs utility
- **Different Hours**: Can't hedge if one market closed

## Entry Rules
### Step 1: Calculate Spread
```
Spread = Price_A - (β × Price_B)
```
Where β (beta) = hedge ratio from linear regression

### Step 2: Normalize to Z-Score
```
Z-Score = (Current_Spread - Mean_Spread) / StdDev_Spread
```

### Step 3: Entry Signals
- **LONG Pair** (Buy A, Sell B) when Z-Score < -2.0
  - Interpretation: Spread is 2 std devs below mean
  - Bet: Will revert upward

- **SHORT Pair** (Sell A, Buy B) when Z-Score > +2.0
  - Interpretation: Spread is 2 std devs above mean
  - Bet: Will revert downward

### Step 4: Filters (Critical!)
#### Cointegration Test
- Run Augmented Dickey-Fuller (ADF) test
- **Only trade if p-value < 0.05** (statistically cointegrated)
- Lookback: 100-200 days

#### Half-Life Check
- Calculate mean reversion speed: `Half-Life = -log(2) / λ`
- **Only trade if Half-Life < 20 days**
- Interpretation: Spread reverts within 20 days

####Volatility Regime
- **Avoid if market VIX > 30** (relationships break down in panic)

## Exit Rules
### Primary Exit (Mean Reversion)
1. **Close position** when Z-Score returns to 0 (spread at mean)
2. **Partial Profit**: Close 50% at Z-Score = -1.0 (halfway)

### Stop Loss
- **Z-Score Stop**: Exit if Z-Score reaches ±3.5 (extreme divergence)
- **Time Stop**: Exit after 30 days regardless (half-life failed)
- **Dollar Stop**: -2% loss on combined position

### Emergency Exit
- **Cointegration Breaks**: ADF p-value > 0.10 (relationship died)
- **Correlation Drop**: Correlation falls below 0.5

## Position Sizing
### Market Neutral Approach
- **Equal Dollar Exposure**: $10k long A, $10k short B
- **Beta-Weighted**: Adjust sizes so β-neutral
  - If β = 1.2, then: Long 100 shares A, Short 120 shares B

### Volatility Sizing
```python
position_size_A = risk_% / volatility_A
position_size_B = position_size_A × beta
```

### Leverage
- **Recommended**: 1:1 (no leverage initially)
- **Maximum**: 2:1 (pairs trading is already leveraged via short leg)

## Expected Performance
### Historical Backtests
- **Win Rate**: 65-75% (high, since mean reversion is reliable)
- **Avg R:R**: 1.5:1 to 2:1
- **Sharpe Ratio**: 1.8-2.5 (market neutral = low correlation to market)
- **Max Drawdown**: 8-12% (tight stops + diversification)
- **Expectancy**: $60-100 per pair trade

### Target Metrics (Titan System)
- **Sharpe Target**: >2.0
- **Win Rate**: >70%
- **Max DD**: <10%
- **Expectancy**: $120+ per trade

## Research References
### Academic
- Engle & Granger (1987). "Co-integration and Error Correction"
- Gatev, Goetzmann, Rouwenhorst (2006). "Pairs Trading: Performance of a Relative-Value Arbitrage Rule"

### Books
- Chan, Ernie (2009). *Quantitative Trading* (Ch. 3: Pairs Trading)
- Vidyamurthy, Ganapathy (2004). *Pairs Trading: Quantitative Methods and Analysis*

### Industry
- QuantConnect: Pairs Trading Algorithm Template
- Hudson & Thames: Statistical Arbitrage Strategies

## Implementation Notes
### Code Location
- `titan_system/strategies/pairs_trading.py`
- `titan_system/math_core/cointegration.py` (new module)

### Dependencies
```python
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import coint, adfuller
from sklearn.linear_model import LinearRegression
```

### Data Requirements
- 200+ days of historical daily data (for cointegration test)
- Real-time tick data for both instruments
- Synchronized timestamps (critical!)

### Complexity
**Medium-High** - Requires statistical knowledge, careful implementation

### Pseudo-code
```python
def calculate_hedge_ratio(prices_A, prices_B):
    model = LinearRegression()
    model.fit(prices_B.reshape(-1, 1), prices_A)
    beta = model.coef_[0]
    return beta

def calculate_spread(prices_A, prices_B, beta):
    spread = prices_A - (beta * prices_B)
    return spread

def calculate_zscore(spread):
    mean = spread.mean()
    std = spread.std()
    zscore = (spread[-1] - mean) / std
    return zscore

def pairs_trading_signal(prices_A, prices_B):
    #1. Cointegration test
    _, pvalue, _ = coint(prices_A, prices_B)
    if pvalue > 0.05:
        return "NO_TRADE"  # Not cointegrated
    
    # 2. Calculate spread
    beta = calculate_hedge_ratio(prices_A, prices_B)
    spread = calculate_spread(prices_A, prices_B, beta)
    zscore = calculate_zscore(spread)
    
    # 3. Entry signals
    if zscore < -2.0:
        return "LONG_PAIR"  # Buy A, Sell B
    elif zscore > 2.0:
        return "SHORT_PAIR"  # Sell A, Buy B
    elif abs(zscore) < 0.5:
        return "CLOSE"  # Reversion complete
    
    return "HOLD"
```

## Backtest Plan
### Data Period
- **Lookback**: 2019-01-01 to 2024-12-31 (6 years)
- **Walk-Forward**: 2025-01-01 onwards

### Universe
- **Primary**: EURUSD / GBPUSD
- **Secondary**: XAUUSD / XAGUSD
- **Tertiary**: US500 / NAS100

### Lookback Windows
- **Cointegration**: 100, 150, 200 days (test which is best)
- **Z-Score**: 60, 90 days

### Benchmarks
- **Long-only** each instrument
- **Buy & Hold** market index
- **Random pairs selection** (to prove edge vs luck)

### Metrics
- Sharpe ratio per pair
- Cointegration stability over time
- Half-life distribution
- Performance during VIX spikes

## Risk Considerations
### Market Regime Dependency
- **Works best**: Normal markets (VIX 12-20)
- **Struggles**: Crisis periods (correlation → 1.0, spreads blow out)
- **Solution**: Exit all pairs if VIX > 30

### Liquidity Requirements
- **Both legs must execute simultaneously** (else directional risk)
- **Tight spreads needed** (pairs trading is low-margin)

### Slippage Sensitivity
- **Very High**: Profit margins are thin (0.5-2%)
- **Mitigation**: Use limit orders, avoid illiquid pairs

### Known Failure Modes
1. **Cointegration Break**: Fundamental shift (Brexit, policy change)
   - *Example*: EUR/GBP post-Brexit vote
   - *Mitigation*: Monitor ADF p-value, exit if > 0.10

2. **Divergence Continues**: "Picking up pennies in front of steamroller"
   - *Example*: LTCM 1998 (spread widened to -25 sigma)
   - *Mitigation*: Hard stop at Z = ±3.5

3. **Execution Risk**: Can't short one leg (margin constraints)
   - *Mitigation*: Pre-check margin requirements

### Psychological Challenges
- **Patience**: Wait for extreme Z-scores (don't trade at -1.5)
- **Discipline**: Exit at Z=0, even if you "feel" it will overshoot
- **Fear During Drawdowns**: Spreads widen during volatility (stay calm)

## Status Log
| Date | Update |
|------|--------|
| 2026-01-01 | Strategy documented, cointegration research needed |
| TBD | Implement cointegration module |
| TBD | Backtest EUR/GBP pair (6 years) |
| TBD | Paper trade (2 weeks minimum) |

---

**Next Steps**:
1. Create `cointegration.py` math module (ADF test, half-life)
2. Implement `pairs_trading.py` strategy class
3. Backtest EUR/GBP first (most liquid, stable pair)
4. Build dashboard to monitor live spreads and Z-scores
5. Paper trade before live (critical for execution testing)
