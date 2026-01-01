# Section 11: Monitoring, Logging & Audit Trail

**Owner**: Operations Lead  
**Status**: 📋 Pending (25%)  
**Last Updated**: 2026-01-01  
**Priority**: 🚨 CRITICAL - Required for prop firm compliance

---

## 🎯 Objective

Build a comprehensive monitoring, logging, and audit trail system that provides real-time visibility into system health, trade execution, and P&L while maintaining compliance-ready records for prop firms and regulators.

---

## 1. System Log Architecture

### Log Hierarchy

```
┌─────────────────────────────────────────────────────────┐
│                  LOG ARCHITECTURE                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  MT5 Terminal Logs                                      │
│  ├── Trades                                             │
│  ├── Expert Advisors                                    │
│  └── Terminal events                                    │
│                                                          │
│  Python Application Logs                                │
│  ├── Strategy signals                                   │
│  ├── Risk decisions                                     │
│  ├── Order submissions                                  │
│  └── Errors/warnings                                    │
│                                                          │
│  Infrastructure Logs                                    │
│  ├── System resources (CPU, memory)                     │
│  ├── Network connectivity                               │
│  └── Session health                                     │
│                                                          │
│  Audit Trail (Compliance)                               │
│  └── Trade → Strategy → Features → Rationale           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Implementation

```python
import logging
from datetime import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(f'logs/titan_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("TitanSystem")

# Structured logging
def log_trade_decision(symbol, signal, rationale, risk_approved):
    """Log trade decision with full audit trail."""
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event": "TRADE_DECISION",
        "symbol": symbol,
        "signal": signal,
        "rationale": rationale,
        "risk_approved": risk_approved
    }
    logger.info(json.dumps(log_entry))
    
    # Also save to database for querying
    save_to_audit_db(log_entry)
```

**Reference**: `titan_system/logging/audit_logger.py`

---

## 2. Time Synchronization (NTP)

### Why Critical
- **Audit compliance**: All events must have accurate timestamps
- **Trade reconciliation**: Match broker fills to strategy signals
- **Debugging**: Correlate events across systems

### Implementation

```python
import ntplib
from time import ctime

def sync_time_with_ntp(server='pool.ntp.org'):
    """Verify system time is accurate."""
    try:
        client = ntplib.NTPClient()
        response = client.request(server, version=3)
        
        offset_ms = response.offset * 1000
        
        if abs(offset_ms) > 1000:  # > 1 second drift
            logger.warning(f"System clock drift: {offset_ms:.0f}ms. Sync required!")
        else:
            logger.info(f"Time sync OK, offset: {offset_ms:.0f}ms")
        
        return offset_ms
    except Exception as e:
        logger.error(f"NTP sync failed: {e}")
        return None

# Run on startup
time_offset = sync_time_with_ntp()
```

---

## 3. Real-Time Dashboard Design

### Dashboard Components

#### 1. P&L Panel
- **Today's P&L**: Net profit/loss in currency and %
- **MTD P&L**: Month-to-date performance
- **Running Sharpe**: Real-time Sharpe ratio
- **Drawdown**: Current vs max drawdown

#### 2. Positions Panel
- **Open Positions**: Symbol, entry, current P&L, risk
- **Exposure**: Total capital at risk
- **Correlation**: Portfolio correlation matrix

#### 3. System Health Panel
- **Connection**: MT5 ping, broker status
- **CPU/Memory**: Resource usage
- **Last Trade**: Time since last execution
- **Errors**: Recent error count

#### 4. Risk Panel
- **Risk Used**: % of capital at risk (should be <10%)
- **Daily Loss**: % loss today vs limit
- **Kill Switches**: Status of all kill switches

### Implementation (Rich Terminal UI)

```python
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
import time

console = Console()

def build_dashboard_layout():
    """Create rich dashboard layout."""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3)
    )
    
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    layout["left"].split_column(
        Layout(name="pnl"),
        Layout(name="positions")
    )
    
    layout["right"].split_column(
        Layout(name="health"),
        Layout(name="risk")
    )
    
    return layout

def create_pnl_panel(account_info, trades_today):
    """Build P&L panel."""
    table = Table(title="📊 P&L Summary", show_header=False)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    daily_pnl = sum([t['profit'] for t in trades_today])
    daily_pnl_pct = (daily_pnl / account_info.balance) * 100
    
    table.add_row("Balance", f"${account_info.balance:,.2f}")
    table.add_row("Equity", f"${account_info.equity:,.2f}")
    table.add_row("Today P&L", f"${daily_pnl:,.2f} ({daily_pnl_pct:+.2f}%)")
    
    return Panel(table, border_style="green")

