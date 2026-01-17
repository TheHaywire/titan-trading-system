# Section 01: MetaTrader 5 Platform Fundamentals

**Owner**: Platform Architect  
**Status**: ✅ Complete (85%)  
**Last Updated**: 2026-01-12

---

## 🎯 Objective

Document MT5 like a bank would: complete technical architecture, symbol properties, order/position models, and algorithmic trading capabilities. This section serves as the foundational knowledge base for all MT5 interactions.

---

## 1. What is MT5 and Why Institutions Use It

### Platform Overview
MetaTrader 5 is a **multi-asset, multi-currency trading platform** designed for:
- ✅ **Forex, Indices, Commodities, Stocks, Futures, CFDs, Crypto**
- ✅ **Netting and Hedging** account modes for different risk approaches
- ✅ **Built-in Strategy Tester** with tick-by-tick backtesting
- ✅ **Depth of Market (DOM)** for Level II pricing
- ✅ **Economic Calendar** integration
- ✅ **Algorithmic Trading** via MQL5 and external APIs (Python, C++, REST)

### Institutional Advantages
- **Multi-threading**: Parallel execution of EAs and indicators
- **High-frequency capability**: Sub-millisecond execution times
- **Risk controls**: Built-in margin management and position limits
- **Audit trail**: Complete trade history and reporting
- **Scalability**: Supports thousands of symbols and concurrent strategies

---

## 2. MT5 Technical Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    MT5 ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Client       │ ◄─────► │ Access       │                 │
│  │ Terminal     │         │ Server       │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                         │                         │
│         │                         ▼                         │
│         │                 ┌──────────────┐                 │
│         │                 │ Dealing      │                 │
│         │                 │ Server       │                 │
│         │                 └──────────────┘                 │
│         │                         │                         │
│         ▼                         ▼                         │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ History      │         │ Data Center  │                 │
│  │ Server       │         │ (Liquidity)  │                 │
│  └──────────────┘         └──────────────┘                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

#### Client Terminal
- **Location**: Trader's local machine (Windows/Linux/Mac)
- **Functions**: Chart display, order entry, EA execution, indicator calculations
- **Data Storage**: Local cache of price history (compact binary format)
- **Python Bridge**: IPC mechanism for external API access

#### Access Server
- **Functions**: Authentication, encryption, client-to-server routing
- **Protocols**: Proprietary TCP/IP with SSL/TLS
- **Load Balancing**: Distributes clients across dealing servers

#### Dealing Server
- **Functions**: Order execution, position management, margin calculations
- **Execution Modes**: Instant, Request, Market, Exchange
- **Risk Engine**: Real-time margin checks, stop-out calculations

#### History Server
- **Data Storage**: Tick data, minute/hour/day bars per symbol
- **Retention**: Configurable (typically 1-5 years of history)
- **Compression**: Tick data stored in compact binary format

#### Data Center
- **Liquidity Providers**: Banks, ECNs, exchanges
- **Price Aggregation**: Best bid/offer from multiple sources
- **Latency**: Sub-millisecond to liquidity providers

### Price Data Storage

**Format**: Compact binary per symbol/timeframe
- **Tick data**: Time, Bid, Ask, Last, Volume, Flags
- **Bar data**: Time, Open, High, Low, Close, Tick Volume, Spread, Real Volume
- **Scalability**: Efficient storage for 1000+ symbols with years of history

---

## 3. Symbol Properties (Critical for Trading & Risk)

### Complete Property List

| Property | Description | Example | Usage |
|----------|-------------|---------|-------|
| **point** | Minimum price increment | 0.00001 (EURUSD) | Price precision |
| **tick_size** | Minimum price change for quotes | 0.01 (XAUUSD) | Order price validation |
| **tick_value** | Profit/loss per tick | $0.01 (Gold mini) | P&L calculations |
| **contract_size** | Lot size in base currency | 100,000 (Forex) | Position sizing |
| **volume_min** | Minimum order volume | 0.01 lots | Order validation |
| **volume_max** | Maximum order volume | 500 lots | Position limits |
| **volume_step** | Volume increment | 0.01 lots | Lot rounding |
| **trade_tick_size** | Minimum price step for trades | 0.01 | SL/TP validation |
| **margin_initial** | Initial margin requirement | 1% | Leverage calculation |
| **margin_maintenance** | Maintenance margin | 0.5% | Stop-out levels |
| **swap_long** | Overnight fee for buy | -1.5 points | Cost modeling |
| **swap_short** | Overnight fee for sell | 0.8 points | Carry trade analysis |
| **trade_mode** | Execution mode | FULL, CLOSE_ONLY | Trading restrictions |
| **digits** | Decimal places in price | 5 (Forex), 2 (Gold) | Display formatting |
| **spread** | Current bid-ask difference | 1.5 pips | Transaction cost |
| **session_deals** | Trading session hours | "00:00-23:59" | Time filters |
| **filling_mode** | Order fill policies | FOK, IOC, RETURN | Execution policy |

