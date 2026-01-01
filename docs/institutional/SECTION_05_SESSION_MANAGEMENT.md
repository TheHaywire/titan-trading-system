# Section 05: MT5 Session Management, Reconnection & Health

**Owner**: Reliability Engineer  
**Status**: 🚧 In Progress (45%)  
**Last Updated**: 2026-01-01  
**Priority**: HIGH

---

## 🎯 Objective

Build a robust session manager that ensures 24/7 MT5 connectivity, handles reconnections gracefully, monitors system health, and implements emergency kill switches to protect capital.

---

## 1. Session Manager Design

### Core Responsibilities
1. **Startup**: Launch MT5 terminal, verify login, check "Algo Trading" enabled
2. **Monitoring**: Continuous health checks (connection, ping, data feed)
3. **Reconnection**: Automatic reconnection with exponential backoff
4. **Kill Switches**: Emergency stops at account/symbol/global levels
5. **Logging**: All events timestamped and logged for audit

### Implementation

```python
import MetaTrader5 as mt5
import time
from datetime import datetime
from enum import Enum

class SessionStatus(Enum):
    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    ERROR = 3

class MT5SessionManager:
    """Manages MT5 terminal connection and health."""
    
    def __init__(self, account: int, password: str, server: str):
        self.account = account
        self.password = password
        self.server = server
        self.status = SessionStatus.DISCONNECTED
        self.last_ping_time = None
        self.reconnect_attempts = 0
        
    def start(self) -> bool:
        """Initialize MT5 connection."""
        self.status = SessionStatus.CONNECTING
        
        # Step 1: Initialize MT5
        if not mt5.initialize():
            error = mt5.last_error()
            print(f"MT5 initialize failed: {error}")
            self.status = SessionStatus.ERROR
            return False
        
        # Step 2: Login
        if not mt5.login(self.account, self.password, self.server):
            error = mt5.last_error()
            print(f"Login failed: {error}")
            self.status = SessionStatus.ERROR
            return False
        
        # Step 3: Verify algo trading enabled
        terminal_info = mt5.terminal_info()
        if not terminal_info.trade_allowed:
            raise RuntimeError("Algo trading disabled in terminal settings!")
        
        self.status = SessionStatus.CONNECTED
        self.reconnect_attempts = 0
        print(f"[{datetime.now()}] Connected to {self.server}, Account: {self.account}")
        return True
    
    def health_check(self) -> dict:
        """Comprehensive health check."""
        health = {
            "timestamp": datetime.now(),
            "status": "healthy",
            "issues": []
        }
        
        # Check 1: Terminal connection
        terminal_info = mt5.terminal_info()
        if terminal_info is None:
            health["status"] = "critical"
            health["issues"].append("Terminal not responding")
            return health
        
        # Check 2: Account info
        account_info = mt5.account_info()
        if account_info is None:
            health["status"] = "critical"
            health["issues"].append("Account info unavailable")
            return health
        
        # Check 3: Server ping
        start = time.time()
        tick = mt5.symbol_info_tick("EURUSD")
        ping_ms = (time.time() - start) * 1000
        
        if ping_ms > 1000:  # > 1 second = problem
            health["status"] = "degraded"
            health["issues"].append(f"High latency: {ping_ms:.0f}ms")
        
        health["ping_ms"] = ping_ms
        health["balance"] = account_info.balance
        health["equity"] = account_info.equity
        
        return health
    
    def reconnect(self, max_attempts: int = 5) -> bool:
        """Reconnect with exponential backoff."""
        for attempt in range(max_attempts):
            mt5.shutdown()
            wait_time = 2 ** attempt  # 1s, 2s, 4s, 8s, 16s
            
            print(f"Reconnect attempt {attempt + 1}/{max_attempts}, waiting {wait_time}s...")
            time.sleep(wait_time)
            
            if self.start():
                print(f"Reconnected successfully on attempt {attempt + 1}")
                return True
        
        print(f"Reconnection failed after {max_attempts} attempts")
        self.status = SessionStatus.ERROR
        return False
```

**Reference**: `titan_system/core/session_manager.py`

---

## 2. Health Metrics Dashboard

### Key Metrics

| Metric | Threshold | Action if Breached |
|--------|-----------|-------------------|
| **Ping Latency** | < 200ms normal, > 1s critical | Log warning, trigger reconnect if >5s |
| **Order Reject Rate** | < 5% | Pause trading if >10% |
| **Data Gaps** | 0 missing bars | Alert if any gaps detected |
| **CPU Usage** | < 50% | Alert if >80% (terminal may crash) |
| **Memory Usage** | < 2GB | Restart terminal if >4GB |

### Implementation

