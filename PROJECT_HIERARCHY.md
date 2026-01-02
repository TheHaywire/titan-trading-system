# Institutional Trading System - Project Hierarchy (v2.0)

## 📂 ROOT DIRECTORY
| File/Folder | Description |
|---|---|
| `titan_system/` | **The Core Package**. All production code lives here. |
| `scripts/` | Utilities for Backtesting, Optimization, and Launching. |
| `docs/` | Institutional Documentation ("The Bible"). |
| `data/` | SQLite Databases (`titan.db`, `backtest.db`) and Logs. |
| `tests/` | Unit and Integration Tests. |
| `README.md` | The Project Homepage. |
| `PROJECT_BOARD.md` | Active Sprint & Kanban Board. |

---

## 🏛️ PACKAGE: `titan_system/`

### `core/` (The Engine Room)
- `engine.py`: **Main Event Loop**. Handles Tick stream and orchestration.
- `data_pipeline.py`: **Data Integrity**. Gap checks and bar alignment.
- `execution.py`: **MT5 Bridge**. Order placement and management.

### `strategies/` (The Alpha Units)
- `base.py`: Abstract Base Class for all strategies.
- `live_crypto_trend.py`: **ETH/BTC Trend** (Regime-Aware).
- `live_gold_breakout.py`: **Gold Breakout** (Coming soon).
- `book_strategies.py`: *Legacy/Backtest implementations*.

### `risk/` (The Shield)
- `kill_switch.py`: **Circuit Breaker**. Stops trading on Drawdown.
- `allocation.py`: **Allocation Agent**. Dynamic Sizing & Regime Scaling.
- `position_sizer.py`: ATR-based risk calculation.

### `analytics/` (The Scoreboard)
- `backtest_logger.py`: Writes results to `backtest_history.db`.
- `metrics.py`: Sharpe/Sortino calculators.

### `ui/` (The Cockpit)
- `dashboard.py`: **Rich Terminal UI**. Real-time monitoring.

---

## 🛠️ UTILITIES: `scripts/`

- `walk_forward_validation.py`: **WFA Engine**. Stress tests strategies.
- `deep_optimization.py`: **Grid Search**. Finds optimal parameters.
- `comprehensive_matrix_backtest.py`: **The Matrix**. 1,000+ simulation runner.
- `launch.py`: Production entry point.

---

## 📚 DOCUMENTATION: `docs/`

- `INSTITUTIONAL_MASTER_PLAN.md`: The 12-Section Architecture.
- `PROJECT_RETROSPECTIVE.md`: Lessons Learned & "Why we don't scalp".
- `research/`: Strategy Database.
- `institutional/`: Detailed specs for each module.


