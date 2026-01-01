# Section 10: Backtesting, Validation & Verification with MT5 Server

**Owner**: Model Validation Lead  
**Status**: 🚧 In Progress (45%)  
**Last Updated**: 2026-01-01  
**Priority**: 🚨 CRITICAL - Blocks capital scaling >$10K

---

## 🎯 Objective

Cross-validate all trading strategies using MT5 Strategy Tester and independent Python backtests. Ensure statistical significance, walk-forward optimization, and broker-realistic execution before deploying capital.

---

## 1. MT5 Strategy Tester Overview

### What It Does
- **Tick-by-tick simulation**: Most accurate backtesting (uses real tick data)
- **Multi-symbol support**: Test portfolios, not just single instruments
- **Genetic optimization**: Find optimal parameters across multiple dimensions
- **Visual backtesting**: See every trade on charts with entry/exit markers

### Execution Modes

| Mode | Description | Accuracy | Speed |
|------|-------------|----------|-------|
| **Every tick** | Most accurate, uses all available ticks | ⭐⭐⭐⭐⭐ | Slow |
| **1 minute OHLC** | Uses minute bars | ⭐⭐⭐ | Medium |
| **Open prices only** | Fastest, least accurate | ⭐ | Fast |
| **Real ticks** | Uses actual historical ticks from broker | ⭐⭐⭐⭐⭐ | Slowest |

**Titan System Standard**: Use **Real ticks** for final validation, **Every tick** for development.

---

## 2. Python Backtest Framework

### Current Implementation

**File**: `titan_system/backtest/engine.py` (to be created)

```python
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import List, Dict

class BacktestEngine:
    """Independent Python backtest framework."""
    
    def __init__(self, symbol: str, timeframe: int, start_date, end_date):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        
        # Load historical data
        self.data = self._load_data()
        
        # Results tracking
        self.trades = []
        self.equity_curve = []
        
    def _load_data(self) -> pd.DataFrame:
        """Load OHLCV data from MT5."""
        rates = mt5.copy_rates_range(
            self.symbol, 
            self.timeframe, 
            self.start_date, 
            self.end_date
        )
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def run_strategy(self, strategy_class):
        """Execute strategy on historical data."""
        strategy = strategy_class()
        
        for i in range(len(self.data)):
            # Get current bar
            current_bar = self.data.iloc[i]
            
            # Check for signals
            signal = strategy.generate_signal(self.data.iloc[:i+1])
            
            if signal == "BUY":
                self._open_trade("BUY", current_bar)
            elif signal == "SELL":
                self._open_trade("SELL", current_bar)
            
            # Update open trades
            self._update_trades(current_bar)
        
        return self._calculate_metrics()
    
    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        wins = [t for t in self.trades if t['profit'] > 0]
        losses = [t for t in self.trades if t['profit'] < 0]
        
        total_trades = len(self.trades)
        win_rate = len(wins) / total_trades if total_trades > 0 else 0
        
        avg_win = np.mean([t['profit'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['profit'] for t in losses]) if losses else 0
        
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        
        # Sharpe Ratio
        returns = pd.Series([t['profit'] for t in self.trades])
        sharpe = returns.mean() / returns.std() * np.sqrt(252) if returns.std() > 0 else 0
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "expectancy": expectancy,
            "sharpe_ratio": sharpe,
            "max_drawdown": self._calc_max_drawdown(),
            "profit_factor": abs(sum([t['profit'] for t in wins]) / sum([t['profit'] for t in losses])) if losses else 0
        }
```

---

## 3. Walk-Forward Optimization

### Methodology

**Definition**: Optimize parameters on one time period (in-sample), validate on the next period (out-of-sample), then roll forward.

### Process

```
┌─────────────────────────────────────────────────────┐
│          WALK-FORWARD ANALYSIS                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│  [In-Sample 1] → [Out-Sample 1]                    │
│  Jan-Mar 2024     Apr 2024                          │
│  Optimize         Validate                          │
│                                                      │
│       [In-Sample 2] → [Out-Sample 2]               │
│       Feb-Apr 2024     May 2024                     │
│       Optimize         Validate                     │
│                                                      │
│            [In-Sample 3] → [Out-Sample 3]          │
│            Mar-May 2024     Jun 2024                │
│            Optimize         Validate                │
└─────────────────────────────────────────────────────┘
```

### Implementation

```python
def walk_forward_analysis(
    symbol: str,
    strategy_class,
    in_sample_months: int = 3,
    out_sample_months: int = 1,
    total_periods: int = 12
):
    """
    Perform walk-forward optimization.
    
    Args:
        in_sample_months: Months to optimize on
        out_sample_months: Months to validate on
        total_periods: Number of walk-forward windows
    """
    results = []
    
    for i in range(total_periods):
        # Define windows
        in_start = start_date + pd.DateOffset(months=i)
        in_end = in_start + pd.DateOffset(months=in_sample_months)
        out_start = in_end
        out_end = out_start + pd.DateOffset(months=out_sample_months)
        
        # Optimize on in-sample
        best_params = optimize_parameters(
            symbol, strategy_class, in_start, in_end
        )
        
        # Validate on out-sample
        out_performance = backtest_with_params(
            symbol, strategy_class, best_params, out_start, out_end
        )
        
        results.append({
            "period": i,
            "in_sample_params": best_params,
            "out_sample_sharpe": out_performance['sharpe_ratio'],
            "out_sample_win_rate": out_performance['win_rate']
        })
    
    return pd.DataFrame(results)
```

**Acceptance Criteria**: Out-of-sample Sharpe > 1.0, Win Rate > 40%

