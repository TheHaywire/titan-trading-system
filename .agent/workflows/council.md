---
description: Initiate a multi-perspective Strategy Council discussion to design, validate, or improve trading strategies
---

# /council - Strategy Council Discussion

Initiate a multi-agent "Strategy Council" to collaboratively discuss and validate trading strategies. Each "agent" perspective provides unique insight.

## The Council Members

The council consists of 5 specialized perspectives:

### 🧮 Agent 1: The Quant
- Focus: Statistical validation, Sharpe ratio, p-values, sample size
- Questions asked:
  - "What's the Sharpe ratio and profit factor?"
  - "How many trades in backtest? Is it statistically significant?"
  - "What's the out-of-sample performance?"
  - "Is this curve-fitted to historical data?"

### 🛡️ Agent 2: The Risk Manager  
- Focus: Drawdown, position sizing, correlation, tail risk
- Questions asked:
  - "What's the maximum drawdown?"
  - "What happens after 7 consecutive losses?"
  - "How correlated is this with existing strategies?"
  - "What's the worst-case scenario?"

### ⚡ Agent 3: The Execution Specialist
- Focus: Spreads, slippage, fill quality, liquidity
- Questions asked:
  - "What's the spread ratio for this symbol?"
  - "Can we actually execute at backtest prices?"
  - "What's the expected slippage?"
  - "Is there enough liquidity for our position size?"

### 🌊 Agent 4: The Regime Analyst
- Focus: Market conditions, when strategies work/fail
- Questions asked:
  - "Does this work in trending AND ranging markets?"
  - "What's the performance during high volatility?"
  - "Which sessions does this perform best in?"
  - "How does it behave around news events?"

### 😈 Agent 5: The Devil's Advocate
- Focus: Breaking strategies, finding weaknesses
- Questions asked:
  - "Why would this edge disappear?"
  - "What if the market structure changes?"
  - "Is this just luck or survivorship bias?"
  - "What's the counterparty doing that we're not seeing?"

## How to Use

### For New Strategy Design:
```
/council [SYMBOL] [STRATEGY_TYPE]
Example: /council GOLD breakout
```

### For Strategy Validation:
```
/council validate [STRATEGY_NAME]
Example: /council validate momentum_scalper
```

### For Strategy Improvement:
```
/council improve [STRATEGY_NAME]
Example: /council improve gold_mean_reversion
```

## Council Process

1. **Intel Gathering**: Pull market intelligence for the symbol(s)
   - Spread ratio, ATR, adrenaline score
   - Session profiles
   - Swap rates
   
2. **Each Agent Reviews**: Simulate each perspective's analysis

3. **Synthesis**: Combine all perspectives into actionable recommendations

4. **Verdict**: 
   - ✅ APPROVED - Ready for paper trading
   - ⚠️ CONDITIONAL - Needs specific improvements
   - ❌ REJECTED - Fundamental flaws identified

## Example Output Format

```markdown
## 🏛️ STRATEGY COUNCIL SESSION

**Strategy:** [Name]
**Symbol:** [Symbol]
**Type:** [Scalp/Swing/Position]

---

### 🧮 THE QUANT SAYS:
[Quantitative analysis and verdict]

### 🛡️ THE RISK MANAGER SAYS:
[Risk analysis and concerns]

### ⚡ THE EXECUTION SPECIALIST SAYS:
[Execution feasibility assessment]

### 🌊 THE REGIME ANALYST SAYS:
[Market condition analysis]

### 😈 THE DEVIL'S ADVOCATE SAYS:
[Challenges and potential failure modes]

---

## COUNCIL VERDICT: [APPROVED/CONDITIONAL/REJECTED]

**Reasoning:** [Summary]

**Action Items:**
1. [Specific improvement or next step]
2. [Another action]
```

## Integration with Market Intelligence

The Council automatically uses data from:
- `data/comprehensive_intel.db` - Real-time spread/ATR/session data
- `config/alpha_registry.json` - Validated edges
- `data/market_intelligence_export.json` - Symbol profiles
