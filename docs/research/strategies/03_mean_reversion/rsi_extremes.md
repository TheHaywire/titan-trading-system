# RSI Extremes Strategy (Larry Connors)

## Category
**Mean Reversion**

## Status
- Research: ✅ Complete
- Backtest: ⏳ Not Started
- Paper Trade: ⏳ Not Started
- Demo: ⏳ Not Started
- Live: ⏳ Not Started

## Hypothesis
**When RSI(2) reaches extreme levels (<10 or >90), it signals panic selling or FOMO buying. Markets tend to revert to the mean within 1-5 days, creating short-term profit opportunities.**

## Edge Explanation
### Behavioral Finance Basis
- **Overreaction**: Traders panic at extremes
- **Exhaustion**: Buyers/sellers run out at peaks/troughs
- **Statistical Mean Reversion**: Prices oscillate around fair value

### Empirical Evidence
- Larry Connors backtested 10,000+ trades
- Win rate >70% on stocks
- Works best on volatile assets (crypto, individual stocks)

## Instruments
### Primary (Best Suited)
- **BTCUSD** (Bitcoin) - Extreme volatility, frequent RSI <10/>90
- **ETHUSD** (Ethereum) - Similar to BTC
- **Individual Growth Stocks** - High beta names (TSLA, NVDA, etc.)
- **XAUUSD** (Gold) - During volatility spikes

### Secondary
- Major FX pairs during news events
- Commodities (Oil, Silver)

### Avoid
- **Strongly trending markets** - RSI extremes can persist
- **Low volatility FX** (EURCHF) - Rarely hits extremes
- **Indices during crashes** - Mean reversion fails in panic

## Entry Rules
### Core Setup (RSI2)
1. Calculate RSI with 2-period lookback
2. **LONG Entry**: RSI(2) < 10
   - Price is oversold / panic selling
3. **SHORT Entry**: RSI(2) > 90
   - Price is overbought / FOMO buying

### Filters (Optional but Recommended)
#### Trend Filter
- Only LONG if price > 200 SMA (uptrend)
- Only SHORT if price < 200 SMA (downtrend)

#### Volume Confirmation
- Volume > 20-day average (institutional participation)

#### Multiple Timeframe
- RSI(2) extreme on M15 AND H1 (stronger signal)

### Entry Execution
- **Market Order** at close of candle showing RSI extreme
- OR **Limit Order** at prior day's low (LONG) or high (SHORT)

## Exit Rules
### Primary Exit (Mean Reversion)
1. **LONG Exit**: RSI(2) crosses above 50 (neutral zone)
2. **SHORT Exit**: RSI(2) crosses below 50

### Profit Targets
- **Conservative**: 1% gain (quick scalp)
- **Aggressive**: 3-5% gain (let it run)
- **Trailing Stop**: 2× ATR from entry

### Stop Loss
- **Fixed**: 2% below entry (LONG) or above (SHORT)
- **ATR-based**: Entry ± 1.5× ATR_14
- **Time-based**: Exit after 5 days regardless

### Maximum Hold Time
- **Recommended**: 1-5 days
- **Rationale**: Strategy is short-term mean reversion

## Position Sizing
### Base Allocation
- **Risk per trade**: 1% of account
- **Position size**: Risk_$ / Stop_Loss_Distance

### Volatility Adjustment
- Reduce size by 50% if ATR > 2× average
- Increase size by 25% if win rate >75% recently

### Max Positions
- Maximum 3 concurrent positions (diversify)
- Prefer uncorrelated assets

## Expected Performance
### Historical Backtests (Connors, 2012)
- **Win Rate**: 70-75% on stocks
- **Avg Win**: +2.5%
- **Avg Loss**: -1.8%
- **Expectancy**: +0.6% per trade
- **Sharpe**: 1.2-1.5 (high win rate smooths equity curve)

### Target Metrics (Titan System)
- **Win Rate Target**: >65%
- **Avg R:R**: 1.4:1
- **Expectancy**: $80+ per trade
- **Max Drawdown**: <12%
- **Sharpe**: >1.3

