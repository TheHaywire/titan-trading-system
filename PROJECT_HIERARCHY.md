# Institutional Trading System - Project Hierarchy

## 🏛️ CATEGORY 1: INFRASTRUCTURE CORE
**"The Foundation"**

### ✅ [PHASE 0] System Reconnaissance
- **Subtask**: Deep Broker Scan (Spreads, Leverage, Contract Sizes)
  - *Output*: `docs/recon/BROKER_MASTER_UNIVERSE.csv`
- **Subtask**: Architecture Blueprinting
  - *Output*: `docs/inst_level/INSTITUTIONAL_BLUEPRINT.md`

### ✅ [PHASE 3] Engine Architecture
- **Subtask**: Single Source of Truth Engine
  - *Output*: `titan_system/core/production_engine.py`
- **Subtask**: Configuration Management
  - *Output*: `titan_system/titan_futures_config.py`
- **Subtask**: Database Schema (Strategy Routing)
  - *Output*: `titan_system/data/models.py` (StrategyAssignment Table)

---

## 🧠 CATEGORY 2: STRATEGY LAB
**"The Alpha Generators"**

### ✅ [PHASE 1] Base Strategy Development
- **Subtask**: BookTechnicalStrategy Implementation
  - *Output*: `titan_system/strategies/book_strategies.py`
- **Subtask**: Technical Indicator Library (MA, RSI, Bollinger)
  - *Output*: `titan_system/strategies/book_strategies.py`

### ✅ [PHASE 2] Edge Optimization
- **Subtask**: "Fat Tail" Discovery (1500+ Symbol Scan)
  - *Output*: `docs/FAT_TAIL_OPPORTUNITIES.md`
- **Subtask**: Trend Filter Verification (SMA 200)
  - *Output*: `docs/OPTIMIZATION_REPORT.md`
- **Subtask**: "Home Run" Exit Logic (SMA 50 Trailing)
  - *Output*: `titan_system/core/trade_manager.py`

### 🚧 [PHASE 6] Strategy Validation (Active)
- **Subtask**: Formal Backtest Suite
- **Subtask**: Monte Carlo Stress Test
- **Subtask**: Institutional Gold Strategy Implementation

---

## 🛡️ CATEGORY 3: RISK CONSTITUTION
**"The Safeguards"**

### ✅ [PHASE 5] Risk Core Implementation
- **Subtask**: Institutional Position Sizer (Risk % Model)
  - *Output*: `titan_system/risk/position_sizer.py`
- **Subtask**: Leverage Normalization (1:1000 Protection)
  - *Output*: `titan_system/titan_futures_config.py`

### 📋 [PHASE 8] Advanced Risk (Pending)
- **Subtask**: Portfolio Correlation Matrix
- **Subtask**: Volatility-Adjusted Sizing
- **Subtask**: Black Swan Circuit Breaker

---

## 🖥️ CATEGORY 4: OPERATIONS COMMAND
**"The Cockpit"**

### 📋 [PHASE 7] Real-Time Monitoring (Pending)
- **Subtask**: Terminal Dashboard (Rich UI)
  - *Output*: `titan_system/dashboard/terminal_ui.py`
- **Subtask**: Deployment Launcher
  - *Output*: `start_production.py`
- **Subtask**: Telegram Command Center

---

## 🔬 CATEGORY 5: QUALITY ASSURANCE
**"The Audit"**

### 📋 [PHASE 10] Testing Suite
- **Subtask**: Unit Tests (PyTest)
- **Subtask**: Integration Tests (MT5 Bridge)
- **Subtask**: Paper Trading Logs

