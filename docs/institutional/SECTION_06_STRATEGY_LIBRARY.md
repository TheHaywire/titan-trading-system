# Section 06: Strategy Library & Research Process

**Owner**: Head of Research  
**Status**: ✅ Complete (95%)  
**Last Updated**: 2026-01-12

---

## 🎯 Objective

Document all trading strategies, their hypotheses, risk models, and research workflow. Ensure new strategies follow institutional validation before capital deployment.

---

## 1. Strategy Catalog

### Core Production Strategies (titan_system/strategies/)

#### BookTechnical Strategy
- **File**: `book_strategies.py`
- **Hypothesis**: Technical indicators (MA, RSI, Bollinger) capture institutional order flow
- **Signals**: MA Golden/Death Cross, RSI Extremes, Bollinger Breakout
- **Win Rate**: 45% | **Expectancy**: 0.57R

#### InstitutionalGold Strategy
- **File**: `institutional_gold.py`
- **Hypothesis**: Gold follows MTF trend alignment (H4 bias → H1 zones → M15 trigger)
- **Win Rate**: 35% | **Expectancy**: 0.40R

#### ProvenStrategy (Backtested Winners)
- **File**: `proven_strategy.py`
- **Strategies**: EMA 9/21 Cross, EMA Pullback
- **Best Performance**: USDJPY 63.3% win rate, 0.79R expectancy

#### Additional Production Strategies
| Strategy | File | Type |
|----------|------|------|
| DualMomentum | `dual_momentum.py` | Cross-asset momentum |
| MeanReversion | `mean_reversion.py` | BB/RSI extremes |
| TrendSurfer | `trend_surfer.py` | Trend following |
| DivergenceHunter | `divergence_hunter.py` | RSI/MACD divergence |
| LiquidityHunter | `liquidity_hunter.py` | SMC liquidity sweeps |
| RegressionSurfer | `regression_surfer.py` | Linear regression |
| MomentumScalper | `scalper.py` | Scalping |
| ScalperPro | `scalper_pro.py` | Advanced scalping |
| LiveGoldBreakout | `live_gold_breakout.py` | Gold breakouts |
| LiveCryptoTrend | `live_crypto_trend.py` | Crypto trends |

---

### Smart Money Concepts (titan_system/smc/)

| Module | File | Purpose |
|--------|------|---------|
| Fair Value Gaps | `fvg.py` | FVG detection and entry |
| Liquidity Analysis | `liquidity.py` | Liquidity sweep detection |
| Market Structure | `market_structure.py` | BOS/CHoCH identification |
| Institutional Engine | `institutional_engine.py` | Complete SMC orchestration |
| VWAP Engine | `vwap_engine.py` | VWAP-based strategies |
| Momentum Engine | `momentum_engine.py` | Momentum analysis |
| Trend Engine | `trend_engine.py` | Trend detection |
| Volatility Engine | `volatility_engine.py` | Volatility analysis |

---

### Backtest Strategy Library (titan_system/backtest/)

**26 strategy files covering 50+ strategies:**

| Category | File | Strategies Included |
|----------|------|---------------------|
| Momentum | `strategies_momentum.py` | MACD, Stochastic, ADX |
| Mean Reversion | `strategies_meanreversion.py` | BB reversals, RSI extremes |
| Breakout | `strategies_breakout.py` | ORB, London breakout, range breaks |
| Patterns | `strategies_patterns.py` | Engulfing, Hammer, Doji, Pin Bar |
| Volume | `strategies_volume.py` | OBV, Volume spikes, VWAP |
| Time-Based | `strategies_timebased.py` | Session opens, time filters |
| Volatility | `strategies_volatility.py` | ATR breakouts, Keltner |
| SMC | `strategies_smc.py` | Order blocks, FVG, liquidity |
| Professional 1-5 | `strategies_professional_*.py` | Advanced institutional setups |
| Advanced | `strategies_advanced.py` | Complex multi-factor strategies |
| MTF | `strategies_mtf.py` | Multi-timeframe alignment |

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
