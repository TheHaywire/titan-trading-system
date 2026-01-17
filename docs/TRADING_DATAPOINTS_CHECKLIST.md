# Trading Datapoints Checklist

> **What to check before backtesting, before trading, and during live execution.**

---

## 1. Symbol Selection (Pre-Backtest)

| Datapoint | Check | Threshold |
|-----------|-------|-----------|
| **Current Spread** | `symbol_info().spread` | < 50 pips |
| **Trade Mode** | `symbol_info().trade_mode` | = 4 (Full) |
| **Volume Min/Max** | `symbol_info().volume_min/max` | Acceptable |
| **Contract Size** | `symbol_info().trade_contract_size` | Know it |
| **Margin Required** | `order_calc_margin()` | Affordable |
| **Data Availability** | `copy_rates()` count | > 500 bars |

---

## 2. Liquidity Assessment

| Datapoint | Check | Notes |
|-----------|-------|-------|
| **Spread Ratio** | spread / price | < 0.05% |
| **Tick Volume** | Average hourly volume | Higher = better |
| **Bid-Ask Gap** | `symbol_info_tick().bid/ask` | Tight |
| **Session Hours** | When is it actively traded? | Know them |
| **Spread by Hour** | Sample spreads at different times | Build profile |

---

## 3. Backtest Reality Checks

| Datapoint | Include? | How |
|-----------|----------|-----|
| **Spread Cost** | ✅ YES | Deduct from every trade |
| **Slippage** | ✅ YES | Add 0.5-1 pip per trade |
| **Commission** | ✅ YES | If broker charges |
| **Swap/Rollover** | ✅ YES | For overnight holds |
| **Realistic Fills** | ✅ YES | No perfect entries |

---

## 4. Pre-Trade Checks (Live)

### Market Conditions
| Check | Threshold | Action |
|-------|-----------|--------|
| **Current Spread** | < 2x normal | Proceed |
| **Current Spread** | > 2x normal | WAIT |
| **News in ±30min** | High-impact | SKIP |
| **Market Hours** | Active session | Proceed |
| **Volatility (ATR)** | Normal range | Proceed |

### Position Size
| Check | Formula |
|-------|---------|
| **Risk Amount** | Account × 1% |
| **Stop Distance** | Entry - SL (in pips) |
| **Lot Size** | Risk / (Stop × Pip Value) |
| **Max Lots** | Never exceed 5% account margin |

---

## 5. Time-Based Filters

### Best Trading Hours (UTC)
| Session | Time | Best For |
|---------|------|----------|
| London Open | 08:00-09:00 | Breakouts |
| **London+NY Overlap** | 13:00-17:00 | **TIGHTEST SPREADS** |
| NY Close | 20:00-21:00 | Avoid |
| Asian Session | 00:00-07:00 | Avoid EUR/USD |

### Avoid
- ❌ First 15 min of any session (volatile)
- ❌ Last 30 min before close (thin liquidity)
- ❌ Fridays after 18:00 UTC (weekend gap risk)
- ❌ ±30 min around high-impact news

---

## 6. News Calendar Integration

| Event Type | Spread Impact | Action |
|------------|---------------|--------|
| NFP | 5-10x wider | NO TRADE ±30min |
| FOMC | 10x+ wider | NO TRADE ±60min |
| CPI/PPI | 3-5x wider | NO TRADE ±15min |
| GDP | 2-3x wider | Caution |
| PMI | 2x wider | Caution |

---

## 7. Strategy Validation Gates

| Metric | Minimum | Reject If |
|--------|---------|-----------|
| **Trade Count** | > 30 | < 10 (not significant) |
| **Sharpe Ratio** | > 1.5 | < 1.0 or > 5.0 (overfitting) |
| **Win Rate** | > 45% | < 40% |
| **Profit Factor** | > 1.5 | < 1.2 |
| **Max Drawdown** | < 20% | > 30% |
| **Avg Trade Duration** | Reasonable | Extremes |

---

## 8. Live Execution Monitoring

| Metric | Track | Alert If |
|--------|-------|----------|
| **Slippage** | Per trade | > 2 pips avg |
| **Fill Time** | Milliseconds | > 500ms |
| **Rejection Rate** | % of orders | > 5% |
| **Actual vs Expected P&L** | Compare | > 10% deviation |
| **Spread at Entry** | Log it | Wider than expected |

---

## 9. Portfolio-Level Checks

| Check | Threshold |
|-------|-----------|
| **Correlation** | < 0.5 between strategies |
| **Max Concurrent Trades** | ≤ 5 |
| **Max Risk Per Symbol** | 2% of account |
| **Total Portfolio Heat** | < 6% of account |
| **Sector Concentration** | Diversify |

---

## 10. Data Quality Checks

| Issue | Detection | Solution |
|-------|-----------|----------|
| **Gaps in Data** | Missing bars | Interpolate or skip |
| **Outlier Spikes** | > 10 ATR move | Flash crash - exclude |
| **Weekend Gaps** | Sunday open ≠ Friday close | Factor into backtest |
| **Dividend/Split** | Sudden price jump | Adjust historical data |

---

## Quick Reference: What MT5 Provides

```python
# Symbol Info
info = mt5.symbol_info(symbol)
info.spread          # Current spread in points
info.trade_mode      # 0=disabled, 4=full trading
info.volume_min      # Minimum lot size
info.volume_max      # Maximum lot size
info.trade_contract_size  # Contract size
info.digits          # Decimal places

# Current Tick
tick = mt5.symbol_info_tick(symbol)
tick.bid             # Current bid
tick.ask             # Current ask
tick.volume          # Last tick volume
tick.time            # Timestamp

# Historical Data
rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
# Returns: time, open, high, low, close, tick_volume, spread, real_volume
```

---

## The Golden Rule

> **If you wouldn't manually trade it at this exact moment with this exact spread, don't let the bot trade it either.**

---

*Last Updated: 2026-01-16*
