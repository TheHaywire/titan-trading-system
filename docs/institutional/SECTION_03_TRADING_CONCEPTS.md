# Section 03: Trading Concepts & Methodology

**Owner**: Education Lead  
**Status**: 🚧 In Progress (50%)  
**Last Updated**: 2026-01-01

---

## 🎯 Objective

Define why and how traders trade at institutional/prop firm level: risk-reward ratios, expectancy formulas, win rate relationships, and the institutional risk philosophy that separates profitable traders from gamblers.

---

## 1. Why Traders Trade (Institutional Perspective)

### Core Principle
Institutional and prop firm traders trade to **exploit small, repeatable statistical edges with controlled risk and scalable capital**.

This is fundamentally different from retail gambling because:
- ✅ **Edge is quantifiable**: Measured via backtests, Monte Carlo, out-of-sample validation
- ✅ **Risk is predetermined**: Never risk more than X% per trade
- ✅ **Process over outcome**: Focus on executing the system, not individual trade results
- ✅ **Scalability**: Proven strategies can handle larger position sizes

---

## 2. Risk-Reward (R:R) Ratio

### Definition
**Risk-Reward Ratio** = Potential Profit / Potential Loss

Where:
- **Potential Profit** = Distance from Entry to Take Profit (in pips/points/currency)
- **Potential Loss** = Distance from Entry to Stop Loss (in pips/points/currency)

### Institutional Targets

| R:R Ratio | Interpretation | Use Case |
|-----------|----------------|----------|
| **1:1** | Break-even with 50% win rate | High-probability setups, scalping |
| **2:1** | Profitable with >33% win rate | Standard swing trades |
| **3:1** | Profitable with >25% win rate | Trend-following, breakouts |
| **5:1+** | "Home run" trades | Rare, high-conviction setups |

### Example Calculation

```python
# EURUSD Trade
entry_price = 1.1000
stop_loss = 1.0980  # 20 pips risk
take_profit = 1.1060  # 60 pips reward

risk_pips = (entry_price - stop_loss) * 10000  # 20 pips
reward_pips = (take_profit - entry_price) * 10000  # 60 pips

rr_ratio = reward_pips / risk_pips  # 3:1
print(f"R:R = {rr_ratio}:1")
```

**Key Insight**: A 3:1 R:R means you can lose 75% of your trades and still break even. Win 30% and you're profitable.

---

## 3. Expectancy: The Holy Grail Metric

### Formula

**Expectancy** = (Win Rate × Average Win) - (Loss Rate × Average Loss)

Or equivalently:

**Expectancy** = (Win Rate × R:R) - (Loss Rate × 1)

Where:
- **Win Rate** = % of winning trades
- **Loss Rate** = % of losing trades = (1 - Win Rate)
- **Average Win** = Average profit per winning trade (in R)
- **Average Loss** = Average loss per losing trade (in R, usually = 1)

### Positive vs Negative Expectancy

- **Positive Expectancy** (E > 0): System makes money over time
- **Negative Expectancy** (E < 0): System loses money over time
- **Zero Expectancy** (E = 0): Break-even system

### Examples

#### Example 1: High Win Rate, Low R:R
```
Win Rate = 60%
R:R = 1:1

Expectancy = (0.60 × 1) - (0.40 × 1) = 0.20R per trade
```
**Interpretation**: Expect to make 0.20R per trade on average. Win $200 per trade if risking $1000.

#### Example 2: Low Win Rate, High R:R
```
Win Rate = 30%
R:R = 4:1

Expectancy = (0.30 × 4) - (0.70 × 1) = 0.50R per trade
```
**Interpretation**: Even with 70% losers, you make 0.50R per trade! This is a breakout/trend-following profile.

#### Example 3: Losing System
```
Win Rate = 45%
R:R = 1:1

Expectancy = (0.45 × 1) - (0.55 × 1) = -0.10R per trade
```
**Interpretation**: Lose 10% of your risk per trade. This will bleed your account slowly.

---

## 4. Win Rate vs R:R Trade-Off

### The Matrix

| Win Rate | Required R:R for Break-Even | Realistic Strategy Type |
|----------|----------------------------|------------------------|
| 90% | 0.11:1 | Market making, mean reversion (tight stops) |
| 70% | 0.43:1 | Scalping, high-frequency |
| 50% | 1:1 | Balanced strategies |
| 40% | 1.5:1 | Swing trading |
| 30% | 2.3:1 | Trend following, breakouts |
| 20% | 4:1 | "Home run" hunters |

### Formula: Minimum R:R for Break-Even
```
Min R:R = Loss Rate / Win Rate = (1 - Win Rate) / Win Rate
```

