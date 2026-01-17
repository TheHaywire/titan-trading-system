---
name: Strategy Council
description: Multi-perspective AI council for designing, validating, and improving trading strategies with 5 specialized agents.
---

# Strategy Council Skill

A multi-agent discussion framework for rigorous strategy evaluation. Each "agent" represents a specialized perspective that challenges and validates trading strategies.

## The Five Agents

1. **The Quant** 🧮 - Statistical rigor, Sharpe, p-values, sample size
2. **The Risk Manager** 🛡️ - Drawdown, position sizing, tail risk  
3. **The Execution Specialist** ⚡ - Spreads, slippage, liquidity
4. **The Regime Analyst** 🌊 - Market conditions, when strategies work
5. **The Devil's Advocate** 😈 - Breaking strategies, finding weaknesses

## How To Use

### In Workflow (via /council):
Use the `/council` workflow to initiate a council session.

### Programmatically:
```python
from scripts.strategy_council import StrategyCouncil

council = StrategyCouncil()
result = council.evaluate_strategy(
    symbol="GOLD",
    strategy_type="breakout",
    strategy_params={"atr_mult": 2, "timeframe": "H1"}
)
print(result["verdict"])  # APPROVED, CONDITIONAL, REJECTED
```

## Council Outputs

Each session produces:
- Individual agent analyses
- Combined synthesis
- Final verdict (APPROVED/CONDITIONAL/REJECTED)
- Action items for improvement

## Integration

The council uses real market intelligence from:
- `titan_system/core/comprehensive_intel.py` - Live spread/ATR data
- `config/alpha_registry.json` - Historical validated edges
- `data/market_intelligence_export.json` - Symbol profiles
