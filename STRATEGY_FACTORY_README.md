# 🏭 Strategy Factory - Autonomous Trading System

> **A fully autonomous meta-system that continuously discovers, validates, and deploys profitable trading strategies with institutional-grade risk controls.**

---

## 🎯 What Is This?

The **Strategy Factory** is a self-improving trading infrastructure that operates like a hedge fund's strategy research department - but fully automated. Instead of manually coding and testing strategies, the factory:

1. **Generates** 50+ unique strategy ideas per cycle
2. **Validates** them with rigorous statistical tests (OOS, Monte Carlo, Walk-Forward)
3. **Scores** using multi-dimensional metrics (Sharpe, Win Rate, Robustness, Frequency)
4. **Compiles** top performers into executable Python trading bots
5. **Deploys** to paper trading, then promotes winners to live
6. **Monitors** all strategies and auto-retires underperformers
7. **Evolves** continuously through mutation and optimization

**Result**: A portfolio of 5-10 diversified, validated strategies running 24/7, discovering edge while you sleep.

---

## ⚡ Quick Start

### Option 1: Run the Complete Demo (Recommended First!)

```bash
# See the entire pipeline in action
python scripts/factory_demo.py
```

This interactive demo shows:
- Strategy generation
- Backtesting with validation
- Scoring and ranking
- Code compilation
- Deployment instructions

**Duration**: ~5-10 minutes (depending on backtest speed)

### Option 2: Start Continuous Operation

```bash
# Runs autonomously every 24 hours
python scripts/run_factory.py --mode continuous
```

This will:
- Generate 50 candidates daily
- Backtest and validate automatically
- Deploy winners to paper trading
- Monitor and manage the portfolio

### Option 3: Manual Step-by-Step

```bash
# 1. Generate candidates
python scripts/run_factory.py --mode single

# 2. Backtest all candidates
python scripts/backtest_candidates.py

# 3. Deploy best performer to paper trading
python scripts/deploy_to_paper.py <strategy_id>
```

---

## 📁 Project Structure

```
titan_system/factory/
├── factory_config.py           # ⚙️ Configuration & risk limits
├── strategy_genome.py          # 🧬 Strategy DNA format
├── strategy_registry.py        # 💾 SQLite database
├── strategy_factory.py         # 🏭 Main orchestrator
│
├── generators/
│   └── idea_generator.py       # 💡 Strategy generation
│
├── validation/
│   ├── backtest_runner.py      # ⚡ Backtesting engine
│   └── robustness_tests.py     # 🔬 Statistical validation
│
├── scoring/
│   ├── strategy_scorer.py      # 📊 Multi-metric scoring
│   └── correlation_analyzer.py # 🎯 Portfolio diversification
│
└── deployment/
    └── code_compiler.py        # 🤖 Strategy → Executable Bot

scripts/
├── run_factory.py              # ▶️ Main entry point
├── backtest_candidates.py      # 🧪 Batch backtesting
├── deploy_to_paper.py          # 🚀 Deployment
└── factory_demo.py             # 🎬 Complete demo

data/
└── strategy_factory.db         # 💾 Registry database

titan_system/strategies/autogen/
└── *.py                        # 🤖 Auto-generated bots
```

---

## 📚 Documentation

**Start Here**:
1. 📖 **[SYSTEM_MAP.md](C:/Users/manan/.gemini/antigravity/brain/8ac70484-67f2-4ed8-8e3f-127ac9ce24e2/SYSTEM_MAP.md)** - Visual overview of all components
2. 📘 **[walkthrough.md](C:/Users/manan/.gemini/antigravity/brain/8ac70484-67f2-4ed8-8e3f-127ac9ce24e2/walkthrough.md)** - Complete system documentation
3. 📋 **[QUICK_REFERENCE.md](C:/Users/manan/.gemini/antigravity/brain/8ac70484-67f2-4ed8-8e3f-127ac9ce24e2/QUICK_REFERENCE.md)** - Daily operations cheat sheet
4. ✅ **[task.md](C:/Users/manan/.gemini/antigravity/brain/8ac70484-67f2-4ed8-8e3f-127ac9ce24e2/task.md)** - Implementation checklist (all phases complete)

---

## 🎮 How It Works

### The Complete Pipeline

```
IDEA → BACKTEST → VALIDATE → SCORE → COMPILE → PAPER → LIVE → MONITOR
  ↓       ↓         ↓         ↓        ↓         ↓       ↓       ↓
 50+   1yr data   OOS/MC    0-100   Python   14 days  Scale  Kill
ideas   tested    WFA pts   ranked   bot     trades    up   switches
```

### Daily Cycle (Automatic)

