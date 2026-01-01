# Section 02: MT5 Python Connectivity & Tech Stack

**Owner**: Python–MT5 Integration Lead  
**Status**: 🚧 In Progress (60%)  
**Last Updated**: 2026-01-01

---

## 🎯 Objective

Specify the complete Python–MT5 tech stack, connection architecture, and function wrappers. Ensure reliable, low-latency communication between Python trading logic and MT5 terminal via the official MetaTrader5 package.

---

## 1. Tech Stack Specification

### Operating System
**Institutional Standard**: Windows Server (2019/2022)

- **Why Windows**: MT5 terminal requires Windows; MetaTrader5 Python package uses Windows-specific IPC
- **Alternative**: Can run on Linux via Wine, but not recommended for production
- **Current Titan System**: Windows 10/11 Pro (development), Windows Server (production target)

### MT5 Terminal
- **Version**: Latest build from MetaQuotes or broker-provided installer
- **Account Type**: Live (production) or Demo (testing)
- **Configuration**: 
  - ✅ "Algo Trading" enabled in Tools → Options → Expert Advisors
  - ✅ "Allow DLL imports" enabled (for Python bridge)
  - ✅ Terminal must be running 24/7 with active login

### Python Environment

```
Python 3.10+ (64-bit)
├── MetaTrader5==5.0.45          # Official MT5 Python API
├── pandas==2.1.0                # Data manipulation
├── numpy==1.24.0                # Numerical operations
├── pytz==2023.3                 # Timezone handling
├── python-dotenv==1.0.0         # Environment variables
└── schedule==1.2.0              # Job scheduling
```

**Installation**:
```bash
pip install MetaTrader5 pandas numpy pytz python-dotenv schedule
```

**Reference**: `requirements.txt`

---

## 2. Python–MT5 IPC Bridge Architecture

### How the Connection Works

```
┌─────────────────────────────────────────────────────────────┐
│                  PYTHON–MT5 IPC BRIDGE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │ Python       │         │ MT5          │                 │
│  │ Trading Bot  │         │ Terminal     │                 │
│  │              │         │ (Running)    │                 │
│  └──────────────┘         └──────────────┘                 │
│         │                         ▲                         │
│         │    mt5.initialize()     │                         │
│         ├────────────────────────►│                         │
│         │                         │                         │
│         │    mt5.login()          │                         │
│         ├────────────────────────►│                         │
│         │                         │                         │
│         │    mt5.order_send()     │                         │
│         ├────────────────────────►│                         │
│         │                         │                         │
│         │◄───── Trade Result ─────┤                         │
│         │                         │                         │
│         │    mt5.copy_rates_*()   │                         │
│         ├────────────────────────►│                         │
│         │                         │                         │
│         │◄───── Price Bars ───────┤                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Constraints

1. **Local Only**: Python must be running on the same machine as MT5 terminal
2. **Terminal Must Be Running**: MT5 terminal must be open and logged into an account
3. **IPC Mechanism**: Uses Windows named pipes and shared memory (internal to MetaTrader5 package)
4. **Single Session**: Only one Python process can connect to MT5 terminal at a time

---

## 3. Connection Lifecycle

### Startup Sequence

```python
import MetaTrader5 as mt5

# Step 1: Initialize connection
if not mt5.initialize():
    print(f"Initialize failed: {mt5.last_error()}")
    quit()

# Step 2: Optional login (if terminal not already logged in)
account = 12345678
password = "YourPassword"
server = "BrokerServer-Live"

if not mt5.login(account, password, server):
    print(f"Login failed: {mt5.last_error()}")
    mt5.shutdown()
    quit()

# Step 3: Verify connection
account_info = mt5.account_info()
if account_info is None:
    print("Failed to get account info")
    mt5.shutdown()
    quit()

print(f"Connected to account {account_info.login}")
```

### Health Checks

```python
def check_mt5_health() -> dict:
    """Perform comprehensive MT5 connection health check."""
    status = {
        "connected": False,
        "terminal_running": False,
        "account_valid": False,
        "algo_trading_enabled": False,
        "ping_ms": None,
        "last_error": None
    }
    
    # Check 1: Terminal connection
    terminal_info = mt5.terminal_info()
    if terminal_info is None:
        status["last_error"] = "Terminal not connected"
        return status
    status["terminal_running"] = True
    
    # Check 2: Account info
    account_info = mt5.account_info()
    if account_info is None:
        status["last_error"] = "Account info unavailable"
        return status
    status["account_valid"] = True
    
    # Check 3: Algo trading status
    if not terminal_info.trade_allowed:
        status["last_error"] = "Algo trading disabled in terminal"
        return status
    status["algo_trading_enabled"] = True
    
    # Check 4: Server ping
    import time
    start = time.time()
    mt5.symbol_info_tick("EURUSD")  # Quick ping
    status["ping_ms"] = (time.time() - start) * 1000
    
    status["connected"] = True
    return status
```

**Reference**: `titan_system/core/session_manager.py`

### Reconnection Strategy

```python
def reconnect_with_backoff(max_attempts=5):
    """Exponential backoff reconnection."""
    import time
    
    for attempt in range(max_attempts):
        mt5.shutdown()
        time.sleep(2 ** attempt)  # 1s, 2s, 4s, 8s, 16s
        
        if mt5.initialize():
            health = check_mt5_health()
            if health["connected"]:
                print(f"Reconnected on attempt {attempt + 1}")
                return True
        
    print("Reconnection failed after max attempts")
    return False