## Research References
### Books
- Connors, Larry (2012). *Short Term Trading Strategies That Work*
- Connors & Alvarez (2009). *High Probability ETF Trading*

### Academic
- Wilder, J. Welles (1978). *New Concepts in Technical Trading Systems* (RSI origin)

### Industry
- QuantConnect: RSI Mean Reversion Backtests
- TradingView: RSI2 Strategy Performance

## Implementation Notes
### Code Location
- `titan_system/strategies/rsi_extremes.py`

### Dependencies
```python
import pandas as pd
import talib  # For RSI calculation
from titan_system.analytics.indicators import IndicatorFactory
```

### Data Requirements
- Minimum 50 bars for RSI calculation
- M15 or H1 timeframe recommended
- Real-time feed for entry/exit signals

### Complexity
**Low** - Single indicator, simple logic

### Pseudo-code
```python
def calculate_rsi2(prices):
    return talib.RSI(prices, timeperiod=2)

def rsi_extremes_signal(df):
    rsi2 = calculate_rsi2(df['close'])
    sma200 = df['close'].rolling(200).mean()
    
    # Long setup
    if rsi2[-1] < 10 and df['close'][-1] > sma200[-1]:
        return "BUY"
    
    # Short setup
    elif rsi2[-1] > 90 and df['close'][-1] < sma200[-1]:
        return "SELL"
    
    # Exit long
    elif rsi2[-1] > 50 and position == "LONG":
        return "CLOSE_LONG"
    
    # Exit short
    elif rsi2[-1] < 50 and position == "SHORT":
        return "CLOSE_SHORT"
    
    return "HOLD"
```

## Backtest Plan
### Data Period
- **Crypto**: 2020-01-01 to 2025-12-31 (5 years, high volatility)
- **Stocks**: 2015-01-01 to 2024-12-31 (10years)

### Universe
- Bitcoin (BTCUSD)
- Ethereum (ETHUSD)
- Gold (XAUUSD) during volatility spikes
- 10 major growth stocks (if broker supports)

### Lookback
- Minimum: 200 bars (for SMA filter)
- RSI calculation: 2 periods only

### Benchmarks
- Buy & Hold Bitcoin
- Buy & Hold S&P 500
- Random entry/exit (to prove edge exists)

### Metrics
- Win rate by asset class
- Average hold time
- RSI level distribution at entry/exit
- Performance with/without trend filter

## Risk Considerations
### Market Regime Dependency
- **Works best**: Range-bound, choppy markets
- **Struggles**: Strong trends (RSI stays extreme)
- **Solution**: Add 200 SMA filter to avoid counter-trend

### Liquidity Requirements
- **Intraday**: Need tight spreads for scalping
- **Crypto**: 24/7 markets, no gaps
- **Stocks**: Avoid low-volume names

### Slippage Sensitivity
- **High**: RSI extremes often occur at volatility spikes
- **Mitigation**: Use limit orders, not market orders

### Known Failure Modes
1. **Flash Crashes**: RSI <10 but price keeps falling (2020 COVID crash)
   - *Mitigation*: Use stop loss, don't "buy the dip" blindly
2. **Strong Trends**: RSI >90 in a parabolic rally
   - *Mitigation*: Trend filter (no shorts in uptrend)
3. **Low Volatility**: RSI rarely reaches extremes
   - *Mitigation*: Skip symbols with ATR < threshold

### Psychological Challenges
- **FOMO**: Want to enter at RSI 30 (too early)
- **Fear**: Scared to buy at RSI 5 (but that's the signal!)
- **Impatience**: Holding past RSI 50 hoping for more

## Status Log
| Date | Update |
|------|--------|
| 2026-01-01 | Strategy documented, ready for backtest |
| TBD | Implement RSI(2) indicator |
| TBD | Backtest on Bitcoin 2020-2024 |
| TBD | Paper trade on crypto markets |

---

**Next Steps**:
1. Implement `rsi_extremes.py` strategy class
2. Create backtest script `scripts/backtests/backtest_rsi_extremes.py`
3. Run on Bitcoin first (most volatile, frequent signals)
4. Optimize: Test RSI thresholds (5/95? 15/85?)
5. Paper trade for 2 weeks before live
