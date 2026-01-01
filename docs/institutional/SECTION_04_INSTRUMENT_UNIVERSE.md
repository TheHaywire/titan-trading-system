# Section 04: Instrument Universe & Symbol Catalog

**Owner**: Universe Manager  
**Status**: ✅ Complete (85%)  
**Last Updated**: 2026-01-01

---

## 🎯 Objective

Maintain a comprehensive, validated catalog of all tradeable instruments across FX, indices, commodities, stocks, CFDs, and crypto. Assign strategies to symbols based on their characteristics and validate against broker specifications.

---

## 1. Asset Classes Enumeration

### Complete Universe

| Asset Class | Symbols | Examples | Characteristics |
|-------------|---------|----------|-----------------|
| **Forex Majors** | 7 pairs | EURUSD, GBPUSD, USDJPY | High liquidity, tight spreads |
| **Forex Minors** | 14 pairs | EURGBP, AUDNZD | Medium liquidity |
| **Forex Exotics** | 20+ pairs | USDTRY, ZARJPY | Wide spreads, volatile |
| **Indices** | 15+ | US30, US100, GER40, UK100 | Stock market indices, session-dependent |
| **Commodities** | 10+ | XAUUSD (Gold), XAGUSD (Silver), USOIL | Supply/demand driven |
| **Crypto** | 5+ | BTCUSD, ETHUSD, XRPUSD | 24/7, high volatility |
| **Stocks** | 50+ | AAPL, TSLA, GOOGL | Company-specific, earnings events |

**Total Universe**: ~1500 symbols scanned

---

## 2. Symbol Catalog (JSON Format)

### Per-Symbol Specification

```json
{
  "symbol": "XAUUSD",
  "description": "Gold vs US Dollar",
  "asset_class": "Commodities",
  "tick_size": 0.01,
  "tick_value": 0.01,
  "contract_size": 100,
  "volume_min": 0.01,
  "volume_max": 500.0,
  "volume_step": 0.01,
  "point": 0.01,
  "digits": 2,
  "spread_avg": 2.5,
  "swap_long": -15.0,
  "swap_short": 5.0,
  "margin_initial": 1.0,
  "trade_mode": "FULL",
  "sessions": {
    "monday": "00:00-23:59",
    "friday": "00:00-23:55"
  },
  "strategy_assignment": ["InstitutionalGold", "BookTechnical"],
  "notes": "High volatility during London/NY overlap"
}
```

**Storage**: `data/symbol_catalog.json`

---

## 3. "Fat Tail" Opportunities (Top 20)

Based on 1500-symbol backtest, these show highest expectancy:

### Top Ranked Symbols

| Rank | Symbol | Asset Class | Expectancy | Sharpe | Strategy |
|------|--------|-------------|------------|--------|----------|
| 1 | XAUUSD | Commodities | 0.85R | 2.1 | BookTechnical |
| 2 | US100 | Indices | 0.72R | 1.8 | Momentum |
| 3 | BTCUSD | Crypto | 0.68R | 1.6 | Breakout |
| 4 | GER40 | Indices | 0.65R | 1.9 | London Open |
| 5 | GBPUSD | Forex | 0.58R | 1.7 | BookTechnical |
| ... | ... | ... | ... | ... | ... |

**Reference**: [FAT_TAIL_OPPORTUNITIES.md](../FAT_TAIL_OPPORTUNITIES.md)

---

## 4. Strategy-Symbol Assignment Rules

### Assignment Matrix

```python
STRATEGY_ASSIGNMENTS = {
    "BookTechnical": {
        "asset_classes": ["Commodities", "Indices", "Forex"],
        "min_expectancy": 0.40,
        "max_spread": 5.0,
        "requirements": "Trending markets, clear support/resistance"
    },
    "InstitutionalGold": {
        "symbols": ["XAUUSD", "XAGUSD"],
        "requirements": "Multi-timeframe analysis, H4 trend alignment"
    },
    "MomentumBreakout": {
        "asset_classes": ["Indices", "Crypto"],
        "min_avg_daily_range": 100,  # points
        "requirements": "High volatility, clear session patterns"
    }
}
```

### Blacklist

Symbols **NOT** allowed for automated trading:
- Exotic FX with spread > 10 pips
- Illiquid stocks (volume < 1M shares/day)
- News-sensitive symbols during high-impact events

---

## 5. Broker Validation

### Validation Checklist

For each symbol in catalog:
- [x] Verify symbol exists on broker MT5 server
- [x] Extract tick_size, tick_value, contract_size from MT5
- [x] Confirm trading sessions match broker schedule
- [x] Test order placement on demo account
- [ ] Quarterly refresh (next: April 2026)

### Validation Script

```python
import MetaTrader5 as mt5
import json

def validate_symbol_catalog():
    """Validate all symbols against live broker."""
    with open('data/symbol_catalog.json', 'r') as f:
        catalog = json.load(f)
    
    discrepancies = []
    
    for symbol_entry in catalog:
        symbol = symbol_entry['symbol']
        info = mt5.symbol_info(symbol)
        
        if info is None:
            discrepancies.append(f"{symbol}: NOT FOUND on broker")
            continue
        
        # Check tick size
        if abs(info.trade_tick_size - symbol_entry['tick_size']) > 0.0001:
            discrepancies.append(
                f"{symbol}: tick_size mismatch "
                f"(catalog: {symbol_entry['tick_size']}, broker: {info.trade_tick_size})"
            )
    
    return discrepancies
```

---

## 6. Trading Sessions

### Major Session Times (GMT+0)

| Session | Open | Close | Active Symbols |
|---------|------|-------|----------------|
| **Sydney** | 22:00 | 07:00 | AUDUSD, NZDUSD |
| **Tokyo** | 00:00 | 09:00 | USDJPY, Nikkei |
| **London** | 08:00 | 16:30 | GBPUSD, GER40, XAUUSD |
| **New York** | 13:00 | 22:00 | US30, US100, USOIL |
| **Overlap (London+NY)** | 13:00 | 16:30 | All major pairs |

**Key**: Overlap periods = highest liquidity = tightest spreads

---

## 📚 Cross-References

### Broker Documentation
- Symbol specifications from broker website
- Trading hours official schedule
- Margin requirements PDF

### Titan System
- **Symbol Catalog**: `data/symbol_catalog.json`
- **Fat Tail Report**: `docs/FAT_TAIL_OPPORTUNITIES.md`
- **Strategy Assignment**: `titan_system/config/strategy_symbols.py`

---

## ✅ Validation Checklist

- [x] Asset classes enumerated
- [x] Symbol catalog created (JSON)
- [x] Fat Tail Top 20 identified
- [x] Strategy-symbol assignments defined
- [x] Broker validation completed
- [ ] Quarterly refresh scheduled (April 2026)

---

**Status**: 85% complete | Quarterly maintenance required
