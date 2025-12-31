# Architecture

## System Overview

Titan uses a **simplified QuantAI architecture** that combines:
1. Proven trading logic (RSI, EMA, Momentum)
2. Intelligent execution decisions
3. Institutional risk management
4. Clean, maintainable code

```
┌───────────────────────────────────────────┐
│         Titan Production Bot              │
├───────────────────────────────────────────┤
│                                           │
│  ┌─────────────────────────────────────┐ │
│  │   MARKET SCANNING (M15)             │ │
│  │   - 8 curated symbols               │ │
│  │   - Every 2 minutes                 │ │
│  └─────────────────────────────────────┘ │
│                  ↓                        │
│  ┌─────────────────────────────────────┐ │
│  │   SIGNAL GENERATION                 │ │
│  │   - RSI extremes (<15, >85)         │ │
│  │   - EMA crossovers                  │ │
│  │   - Momentum breaks                 │ │
│  └─────────────────────────────────────┘ │
│                  ↓                        │
│  ┌─────────────────────────────────────┐ │
│  │   EXECUTION DECISION AGENT          │ │
│  │   - Validates signal quality        │ │
│  │   - Checks correlation limits       │ │
│  │   - Approves/rejects                │ │
│  └─────────────────────────────────────┘ │
│                  ↓                        │
│  ┌─────────────────────────────────────┐ │
│  │   CIRCUIT BREAKER                   │ │
│  │   - Daily loss limit (5%)           │ │
│  │   - Max positions (8)               │ │
│  │   - Correlation caps                │ │
│  └─────────────────────────────────────┘ │
│                  ↓                        │
│  ┌─────────────────────────────────────┐ │
│  │   MT5 EXECUTION                     │ │
│  │   - Dynamic position sizing         │ │
│  │   - Spread checks                   │ │
│  │   - Order placement                 │ │
│  └─────────────────────────────────────┘ │
│                  ↓                        │
│  ┌─────────────────────────────────────┐ │
│  │   POSITION MANAGEMENT               │ │
│  │   - Auto break-even (>$100/lot)     │ │
│  │   - Profit tracking                 │ │
│  │   - SQLite logging                  │ │
│  └─────────────────────────────────────┘ │
│                                           │
└───────────────────────────────────────────┘
```

## Core Components

### 1. Market Scanning
- **Timeframe**: M15 (15 minutes)
- **Symbols**: 8 liquid instruments
- **Frequency**: Every 2 minutes

### 2. Signal Generation
Strict criteria for high-quality signals:
- RSI < 15 or > 85 (extreme levels)
- EMA crossover + momentum confirmation
- Minimum score: 85/100

### 3. Execution Agent
Validates each signal before execution:
- Symbol not correlated with existing positions
- Score meets threshold
- Risk limits not exceeded

### 4. Circuit Breaker
Safety mechanism:
- Halts trading at 5% daily loss
- Prevents over-leverage
- Enforces correlation limits

### 5. Position Management
Automatic profit protection:
- Moves SL to break-even when profit > $100/lot
- Monitors all open positions
- Logs every trade to database

## Data Flow

```python
while True:
    # 1. Safety check
    if not circuit_breaker.is_safe():
        continue
    
    # 2. Scan markets
    for symbol in UNIVERSE:
        signal = analyze(symbol)
        
        # 3. Validate
        if signal.score >= 85:
            if execution_agent.approve(signal):
                # 4. Execute
                execute_trade(signal)
    
    # 5. Manage positions
    manage_open_positions()
    
    sleep(120)  # 2 minutes
```

## File Structure

```
titan_system/
├── titan_production.py       # Main bot
├── agents/
│   └── execution_decision_agent.py
├── core/
│   └── circuit_breaker.py
├── execution/
│   ├── mt5_executor.py
│   └── trade_manager.py
└── strategies/              # Legacy (not used)
```

## Database Schema

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    timestamp TEXT,
    symbol TEXT,
    direction TEXT,
    entry_price REAL,
    lot_size REAL,
    stop_loss REAL,
    take_profit REAL,
    score REAL,
    reason TEXT,
    ticket INTEGER
);
```

## Design Principles

1. **Simplicity Over Complexity**: No event buses, no orchestrators - just clean logic
2. **Proven Over Novel**: RSI/EMA strategies backtested for years
3. **Safety First**: Multiple layers of risk protection
4. **Transparency**: Every decision logged

## What We Removed

From the original complex architecture, we removed:
- ❌ Event Bus (too complex)
- ❌ Orchestrator (unnecessary)
- ❌ Memory System (use SQLite instead)
- ❌ SMC Engines (too selective, negative expectancy)

What we kept:
- ✅ Execution Decision Agent
- ✅ Circuit Breaker
- ✅ MT5 Executor
- ✅ Clean risk management

## Future Enhancements

Possible additions:
- Web dashboard (FastAPI)
- Performance analytics
- Advanced trailing stops
- Multi-account support