**Example**: 40% win rate requires minimum 1.5:1 R:R to break even.

### Titan System Strategy Profiles

| Strategy | Win Rate | R:R | Expectancy | Profile |
|----------|----------|-----|------------|---------|
| **BookTechnical** | 45% | 2.5:1 | 0.57R | Moderate win rate, good R:R |
| **InstitutionalGold** | 35% | 3:1 | 0.40R | Trend-following, lower win rate |
| **Target (Future)** | 50%+ | 2:1+ | 1.0R+ | Ideal institutional profile |

---

## 5. Institutional Risk Philosophy

### Core Tenets

#### 1. **Process Over Results**
- Individual trade outcomes are random
- Focus on executing the system flawlessly
- 100 trades define performance, not 1

#### 2. **Risk First, Reward Second**
- Always define stop loss BEFORE entry
- Position size based on risk %, not account size
- Never "wing it" without a stop

#### 3. **Expectancy Is King**
- Win rate alone means nothing
- R:R alone means nothing
- Only their combination (expectancy) matters

#### 4. **Consistency Beats Heroics**
- Small, consistent edges compound over time
- Avoid "all-in" or "revenge" trades
- Boring is profitable

#### 5. **Drawdowns Are Inevitable**
- Even positive expectancy systems have losing streaks
- Max drawdown is a feature, not a bug
- Risk management prevents catastrophic loss

### Statistical Rigor

Institutional traders demand:
- ✅ **Backtests**: Minimum 100 trades, ideally 500+
- ✅ **Monte Carlo**: Simulate 10,000 possible futures
- ✅ **Walk-Forward**: Out-of-sample validation
- ✅ **Sharpe Ratio**: Risk-adjusted returns (> 1.5 preferred)
- ✅ **Maximum Drawdown**: Tolerable pain threshold (< 20% preferred)

---

## 6. Drawdown, Volatility, and Position Sizing

### Maximum Drawdown (MDD)

**Definition**: Largest peak-to-trough decline in account equity.

**Example**:
```
Peak equity: $10,000
Trough equity: $8,000
MDD = ($10,000 - $8,000) / $10,000 = 20%
```

**Institutional Limits**:
- **Conservative**: 10-15% MDD
- **Aggressive**: 20-25% MDD
- **Prop Firm Challenge**: Often 10% daily, 5% max total

### Kelly Criterion (Position Sizing)

**Formula**:
```
Kelly % = (Win Rate × (1 + R:R) - 1) / R:R
```

**Example**:
```
Win Rate = 40%
R:R = 2:1

Kelly % = (0.40 × 3 - 1) / 2 = 0.10 = 10%
```

**Interpretation**: Risk 10% of capital per trade for optimal growth.

**Institutional Practice**: Use **Half Kelly** or **Quarter Kelly** to reduce volatility.
- Half Kelly = 5% per trade (more realistic)
- Quarter Kelly = 2.5% per trade (conservative)

**Titan System**: Uses 0.5-1% per trade (even more conservative than Quarter Kelly).

---

## 📚 Cross-References

### External Resources
- **Book**: Ernest Chan - "Quantitative Trading" (Expectancy chapter)
- **Book**: Van Tharp - "Trade Your Way to Financial Freedom" (Expectancy systems)
- **Paper**: Kelly Criterion: "A New Interpretation of Information Rate" (1956)

### Prop Firm Risk Frameworks
- **FTMO**: Daily loss 5%, total loss 10%
- **TopStepTrader**: Daily loss target-based
- **The5ers**: Aggressive funding, 6% daily loss

### Titan System Implementation
- **Position Sizer**: `titan_system/risk/position_sizer.py`
- **Expectancy Calculator**: (To be built - Section 03 deliverable)
- **Backtest Metrics**: `titan_system/analytics/metrics.py`

---

## ✅ Validation Checklist

- [x] R:R ratio framework documented
- [ ] Expectancy calculator tool built
- [ ] Win rate vs R:R analysis automated
- [ ] Institutional risk philosophy documented ✅
- [ ] Kelly Criterion position sizer integrated
- [ ] Drawdown monitoring implemented

---

## 🚨 Known Gaps

1. **Expectancy Calculator**: Need standalone tool to compute expectancy from CSV trade logs
2. **Live Expectancy Tracking**: Dashboard should show running expectancy per strategy
3. **Correlation to R:R**: Automatic alerts when trades deviate from target R:R

**Next Actions**: Build expectancy calculator, integrate into monitoring dashboard (Section 11).

---

**Status**: Core concepts documented ✅ | Tools pending implementation 📋