### Python Extraction

```python
import MetaTrader5 as mt5

def get_symbol_spec(symbol: str) -> dict:
    """Extract complete symbol specification."""
    info = mt5.symbol_info(symbol)
    if info is None:
        return None
    
    return {
        "symbol": symbol,
        "tick_size": info.trade_tick_size,
        "tick_value": info.trade_tick_value,
        "contract_size": info.trade_contract_size,
        "volume_min": info.volume_min,
        "volume_max": info.volume_max,
        "volume_step": info.volume_step,
        "point": info.point,
        "digits": info.digits,
        "spread": info.spread,
        "margin_initial": info.margin_initial,
        "swap_long": info.swap_long,
        "swap_short": info.swap_short,
        "trade_mode": info.trade_mode,
    }
```

**Reference**: `titan_system/core/symbol_catalog.py`

---

## 4. Order and Position Model

### Order Types

#### Market Orders
- **Execution**: Immediate at current market price
- **Slippage Risk**: Yes (especially in volatile markets)
- **Use Case**: Time-sensitive entries, stop-outs

#### Limit Orders
- **Execution**: At specified price or better
- **Slippage Risk**: No (but may not fill)
- **Use Case**: Better entry prices, scaling in

#### Stop Orders
- **Execution**: Triggered when market reaches price, then filled as market order
- **Slippage Risk**: Yes (after trigger)
- **Use Case**: Breakout entries, stop-losses

#### Stop-Limit Orders
- **Execution**: Triggered at stop price, filled as limit order
- **Slippage Risk**: May not fill if price gaps through limit
- **Use Case**: Controlled breakout entries

### Stop Loss & Take Profit
- **Attached to order**: SL/TP sent with order request
- **Minimum distance**: Broker-defined (e.g., 10 points for EURUSD)
- **Modification**: Can be adjusted on live positions
- **Trailing Stop**: Dynamic SL that follows favorable price movement

### Netting vs Hedging Accounts

#### Netting (MT5 Default)
- **One position per symbol**: Opposite orders net out
- **Example**: Buy 1 lot + Sell 0.5 lot = Net long 0.5 lot
- **Advantage**: Simpler P&L tracking, lower margin
- **Use Case**: Directional strategies, institutional portfolios

#### Hedging
- **Multiple positions per symbol**: Each trade is independent
- **Example**: Buy 1 lot + Sell 0.5 lot = 2 separate positions
- **Advantage**: More complex strategies (grid, martingale)
- **Use Case**: Hedging, lock-in strategies

**Titan System**: Uses **netting** for institutional simplicity.

---

## 5. Built-in Algorithmic Layer (MQL5)

### MQL5 Overview
- **Language**: Object-oriented, C++-like syntax
- **Execution Speed**: Near-native (compiled to machine code)
- **Components**: Expert Advisors (EAs), Indicators, Scripts
- **Event-driven**: OnTick, OnTimer, OnTrade, OnTester events

### Integration Points
- **Python + MQL5**: Hybrid approach (Python for ML/data, MQL5 for speed-critical execution)
- **Custom Indicators**: Can be called from Python via MT5 API
- **Strategy Tester**: MQL5 EAs can be backtested, Python strategies cannot (natively)

**Titan System Approach**: Pure Python for flexibility; fallback MQL5 for ultra-low latency if needed.

---

## 📚 Cross-References

### MT5 Official Documentation
- **Architecture**: [MetaTrader 5 Architecture](https://www.metatrader5.com/en/automated-trading/architecture)
- **Trade Operations**: [MQL5 Trading Functions](https://www.mql5.com/en/docs/trading)
- **Symbol Info**: [SymbolInfo Structure](https://www.mql5.com/en/docs/constants/structures/symbolinfo)
- **Error Codes**: [Trade Server Return Codes](https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes)

### MQL5 Book Sections
- **Chapter 2**: Platform Architecture and Data Model
- **Chapter 5**: Trading Operations and Order Management
- **Chapter 12**: Strategy Tester and Optimization

### Broker Documentation
- **Validation Required**: Extract symbol specs from live broker (demo + production)
- **Symbol List**: Request current tradeable universe from broker support
- **Contract Specs**: Download PDFs for all instruments

---

## ✅ Validation Checklist

- [ ] All symbol properties documented and extracted via Python
- [ ] Order type behavior tested on demo account
- [ ] Netting mode confirmed for account
- [ ] Minimum SL/TP distances validated per symbol
- [ ] MT5 architecture diagram reviewed with team
- [ ] Cross-references to official docs verified
- [ ] Broker-specific symbol specs downloaded

---

## 🚨 Known Gaps

1. **Exchange execution mode**: Not fully tested (futures-specific)
2. **Corporate actions**: Stock dividend/split handling needs documentation
3. **Multi-currency accounting**: Base currency conversion rules need verification

**Next Actions**: Complete validation checklist, update gaps section after broker confirmation.