```

---

## 4. Critical Error: "Algo Trading Disabled" (Error 10027)

### Problem
**Error Code**: `TRADE_RETCODE_CLIENT_DISABLES_AT` (10027)  
**Message**: "Autotrading disabled by client terminal"

### Root Cause
The MT5 terminal has "Algo Trading" disabled in Expert Advisors settings.

### Solution

**Manual Fix**:
1. Open MT5 terminal
2. Go to **Tools → Options → Expert Advisors**
3. Enable **"Allow algorithmic trading"**
4. Click **OK**
5. Restart Python script

**Python Detection**:
```python
terminal_info = mt5.terminal_info()
if not terminal_info.trade_allowed:
    raise RuntimeError(
        "Algo trading disabled! Enable in MT5: "
        "Tools → Options → Expert Advisors → Allow algorithmic trading"
    )
```

---

## 5. Critical Python Functions (Wrapped)

### Symbol Discovery & Properties

```python
# Get all symbols
symbols = mt5.symbols_get()

# Get symbol info
info = mt5.symbol_info("EURUSD")

# Get current tick
tick = mt5.symbol_info_tick("XAUUSD")
```

### Historical Data

```python
# Get OHLCV bars (from/to datetime)
import datetime
import pytz

utc_from = datetime.datetime(2024, 1, 1, tzinfo=pytz.UTC)
utc_to = datetime.datetime.now(pytz.UTC)

rates = mt5.copy_rates_range("EURUSD", mt5.TIMEFRAME_H1, utc_from, utc_to)

# Get last N bars
rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 100)

# Convert to DataFrame
import pandas as pd
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
```

### Tick Data

```python
# Get ticks from timestamp
ticks = mt5.copy_ticks_from("XAUUSD", utc_from, 1000, mt5.COPY_TICKS_ALL)

# Get tick range
ticks = mt5.copy_ticks_range("BTCUSD", utc_from, utc_to, mt5.COPY_TICKS_TRADE)
```

### Account Information

```python
# Account details
account = mt5.account_info()
print(f"Balance: {account.balance}, Equity: {account.equity}")
print(f"Margin Free: {account.margin_free}, Leverage: {account.leverage}")
```

### Order Sending

```python
# Market buy order
request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "EURUSD",
    "volume": 0.1,
    "type": mt5.ORDER_TYPE_BUY,
    "price": mt5.symbol_info_tick("EURUSD").ask,
    "sl": 1.0800,  # Stop loss
    "tp": 1.1000,  # Take profit
    "deviation": 20,  # Slippage tolerance in points
    "magic": 234000,  # EA ID
    "comment": "Titan Bot Buy",
    "type_time": mt5.ORDER_TIME_GTC,
    "type_filling": mt5.ORDER_FILLING_IOC,
}

result = mt5.order_send(request)
if result.retcode != mt5.TRADE_RETCODE_DONE:
    print(f"Order failed: {result.retcode} - {result.comment}")
else:
    print(f"Order placed: ticket={result.order}")
```

### Position & Order Management

```python
# Get open positions
positions = mt5.positions_get(symbol="EURUSD")

# Get pending orders
orders = mt5.orders_get()

# Close position
close_request = {
    "action": mt5.TRADE_ACTION_DEAL,
    "symbol": "EURUSD",
    "volume": 0.1,
    "type": mt5.ORDER_TYPE_SELL,  # Opposite of position
    "position": 123456,  # Position ticket
    "price": mt5.symbol_info_tick("EURUSD").bid,
    "deviation": 20,
    "magic": 234000,
    "comment": "Close position",
}
result = mt5.order_send(close_request)
```

**Reference**: `titan_system/core/mt5_bridge.py`

---

## 📚 Cross-References

### MetaQuotes Documentation
- **Python Package**: [MetaTrader5 on PyPI](https://pypi.org/project/MetaTrader5/)
- **Function Reference**: [MT5 Python API Docs](https://www.mql5.com/en/docs/integration/python_metatrader5)
- **Error Codes**: [Trade Return Codes](https://www.mql5.com/en/docs/constants/errorswarnings/enum_trade_return_codes)

### Broker Validation
- **Demo Server**: Test all functions on broker demo account
- **Live Server**: Validate order execution, margin calculations, swap rates
- **Symbol Universe**: Confirm tradeable symbols match broker offering

### Titan System Implementation
- **Bridge**: `titan_system/core/mt5_bridge.py`
- **Session Manager**: `titan_system/core/session_manager.py`
- **Example Usage**: `main.py`

---

## ✅ Validation Checklist

- [x] MetaTrader5 package installed and functional
- [x] MT5 terminal running with account logged in
- [x] Algo trading enabled in terminal settings
- [ ] All critical functions tested on demo account
- [ ] Health check and reconnection logic implemented
- [ ] Error 10027 detection and user notification added
- [ ] Latency measured (Python → MT5 → Broker)
- [ ] Cross-referenced with broker's live MT5 server

---

## 🚨 Known Issues

1. **Single Connection**: Only one Python process can connect; need mutex for multi-bot setups
2. **Terminal Restart**: If MT5 crashes, Python script must reinitialize connection
3. **Timezone Handling**: MT5 uses broker timezone; Python must convert to UTC
4. **Windows Only**: No native Linux support (Wine is unstable for production)

**Next Actions**: Complete latency measurement, add mutex for multi-process safety.
