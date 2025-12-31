# Risk Management

## Overview

Titan implements **multiple layers of risk protection**:
1. Circuit Breaker
2. Position sizing
3. Correlation limits
4. Auto break-even
5. Max exposure caps

## Layer 1: Circuit Breaker

### Daily Loss Limit
- **Threshold**: 5% of starting equity
- **Action**: Halts all new trades
- **Recovery**: Resets next trading day

### Example
```
Starting Equity: $10,000
Max Loss: 5% = $500

If equity drops to $9,500:
- ⛔ Trading HALTED
- ✅ Can still manage existing positions
- ✅ Resumes next day
```

### Consecutive Loss Limit
- **Threshold**: 5 losing trades in a row
- **Action**: Pause trading for 1 hour
- **Rationale**: System might be out of sync with market

## Layer 2: Position Sizing

### Per-Trade Risk
- **Fixed**: 0.5% of equity per trade
- **Calculation**: Dynamic, scales with account size

### Formula
```python
risk_amount = current_equity × 0.005
lot_size = risk_amount / (sl_distance × tick_value)
```

### Benefits
- Small accounts protected (min lots)
- Large accounts scale up appropriately
- Consistent risk across all symbols

### Example Scenarios

| Equity | Risk (0.5%) | SL (pips) | Lot Size |
|--------|-------------|-----------|----------|
| $1,000 | $5 | 50 | 0.10 |
| $10,000 | $50 | 50 | 1.00 |
| $100,000 | $500 | 50 | 10.00 |

## Layer 3: Correlation Limits

### Currency Groups
```python
CORRELATION_GROUPS = {
    "USD": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"],
    "JPY": ["USDJPY", "EURJPY", "GBPJPY"],
    "GOLD": ["GOLD", "XAUUSD"],
    "CRYPTO": ["BTCUSD", "ETHUSD"]
}
```

### Rule
- **Max 2 positions per group**
- Prevents concentrated exposure

### Example
```
Current:
- EURUSD SELL (USD group)
- GBPUSD SELL (USD group)

New Signal:
- USDJPY BUY (USD group)
❌ REJECTED - USD group at max (2)
```

## Layer 4: Auto Break-Even

### Logic
```
IF profit_per_lot > $100:
    move_sl_to_entry_price()
```

### Benefits
- Locks in zero-loss minimum
- Psychological comfort
- Lets winners run

### Example
```
EURUSD BUY @ 1.1000
- Initial SL: 1.0950
- TP: 1.1100

Price moves to 1.1050:
- Profit: $50/lot
- SL: Still 1.0950 (no change yet)

Price moves to 1.1100:
- Profit: $100/lot
- SL: Moved to 1.1000 (break-even) ✅
```

## Layer 5: Maximum Exposure

### Position Limits
- **Max positions**: 8 at once
- **Max per symbol**: 1 position
- **Total risk cap**: 5% of equity

### Calculation
```
8 positions × 0.5% each = 4% total risk < 5% cap ✅
```

## Monitoring & Alerts

### Real-Time Checks (Every Cycle)
1. Account equity
2. Open position count
3. P/L per position
4. Circuit breaker status

### Telegram Alerts
- Circuit breaker triggered
- Position opened
- Position moved to break-even
- Daily summary

## Risk Scenarios

### Scenario 1: Multiple Losing Trades
```
Trade 1: -$50 (EURUSD)
Trade 2: -$50 (GBPUSD)
Trade 3: -$50 (USDJPY)
Trade 4: -$50 (AUDUSD)
Trade 5: -$50 (GOLD)

Total Loss: -$250 (2.5% of $10k)

Action: Continue trading (under 5% limit)
```

### Scenario 2: Daily Limit Hit
```
Starting: $10,000
Losses: -$520

Current: $9,480 (5.2% drawdown)

Action: ⛔ HALT TRADING
- No new positions
- Manage existing only
```

### Scenario 3: Correlation Breach
```
Open:
- EURUSD SELL
- GBPUSD SELL

Signal: AUDUSD SELL

Issue: All 3 are USD pairs (correlated)

Action: ❌ Reject AUDUSD
```

## Disaster Recovery

### If Circuit Breaker Triggered
1. Review what happened
2. Check market conditions (news, volatility)
3. Verify strategy still valid
4. Wait for next trading day
5. Resume with reduced size if uncertain

### If Major Slippage
1. Check broker execution quality
2. Verify spread was acceptable
3. Consider symbol-specific spread limits
4. Report to broker if egregious

## Best Practices

### Do's
- ✅ Let the bot run continuously
- ✅ Monitor Telegram alerts
- ✅ Check database logs daily
- ✅ Respect circuit breaker

### Don'ts
- ❌ Override circuit breaker
- ❌ Manually adjust positions
- ❌ Increase risk beyond 1% per trade
- ❌ Trade during major news events

## Key Metrics to Track

Daily:
- Win rate
- Avg R
- Max drawdown
- Circuit breaker hits

Weekly:
- Profit factor
- Sharpe ratio
- Symbol performance
- Time-of-day patterns

## FAQs

**Q: Can I increase risk to 2% per trade?**
A: Not recommended. Higher risk = higher drawdowns = earlier circuit breaker.

**Q: Why auto break-even at $100/lot?**
A: Empirically found to balance protection vs letting winners run.

**Q: What if all 8 positions are losing?**
A: Max loss = 8 × 0.5% = 4% < 5% circuit breaker threshold.

**Q: Can I disable circuit breaker?**
A: Yes, but highly discouraged. It's your safety net.