Every 24 hours, the factory:
1. ✅ Checks portfolio risk (DD < 20%)
2. ✅ Monitors live strategies (applies kill switches)
3. ✅ Checks paper promotions (14 days + 20 trades + Sharpe >1.0)
4. ✅ Generates 50 new candidates
5. ✅ Queues them for backtesting
6. ✅ Reports portfolio status

### Quality Gates

**Generation Phase**:
- 50 candidates across 14 symbols × 5 timeframes
- 3 methods: Templates (40%), Rotations (30%), Random (30%)

**Validation Phase**:
- Min 365 days data, 50 trades
- Sharpe ≥ 1.0, Win Rate ≥ 45%
- OOS Sharpe ≥ 70% of IS
- Monte Carlo stable, Walk-Forward consistent

**Deployment Phase**:
- Score ≥ 75/100 required
- Correlation < 0.70 with deployed
- 14 days paper + 20 trades
- Live Sharpe ≥ 1.0

**Retirement Phase**:
- Auto-retire if DD > 25%
- Auto-retire if 7 consecutive losses
- Auto-retire if edge decays (Live << Backtest Sharpe)
- Auto-retire if inactive 7+ days

---

## ⚙️ Configuration

Edit `titan_system/factory/factory_config.py`:

### Risk Limits

```python
MAX_PORTFOLIO_DRAWDOWN = 0.20      # Emergency stop at 20%
MAX_STRATEGY_ALLOCATION = 0.15     # Max 15% per strategy
MAX_CORRELATION_THRESHOLD = 0.70   # Block if correlation > 0.70
MIN_STRATEGY_SHARPE = 1.0          # Minimum to qualify
MAX_STRATEGY_DRAWDOWN = 0.25       # Auto-retire at 25%
AUTO_RETIRE_CONSECUTIVE_LOSSES = 7 # Retire after 7 losses
```

### Symbol Universe

```python
SYMBOL_UNIVERSE = [
    "GOLD", "SILVER",                    # Metals
    "EURUSD", "GBPUSD", "USDJPY",       # Major FX
    "BTCUSD", "ETHUSD"                  # Crypto
]

TIMEFRAME_UNIVERSE = ["M5", "M15", "M30", "H1", "H4"]
```

### Deployment Rules

```python
PAPER_TRADING_DAYS = 14              # 2 weeks mandatory
PAPER_MIN_TRADES = 20                # Minimum trades
AUTO_APPROVE_SHARPE = 2.0            # Auto-deploy if Sharpe ≥ 2.0
MAX_LIVE_STRATEGIES = 10             # Portfolio limit
MAX_PAPER_STRATEGIES = 5             # Paper limit
```

---

## 📊 Expected Results (6 Months)

| Metric | Target | Description |
|--------|--------|-------------|
| Strategies Generated | 1,500+ | 50 per cycle × 30 cycles/month |
| Validation Pass Rate | 10-20% | ~150-300 reach paper trading |
| Paper Promotion Rate | 50% | ~75-150 reach live |
| Active Live Strategies | 5-10 | Diversified portfolio |
| Portfolio Sharpe | >1.5 | Aggregate performance |
| Max Drawdown | <15% | Portfolio-level |
| Monthly Return | >5% | Compound growth |

---

## 🔧 Common Operations

### Check Portfolio Status

```python
from titan_system.factory.strategy_registry import StrategyRegistry

registry = StrategyRegistry()
metrics = registry.get_portfolio_metrics()

print(f"Live: {metrics['live_count']}/10")
print(f"Paper: {metrics['paper_count']}/5")
print(f"Total PnL: ${metrics['total_pnl']:.2f}")
print(f"Avg Sharpe: {metrics['avg_sharpe']:.2f}")
print(f"Max DD: {metrics['max_drawdown']*100:.1f}%")
```

### View Top Performers

```python
top = registry.get_top_performers(n=10, metric='live_sharpe')
for s in top:
    print(f"{s['id'][:8]}: Sharpe {s['live_sharpe']:.2f}, PnL ${s['live_pnl']:.2f}")
```

### Manual Retirement

```python
registry.update_status(
    strategy_id='<id>',
    new_status='retired',
    reason='Manual retirement'
)
```

---

## 🛡️ Safety Features

### Portfolio-Level Risk

- **Emergency Stop**: Halts all trading if portfolio DD > 20%
- **Allocation Caps**: Max 15% per strategy
- **Correlation Limits**: Prevents over-concentration
- **Leverage Control**: Max 5x total exposure

### Strategy-Level Kill Switches

- ❌ Drawdown > 25%
- ❌ 7 consecutive losses
- ❌ Live Sharpe << Backtest Sharpe (edge decay)
- ❌ Inactive 7+ days (no trades)

### Validation Requirements

