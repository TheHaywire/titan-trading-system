# Titan System - Quantitative Engine (v2.0)

This directory contains the new modular architecture for the Titan Trading System, designed to separate Data, Research, and Portfolio management into robust, testable components.

## 📂 Architecture Overview

### 1. Data Layer (`titan_system/data`)
**"The Source of Truth"**
*   **Purpose**: Manages historical data storage to ensure no lookahead bias.
*   **Tech**: SQLite (`titan.db`), SQLAlchemy, MetaTrader5.
*   **Key Files**:
    *   `ingest_mt5.py`: Fetches data from MT5. Auto-resolves symbols (e.g., "GOLD" -> "XAUUSD").
    *   `models.py`: Defines the database schema (Tickers, OHLCV, Trades).
*   **Usage**:
    ```bash
    python -m titan_system.data.ingest_mt5 GOLD H1 30  # Ingest 30 days of H1 data
    ```

### 2. Research Layer (`titan_system/research`)
**"The Laboratory"**
*   **Purpose**: Develop and backtest strategies on stored data.
*   **Tech**: VectorBT (Pro-style backtesting), Pandas, Plotly.
*   **Key Files**:
    *   `data_loader.py`: Loads data from SQLite into VectorBT-ready DataFrames.
    *   `backtester.py`: Runs fast vectorised simulations.
*   **Usage**:
    ```python
    from titan_system.research.backtester import Backtester
    bt = Backtester("GOLD", "H1")
    bt.run_sma_crossover(10, 20)
    ```

### 3. Portfolio Layer (`titan_system/portfolio`)
**"The Brain"**
*   **Purpose**: Determines position sizing and validates trading risk.
*   **Tech**: PyPortfolioOpt (Mean-Variance Optimization).
*   **Key Files**:
    *   `optimizer.py`: Calculates efficient frontier weights.
    *   `risk_engine.py`: Acts as a circuit breaker (Max Drawdown, Max Pos Size).

## 🚀 Getting Started
1.  **Ingest Data**: Ensure MT5 is running. Run the ingestion script to populate your DB.
2.  **Run Research**: Use `scripts/test_backtest.py` to test a strategy.
3.  **Check Health**: Run `scripts/test_full_system.py` to verify all components are talking to each other.