def run_dashboard():
    """Run live dashboard."""
    layout = build_dashboard_layout()
    
    with Live(layout, refresh_per_second=1, screen=True):
        while True:
            # Update panels
            account_info = mt5.account_info()
            positions = mt5.positions_get()
            health = check_system_health()
            
            layout["header"].update(Panel("[bold cyan]Titan Trading System - Live Dashboard[/]"))
            layout["pnl"].update(create_pnl_panel(account_info, trades_today))
            layout["positions"].update(create_positions_panel(positions))
            layout["health"].update(create_health_panel(health))
            layout["risk"].update(create_risk_panel(account_info))
            layout["footer"].update(Panel(f"[dim]Last Update: {datetime.now()}[/]"))
            
            time.sleep(1)
```

**Reference**: `titan_system/dashboard/terminal_ui.py`

---

## 4. Audit Trail: Trade → Strategy → Rationale

### Complete Audit Chain

Every trade must link to:
1. **Strategy**: Which strategy generated the signal
2. **Features**: Market conditions at signal time
3. **Risk Assessment**: Why trade was approved/rejected
4. **Execution**: Order details, slippage, fills

### Database Schema

```sql
CREATE TABLE audit_trail (
    id INTEGER PRIMARY KEY,
    timestamp DATETIME NOT NULL,
    symbol TEXT NOT NULL,
    strategy_name TEXT NOT NULL,
    signal_type TEXT,  -- 'BUY', 'SELL', 'CLOSE'
    entry_price REAL,
    stop_loss REAL,
    take_profit REAL,
    risk_amount REAL,
    risk_approved BOOLEAN,
    rejection_reason TEXT,
    order_ticket INTEGER,
    features JSON,  -- Market features at signal time
    rationale TEXT
);
```

### Usage

```python
def log_trade_to_audit_trail(trade_data):
    """Save complete trade audit trail."""
    db.execute("""
        INSERT INTO audit_trail (
            timestamp, symbol, strategy_name, signal_type,
            entry_price, stop_loss, take_profit,
            risk_amount, risk_approved, features, rationale
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now(),
        trade_data['symbol'],
        trade_data['strategy'],
        trade_data['signal'],
        trade_data['entry'],
        trade_data['sl'],
        trade_data['tp'],
        trade_data['risk_usd'],
        trade_data['approved'],
        json.dumps(trade_data['features']),
        trade_data['rationale']
    ))
```

**Query Example**: "Show me all trades where risk was rejected"
```python
rejected_trades = db.execute("""
    SELECT * FROM audit_trail 
    WHERE risk_approved = 0 
    ORDER BY timestamp DESC
""").fetchall()
```

---

## 5. Compliance Requirements

### Prop Firm Standards

| Requirement | Implementation |
|-------------|----------------|
| **Trade Timestamps** | NTP-synced, logged to millisecond precision |
| **P&L Tracking** | Real-time, per-trade and daily aggregates |
| **Risk Documentation** | Every trade links to risk approval decision |
| **Drawdown Monitoring** | Continuous tracking, alert if approaching limits |
| **Activity Logs** | All system events logged (logins, errors, kills switches) |

### Tamper-Evidence

```python
import hashlib

def create_tamper_proof_log(log_entry):
    """Hash chaining for tamper-evident logs."""
    previous_hash = get_last_log_hash()
    
    log_entry['previous_hash'] = previous_hash
    entry_str = json.dumps(log_entry, sort_keys=True)
    current_hash = hashlib.sha256(entry_str.encode()).hexdigest()
    log_entry['hash'] = current_hash
    
    save_log(log_entry)
    return current_hash
```

---

## 📚 Cross-References

### Industry Standards
- **NTP**: https://www.ntp.org/
- **Structured Logging**: https://www.structlog.org/

### Prop Firm Compliance
- FTMO Audit Requirements
- TopStepTrader Logging Standards

### Titan System
- **Audit Logger**: `titan_system/logging/audit_logger.py`
- **Dashboard**: `titan_system/dashboard/terminal_ui.py`
- **Database**: `titan_system/data/audit.db`

---

## ✅ Validation Checklist

- [ ] System logs structured (JSON format)
- [ ] NTP time sync implemented
- [ ] Real-time dashboard (Rich UI) built
- [ ] Audit trail database created
- [ ] Tamper-evident logging enabled
- [ ] Compliance requirements mapped

---

## 🚨 Blockers

**Critical**: Cannot submit to prop firm without complete audit trail showing:
1. Every trade decision and rationale
2. Risk approval/rejection logic
3. Real-time P&L tracking
4. Tamper-evident logs

**Next Actions**: Build dashboard prototype, implement audit trail database.

---

**Status**: Architecture defined | Implementation 25% complete ⚠️
