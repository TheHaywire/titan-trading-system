# 🏦 Titan Institutional Trading System (v2.0)
**Regime-Aware Quantitative Trading Engine for MetaTrader 5**

![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)
![Live Phase](https://img.shields.io/badge/Phase-4_Deployment-green.svg)
![Validation](https://img.shields.io/badge/Strategy-WFA_Validated-purple.svg)

Titan is an institutional-grade algorithmic trading system designed to trade **Regime-Dependent Strategies** on Daily (D1) timeframes. Unlike retail bots that attempt to scalp noise (M5/M15), Titan uses rigorous Walk-Forward Analysis (WFA) to deploy strategies only when market conditions match their statistical edge.

---

## 🚀 Key Features

### 🧠 AlphaOptimizer (The Brain)
Strategies are not always "On". The **AlphaOptimizer** analyzes the market regime (Trend vs. Chop) using ADX and Volatility metrics to enable/disable specific strategies dynamically.

### 🛡️ Institutional Risk Management
- **Audit Trail**: Every decision is logged to SQLite `data/titan.db`.
- **Kill Switch**: Hard circuit breaker for Drawdowns > 10% or Connection Loss.
- **Volatility Sizing**: Position size = `(Equity * Risk%) / (ATR * TickValue)`.
- **Data Integrity**: Bars are scanned for gaps before any calculation.

### 🧪 Validated "Golden Basket" Strategies
We filtered 1,000+ combinations to find the only 3 that survive transaction costs and Walk-Forward Analysis:
1.  **ETH/BTC Trend** (D1) - *Regime: Trending (ADX > 20)*
2.  **Gold Breakout** (D1) - *Regime: Expanding Volatility*
3.  **Forex Mean Reversion** - *REJECTED* (Markets too efficient)

---

## 📂 Architecture

The system is organized as a modular Python package `titan_system`:

```
titan-trading-system/
├── titan_system/
│   ├── core/               # Engine, Event Loop, Data Pipeline
│   ├── strategies/         # Live Strategies (LiveCryptoTrend, etc.)
│   ├── risk/               # AllocationAgent, KillSwitch
│   ├── analytics/          # BacktestLogger, Performance Metrics
│   └── ui/                 # Rich Terminal Dashboard
├── scripts/
│   ├── optimize/           # Deep Optimization & WFA Scripts
│   ├── launch.py           # Main Entry Point
│   └── tools/              # Database maintenance
├── docs/
│   ├── institutional/      # The 12-Section Master Plan
│   └── research/           # Strategy Research Database
└── data/                   # SQLite DBs and Logs
```

---

## 📦 Installation

1.  **Clone & Venv**:
    ```bash
    git clone https://github.com/TheHaywire/titan-trading-system.git
    cd titan-trading-system
    python -m venv .venv
    .venv\Scripts\activate
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure MT5**:
    - Open MetaTrader 5
    - Tools > Options > Expert Advisors: Enable "Allow WebRequest"
    - Copy `.env.example` to `.env` and set your credentials (optional, system auto-detects active terminal).

---

## 🎮 Usage

### 1. Run the Engine (Live/Paper)
New simplified entry point (Coming in Phase 4):
```bash
python scripts/launch.py --mode=paper
```

### 2. View the Dashboard
The system runs a **Rich Terminal UI** showing real-time PnL, Regime, and Active Positions.
![Dashboard](docs/assets/dashboard_preview.png)

### 3. Run Strategy Validation (Backtesting)
To re-validate the models:
```bash
# Run 1,000+ Matrix Backtest
python scripts/comprehensive_matrix_backtest.py

# Run Walk-Forward Analysis
python scripts/walk_forward_validation.py
```

---

## 📚 Documentation "The Bible"

- **[Master Plan](docs/INSTITUTIONAL_MASTER_PLAN.md)**: The 12-Section Architecture.
- **[Retrospective & Learnings](docs/PROJECT_RETROSPECTIVE_AND_LEARNINGS.md)**: Why we stopped scalping (Read this first!).
- **[Backtest Reports](docs/COMPREHENSIVE_BACKTEST_REPORT.md)**: Statistical proof of edge.
- **[Research Database](docs/research/STRATEGY_RESEARCH_DATABASE.md)**: Catalog of 50+ strategies.

---

## ⚠️ Disclaimer
**This is not financial advice.** Algorithmic trading involves substantial risk. The "Golden Basket" strategies performed well in backtests (2018-2025) but past performance is no guarantee of future results. **Use the Kill Switch.**

---
**Maintained by:** Manan Kharbanda (@TheHaywire)
**License:** MIT