```python
def monitor_health_loop(session_manager, interval_seconds=60):
    """Continuous health monitoring."""
    while True:
        health = session_manager.health_check()
        
        if health["status"] == "critical":
            print(f"🚨 CRITICAL: {health['issues']}")
            session_manager.reconnect()
        
        elif health["status"] == "degraded":
            print(f"⚠️ WARNING: {health['issues']}")
        
        # Log to database
        log_health_metric(health)
        
        time.sleep(interval_seconds)
```

---

## 3. Kill Switch Mechanism

### Three-Tier Kill Switch

```python
class KillSwitch:
    """Emergency stop mechanism."""
    
    def __init__(self):
        self.global_enabled = True
        self.symbol_blacklist = set()
        self.account_active = True
    
    def trigger_global(self, reason: str):
        """Level 1: Stop ALL trading immediately."""
        print(f"🚨 GLOBAL KILL SWITCH ACTIVATED: {reason}")
        self.global_enabled = False
        
        # Close all open positions
        self._close_all_positions()
        
        # Cancel all pending orders
        self._cancel_all_orders()
        
        # Send email/SMS alert
        self._send_alert(f"Trading halted: {reason}")
    
    def trigger_symbol(self, symbol: str, reason: str):
        """Level 2: Stop trading specific symbol."""
        print(f"⚠️ SYMBOL KILL SWITCH: {symbol} - {reason}")
        self.symbol_blacklist.add(symbol)
        
        # Close positions for this symbol only
        positions = mt5.positions_get(symbol=symbol)
        for pos in positions:
            self._close_position(pos.ticket)
    
    def trigger_account(self, reason: str):
        """Level 3: Pause account, keep positions open."""
        print(f"⏸️ ACCOUNT PAUSED: {reason}")
        self.account_active = False
    
    def can_trade(self, symbol: str) -> bool:
        """Check if trading is allowed."""
        if not self.global_enabled:
            return False
        if not self.account_active:
            return False
        if symbol in self.symbol_blacklist:
            return False
        return True
```

### Trigger Conditions

```python
def check_kill_switch_triggers(kill_switch, account_info):
    """Check conditions that should trigger kill switches."""
    
    # Global triggers
    if account_info.equity < account_info.balance * 0.90:  # 10% drawdown
        kill_switch.trigger_global("Max account drawdown (10%) reached")
    
    # Connection loss for > 5 minutes
    if session_health["ping_ms"] > 5000:
        kill_switch.trigger_global("Connection lost >5 seconds")
    
    # Symbol-specific: excessive slippage
    if symbol_slippage["XAUUSD"] > 5.0:  # >5 pips average slippage
        kill_switch.trigger_symbol("XAUUSD", "Excessive slippage detected")
```

---

## 4. Reconnection Stress Testing

### Test Scenarios

1. **Terminal Crash**: Kill MT5 process, verify auto-restart
2. **Broker Disconnect**: Simulate network loss, verify reconnection
3. **Duplicate Orders**: Ensure no orders sent during reconnection window
4. **Position State**: Verify open positions persist after reconnection

### Test Script

```python
def stress_test_reconnection():
    """Test reconnection reliability."""
    session = MT5SessionManager(account, password, server)
    session.start()
    
    # Open a test position
    test_order = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": "EURUSD",
        "volume": 0.01,
        "type": mt5.ORDER_TYPE_BUY,
        "price": mt5.symbol_info_tick("EURUSD").ask,
    }
    result = mt5.order_send(test_order)
    original_ticket = result.order
    
    # Simulate disconnect
    mt5.shutdown()
    time.sleep(5)
    
    # Reconnect
    success = session.reconnect()
    assert success, "Reconnection failed"
    
    # Verify position still exists
    positions = mt5.positions_get(ticket=original_ticket)
    assert len(positions) == 1, "Position lost after reconnection"
    
    print("✅ Reconnection stress test passed")
```

---

## 📚 Cross-References

### MT5 Documentation
- **Terminal Info**: https://www.mql5.com/en/docs/constants/environment_state/terminalstatus
- **Error Codes**: https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes

### Titan System
- **Session Manager**: `titan_system/core/session_manager.py`
- **Kill Switch**: `titan_system/risk/kill_switch.py`

---

## ✅ Validation Checklist

- [x] Session manager basic implementation
- [ ] Health metrics dashboard (real-time)
- [ ] 3-tier kill switch coded
- [ ] Kill switch stress tested
- [ ] Reconnection tests passed (100% success rate)
- [ ] Duplicate order prevention verified

---

## 🚨 Critical Gaps

**High Risk**: Kill switches not yet stress-tested in live environment. This is a critical safety gap.

**Next Actions**: 
1. Build kill switch module
2. Run reconnection stress tests (50 iterations)
3. Add health dashboard to monitoring (Section 11)

---

**Status**: Basic session manager exists | Kill switches pending ⚠️