---

## 4. Cross-Validation: MT5 vs Python

### Why Cross-Validate?

- **Python backtest** may have look-ahead bias, data snooping
- **MT5 Strategy Tester** uses broker's actual data feed
- **Discrepancy** indicates implementation bugs or unrealistic assumptions

### Validation Process

```python
def cross_validate_mt5_vs_python(
    symbol: str,
    strategy_mql5_path: str,
    strategy_python_class,
    start_date,
    end_date
):
    """Compare MT5 and Python backtest results."""
    
    # Run MT5 backtest (via API or manual)
    mt5_results = run_mt5_strategy_tester(
        symbol, strategy_mql5_path, start_date, end_date
    )
    
    # Run Python backtest
    engine = BacktestEngine(symbol, mt5.TIMEFRAME_H1, start_date, end_date)
    python_results = engine.run_strategy(strategy_python_class)
    
    # Compare
    comparison = {
        "metric": ["Total Trades", "Win Rate", "Sharpe", "Max DD"],
        "MT5": [
            mt5_results['total_trades'],
            mt5_results['win_rate'],
            mt5_results['sharpe'],
            mt5_results['max_drawdown']
        ],
        "Python": [
            python_results['total_trades'],
            python_results['win_rate'],
            python_results['sharpe_ratio'],
            python_results['max_drawdown']
        ]
    }
    
    df = pd.DataFrame(comparison)
    df['Discrepancy %'] = ((df['Python'] - df['MT5']) / df['MT5'] * 100).round(2)
    
    return df
```

**Acceptance Criteria**: Discrepancy < 5% for all key metrics

---

## 5. Performance Metrics (Institutional Standard)

### Core Metrics

| Metric | Formula | Institutional Target |
|--------|---------|---------------------|
| **Sharpe Ratio** | (Mean Return - Risk-Free Rate) / Std Dev of Returns | > 1.5 |
| **Sortino Ratio** | (Mean Return - Risk-Free Rate) / Downside Deviation | > 2.0 |
| **Max Drawdown** | Largest peak-to-trough decline | < 20% |
| **Profit Factor** | Gross Profit / Gross Loss | > 2.0 |
| **Expectancy** | (Win Rate × Avg Win) - (Loss Rate × Avg Loss) | > 0.5R |
| **Win Rate** | % of Winning Trades | > 40% |
| **Average R:R** | Avg Win / Avg Loss | > 2:1 |

### Monte Carlo Stress Testing

```python
import random

def monte_carlo_simulation(trades: List[float], num_simulations: int = 10000):
    """
    Simulate random trade sequences to estimate drawdown distribution.
    
    Args:
        trades: List of trade P&Ls (in R multiples)
        num_simulations: Number of random sequences to test
    """
    max_drawdowns = []
    
    for _ in range(num_simulations):
        # Shuffle trades randomly
        shuffled = random.sample(trades, len(trades))
        
        # Calculate equity curve
        equity = [1.0]  # Start with 1 (100%)
        for trade_pnl in shuffled:
            equity.append(equity[-1] * (1 + trade_pnl))
        
        # Find max drawdown
        peak = equity[0]
        max_dd = 0
        for e in equity:
            if e > peak:
                peak = e
            dd = (peak - e) / peak
            if dd > max_dd:
                max_dd = dd
        
        max_drawdowns.append(max_dd)
    
    return {
        "mean_dd": np.mean(max_drawdowns),
        "worst_case_dd": np.percentile(max_drawdowns, 95),  # 95th percentile
        "best_case_dd": np.percentile(max_drawdowns, 5)
    }
```

**Usage**: Estimate worst-case drawdown before going live

---

## 6. Live Replay Sanity Checks

### Process

1. **Record broker data**: Save tick data from live MT5 feed
2. **Replay in backtest**: Feed same ticks into Python backtest
3. **Compare results**: Ensure strategy produces identical signals

**Purpose**: Catch slippage, requote, or execution model differences

---

## 📚 Cross-References

### MT5 Documentation
- **Strategy Tester**: https://www.mql5.com/en/docs/runtime/testing
- **Optimization**: https://www.mql5.com/en/articles/1513
- **Custom Symbols**: https://www.mql5.com/en/docs/customsymbols

### Industry Standards
- **Walk-Forward Analysis**: Pardo, "Design, Testing, and Optimization of Trading Systems"
- **Monte Carlo**: Ralph Vince, "The Mathematics of Money Management"

### Titan System Files
- **Backtest Engine**: `titan_system/backtest/engine.py` (to be created)
- **Metrics**: `titan_system/analytics/metrics.py`
- **Walk-Forward**: `titan_system/backtest/walk_forward.py` (to be created)

---

## ✅ Validation Checklist

- [x] Python backtest framework exists
- [ ] MT5 Strategy Tester integrated
- [ ] Walk-forward optimization implemented
- [ ] Cross-validation (MT5 vs Python) < 5% discrepancy
- [ ] Monte Carlo simulations (10,000 runs)
- [ ] All metrics (Sharpe, Sortino, MDD) calculated
- [ ] Live replay sanity checks performed

---

## 🚨 Blockers

**Critical Path**: Cannot scale capital beyond $10K until:
1. Walk-forward optimization shows consistent out-of-sample performance
2. MT5 vs Python cross-validation passes (<5% discrepancy)
3. Monte Carlo shows <25% worst-case drawdown at 95th percentile

**Next Actions**: Build walk-forward module, integrate MT5 Strategy Tester API.

---

**Status**: Framework exists | Validation pipeline incomplete ⚠️
