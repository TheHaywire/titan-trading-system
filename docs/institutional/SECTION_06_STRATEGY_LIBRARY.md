# Section 06: Strategy Library & Research Process

**Owner**: Head of Research  
**Status**: 🚧 In Progress (55%)  
**Last Updated**: 2026-01-01

---

## 🎯 Objective

Document all trading strategies, their hypotheses, risk models, and research workflow. Ensure new strategies follow institutional validation before capital deployment.

---

## 1. Strategy Catalog

### Active Strategies

#### BookTechnical Strategy
- **Hypothesis**: Technical indicators (MA, RSI, Bollinger) capture institutional order flow
- **Timeframe**: H1, H4
- **Symbols**: XAUUSD, GBPUSD, US100
- **Entry**: MA crossover + RSI confirmation
- **Exit**: Take profit at 2.5R, trailing stop with SMA 50
- **Win Rate**: 45%
- **Expectancy**: 0.57R
- **Risk Model**: 1% per trade

**Code**: `titan_system/strategies/book_strategies.py`

#### InstitutionalGold Strategy
- **Hypothesis**: Gold follows multi-timeframe trend alignment (H4 bias → H1 zones → M15 trigger)
- **Timeframe**: M15 entry, H1/H4 confirmation
- **Symbols**: XAUUSD only
- **Entry**: H4 trend + H1 support/resistance + M15 breakout
- **Exit**: 3:1 R:R minimum
- **Win Rate**: 35%
- **Expectancy**: 0.40R
- **Risk Model**: 0.75% per trade

**Code**: `titan_system/strategies/institutional_gold.py`

---

## 2. Strategy Research Workflow

### 6-Step Institutional Process

```
1. IDEA GENERATION
   ├── Market observation
   ├── Literature review (books, papers)
   └── Hypothesis formulation

2. SIMULATION / BACKTEST
   ├── Python backtest (1+ years data)
   ├── Monte Carlo (10,000 runs)
   └── Expectancy > 0.5R required

3. STRESS TESTS
   ├── Different market regimes (trending, ranging, volatile)
   ├── Slippage modeling
   └── Commission impact

4. FORWARD TEST / PAPER TRADING
   ├── Demo account (3+ months)
   ├── Live signals, no real money
   └── Track execution quality

5. LIMITED CAPITAL DEPLOYMENT
   ├── Start with $500-$1000
   ├── Monitor for 50+ trades
   └── Confirm live expectancy matches backtest

6. SCALING RULES
   ├── If expectancy maintained → increase allocation
   ├── If expectancy degrades → pause and analyze
   └── Maximum 3 strategies live concurrently
```

---

## 3. Strategy Family Catalog

### Trend Following
- **Examples**: Moving Average Crossover, Donchian Breakout
- **Characteristics**: Low win rate (30-40%), high R:R (3:1+)
- **Best Markets**: Trending indices, commodities

### Mean Reversion
- **Examples**: Bollinger Band reversals, RSI oversold/overbought
- **Characteristics**: High win rate (60-70%), low R:R (1:1)
- **Best Markets**: Range-bound FX pairs

### Breakout
- **Examples**: Asian Range Breakout, London Open
- **Characteristics**: Medium win rate (40-50%), medium R:R (2:1)
- **Best Markets**: Volatile indices, crypto

### Carry Trade
- **Examples**: Positive swap pairs, interest rate differential
- **Characteristics**: Steady income, catastrophic tail risk
- **Best Markets**: Stable FX pairs (AUDJPY, NZDJPY)

### Statistical Arbitrage
- **Examples**: Pair trading, futures curve arbitrage
- **Characteristics**: Market-neutral, low volatility
- **Best Markets**: Correlated instruments

---

## 4. Multi-Agent Architecture (Planned)

### Separation of Concerns

```
┌─────────────────────────────────────────────────┐
│           MULTI-AGENT FRAMEWORK                 │
├─────────────────────────────────────────────────┤
│                                                  │
│  PREDICTION AGENTS (Forecast)                   │
│  ├── TechnicalAgent: MA, RSI, Bollinger        │
│  ├── SentimentAgent: News, Twitter             │
│  ├── MacroAgent: Interest rates, GDP           │
│  └── MLAgent: Neural networks, ensembles        │
│                                                  │
│  ALLOCATION AGENT (Portfolio)                   │
│  ├── Aggregates all predictions                │
│  ├── Manages risk budgets                      │
│  ├── Optimizes position sizes                  │
│  └── Decides which trades to take              │
│                                                  │
│  EXECUTION AGENT (Trading)                      │
│  └── Sends orders to MT5                       │
│                                                  │
└─────────────────────────────────────────────────┘
```

**Status**: Single-agent currently. Multi-agent planned for Phase 2.

---

## 5. Formal Hypothesis Documentation

### Template

For each new strategy:

```markdown
## Strategy Name: [Name]

### Hypothesis
**What**: [Clear statement of edge]
**Why**: [Economic/behavioral reason it should work]
**When**: [Market conditions required]

### Features Used
- Feature 1: [e.g., 200-day MA]
- Feature 2: [e.g., ATR]
- Feature 3: [e.g., Volume]

### Entry Rules
1. Condition 1
2. Condition 2
3. Condition 3

### Exit Rules
- TP: [e.g., 2.5R]
- SL: [e.g., below recent swing low]
- Trailing: [e.g., SMA 50]

### Risk Model
- Risk per trade: [e.g., 1%]
- Max concurrent trades: [e.g., 3]
- Max symbol allocation: [e.g., 5%]

### Backtested Performance
- Period: [e.g., 2020-2024]
- Total trades: [e.g., 250]
- Win rate: [e.g., 45%]
- Expectancy: [e.g., 0.6R]
- Sharpe: [e.g., 1.8]
- Max DD: [e.g., 15%]

### Validation Status
- [ ] Backtested
- [ ] Monte Carlo passed
- [ ] Forward tested
- [ ] Live (limited capital)
- [ ] Live (full allocation)
```

---

## 📚 Cross-References

### External Resources
- **Chan**: "Algorithmic Trading" (mean reversion strategies)
- **Coulling**: "Volume Price Analysis" (VPA concepts)
- **Academic Papers**: arXiv.org (quantitative trading)

### Titan System
- **BookTechnical**: `titan_system/strategies/book_strategies.py`
- **InstitutionalGold**: `titan_system/strategies/institutional_gold.py`
- **Research Workflow**: `docs/RESEARCH_WORKFLOW.md` (to be created)

---

## ✅ Validation Checklist

- [x] Strategy catalog documented (2 strategies)
- [x] Research workflow defined
- [ ] Multi-agent architecture designed
- [ ] 5 formal hypothesis docs created
- [ ] Strategy performance dashboard built

---

**Status**: Core strategies documented | Pipeline formalization pending