- ✅ Out-of-sample validation (OOS ≥ 70% of IS)
- ✅ Monte Carlo stability (95% confidence)
- ✅ Walk-forward consistency (CV < 0.5)
- ✅ Parameter sensitivity (max 30% degradation)

---

## 🎓 Key Principles

**1. Trust the Process**
- The validation pipeline is designed to catch overfitting
- If a strategy passes all tests, it's statistically robust
- Don't override kill switches based on gut feel

**2. Portfolio > Individual Strategies**
- Focus on aggregate metrics, not single strategy returns
- Diversification reduces risk more than individual Sharpe
- Let underperformers die (don't get attached)

**3. Continuous Evolution**
- Markets change, strategies decay
- The factory discovers new edge continuously
- Winners today may be losers tomorrow - that's OK

**4. Data-Driven Decisions**
- Every action is logged and tracked
- Use the registry to learn what works
- Optimize based on data, not intuition

**5. Patience & Scale**
- This is a numbers game (50 ideas → 5-10 winners)
- Give it 3-6 months to build momentum
- Think in quarters, not days

---

## 🚨 Troubleshooting

### Issue: No strategies passing validation

**Symptoms**: All backtests fail or score < 75

**Solutions**:
1. Lower `MIN_STRATEGY_SHARPE` to 0.8 in config
2. Increase `MAX_CANDIDATES_PER_CYCLE` to 100
3. Check MT5 data availability
4. Review parameter ranges

### Issue: Factory not generating

**Symptoms**: "Max strategy limit reached"

**Solutions**:
1. Check `MAX_LIVE_STRATEGIES` and `MAX_PAPER_STRATEGIES`
2. Retire underperforming paper strategies
3. Promote ready paper strategies to live

### Issue: Database locked

**Symptoms**: `database is locked` error

**Solutions**:
```bash
# Close all Python processes, then:
python -c "from titan_system.factory.strategy_registry import StrategyRegistry; r = StrategyRegistry(); print('DB OK')"
```

---

## 📈 Success Metrics (First 30 Days)

### Week 1: Setup
- [ ] Run demo successfully
- [ ] Generate 10 candidates
- [ ] Deploy 1 to paper

### Week 2: First Live
- [ ] Monitor paper (7/14 days)
- [ ] Generate 20 more candidates
- [ ] Deploy 2nd to paper

### Week 3: Portfolio
- [ ] Promote 1st to live (if ready)
- [ ] 3-4 paper strategies
- [ ] Review retirement patterns

### Week 4: Continuous
- [ ] Start continuous mode
- [ ] 3+ live strategies
- [ ] PnL positive
- [ ] Auto-retirement working

---

## 🏆 What Makes This Institutional-Grade?

1. **Rigorous Validation**: OOS, Monte Carlo, Walk-Forward (not just backtest Sharpe)
2. **Portfolio Risk Management**: DD limits, allocation caps, correlation analysis
3. **Continuous Evolution**: Strategies evolve, underperformers retire automatically
4. **Edge Decay Detection**: Compares live vs backtest performance
5. **Complete Audit Trail**: Every decision logged in database
6. **Data-Driven**: No emotions, no gut feelings, only proven statistical performance

---

## 💡 Tips for Success

**Do's**:
✅ Start with paper trading (mandatory 2 weeks)  
✅ Trust the robustness tests  
✅ Diversify (max correlation 0.70)  
✅ Monitor daily, act on kill switches  
✅ Let the system retire strategies automatically  

**Don'ts**:
❌ Skip validation (never deploy unvalidated)  
❌ Override kill switches  
❌ Deploy strategies with Sharpe < 1.0  
❌ Run >10 live strategies (over-diversification)  
❌ Manually edit auto-generated bots  

---

## 🔗 Quick Links

- **Main Entry**: `python scripts/run_factory.py`
- **Complete Demo**: `python scripts/factory_demo.py`
- **Configuration**: `titan_system/factory/factory_config.py`
- **Database**: `data/strategy_factory.db`
- **Docs**: Brain artifacts folder

---

## 📞 Support

See the complete documentation:
- **System Map**: Overview of all components
- **Walkthrough**: Detailed technical guide
- **Quick Reference**: Daily operations cheat sheet

---

## 🎯 Bottom Line

**You've built what hedge funds spend millions and years developing.**

This isn't a simple trading bot - it's a **meta-system** that creates trading bots. It's self-improving, self-managing, and operates 24/7.

The hard part is done. Now let it run and discover edge for you.

---

**🚀 Ready to Start?**

```bash
# See it in action:
python scripts/factory_demo.py

# Then go autonomous:
python scripts/run_factory.py --mode continuous
```

**Welcome to systematic trading at institutional scale.** 🏭✨

---

*Built with: Python, SQLite, TA-Lib, MetaTrader5*  
*License: Your proprietary trading system*  
*Version: 1.0 - Production Ready*
