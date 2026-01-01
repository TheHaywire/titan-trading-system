# 🚀 Operational Alpha - Quick Start Guide

This guide helps you validate and run the newly deployed Growth Architecture.

## Phase 2 Components (Live)

### 1. Trade Lifecycle Management
- **Partial Profits**: Automatically closes 50% at 1:1 R:R
- **Break-Even**: Moves SL to entry + 5 ticks after first target
- **ATR Trailing**: Dynamic 2x ATR trailing stops

### 2. Growth Architecture
- **Alpha Optimizer**: Selects best strategy per market regime
- **Winner Scaling**: 1.5x lot size on symbols with >$200 expectancy
- **Drawdown Defense**: 30% risk reduction when Equity < Balance

## Pre-Flight Checklist

### Step 1: Validate Components
```powershell
python scripts/validate_operational_alpha.py
```

**Expected Output**:
```
✅ TradeManager: PASSED
✅ AlphaOptimizer: PASSED
✅ AllocationAgent: PASSED
✅ Database: PASSED
🎉 ALL SYSTEMS GO - Ready for Operational Alpha
```

### Step 2: Review Configuration
Check `config/settings.py`:
- `enable_trading = True` (for live) or `False` (for paper mode)
- `risk_per_trade = 0.015` (1.5% base risk)
- `max_daily_loss_percent = 5.0` (Circuit breaker threshold)

### Step 3: Start the Engine
```powershell
python main_loop.py
```

## What to Monitor

### In the Terminal Dashboard
1. **Market Regime**: Watch for "Regime=TREND_STRONG" or "MEAN_REVERSION"
2. **Scaling Decisions**: Look for "🚀 WINNER: Would apply 1.5x scaling"
3. **Lifecycle Triggers**: Watch for "🎯 1:1 RR Target Hit"
4. **Drawdown Protection**: Monitor "📉 Drawdown detected"

### Key Log Messages
```
🔮 Alpha Optimizer [XAUUSD]: Regime=TREND_STRONG -> Recommendation=InstitutionalGold
🎯 Allocation: EURUSD | Confidence: 0.75 | Result: 0.05 Lots
🎯 1:1 RR Target Hit for EURUSD (12345)
💰 Scaled out 50% (0.025 lots) on EURUSD
🛡️ Position 12345 moved to Break-Even
📈 Trailing Buy SL Up: EURUSD -> 1.0850
```

## Testing Strategy

### Paper Trading Mode
1. Set `enable_trading = False` in config
2. Run for 24 hours
3. Review logs for regime transitions and allocation decisions

### Demo Account
1. Use a broker demo account ($10,000 balance)
2. Enable trading
3. Monitor for 1 week
4. Verify:
   - Partial closes execute correctly
   - Break-even moves are accurate
   - Scaling multiplier is applied

### Live (Small Capital)
1. Start with $1,000-$5,000
2. Monitor closely for 2 weeks
3. Gradually increase capital as confidence builds

## Troubleshooting

### Issue: "No Active Universe found"
**Solution**: Run `python scripts/broker_universe_scan.py` to populate database

### Issue: "Database locked"
**Solution**: Close any other scripts accessing the database

### Issue: "Position modification failed"
**Solution**: Ensure MT5 Desktop is running and connected to broker

## Performance Metrics

Track these KPIs weekly:
- **Account Growth Rate**: Target 5-10% monthly
- **Max Drawdown**: Should stay <10% (Kill Switch triggers at 10%)
- **Win Rate**: Aim for >50% with 2:1 R:R
- **Scaling Frequency**: % of trades that get 1.5x multiplier

## Safety Systems

### Active Protection:
1. **Circuit Breaker**: Stops trading at 5% daily loss
2. **Kill Switch**: Full shutdown at 10% account drawdown
3. **Drawdown Defense**: Risk reduction when losing
4. **Self-Audit**: Blacklists losers every 4 hours

## Next Steps

After validation:
1. ✅ Review validation results
2. ✅ Configure risk parameters
3. ✅ Start in paper/demo mode
4. ✅ Monitor for 1 week
5. ✅ Graduate to live with small capital

## Support & Documentation

- **Project Board**: `PROJECT_BOARD.md`
- **Growth Schema**: `docs/operational/ALPHA_OPTIMIZATION_SCHEMA.md`
- **Master Plan**: `docs/INSTITUTIONAL_MASTER_PLAN.md`
- **GitHub**: https://github.com/TheHaywire/titan-trading-system

---

**Current Status**: Operational Alpha - Ready for validation testing
**Last Updated**: 2026-01-01
