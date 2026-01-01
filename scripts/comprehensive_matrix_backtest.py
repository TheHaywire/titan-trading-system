"""
COMPREHENSIVE STRATEGY MATRIX BACKTEST
Systematic testing of ALL strategy × symbol × timeframe combinations
With proper naming, charting, and documentation
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import vectorbt as vbt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box
import json

# Import our logger
from titan_system.analytics.backtest_logger import BacktestLogger

console = Console()
logger = BacktestLogger()

# ============================================
# CONFIGURATION - ALL COMBINATIONS TO TEST
# ============================================

SYMBOLS = {
    # Crypto
    'BTCUSD': {'category': 'Crypto', 'spread': 0.0005},
    'ETHUSD': {'category': 'Crypto', 'spread': 0.0005},
    # Commodities
    'GOLD': {'category': 'Commodity', 'spread': 0.0003},
    'SILVER': {'category': 'Commodity', 'spread': 0.0004},
    # Forex Majors
    'EURUSD': {'category': 'Forex', 'spread': 0.0001},
    'GBPUSD': {'category': 'Forex', 'spread': 0.0002},
    'USDJPY': {'category': 'Forex', 'spread': 0.0001},
    'AUDUSD': {'category': 'Forex', 'spread': 0.0002},
    # Indices
    'US500Cash': {'category': 'Index', 'spread': 0.0003},
    'NAS100': {'category': 'Index', 'spread': 0.0003},
    'GER40': {'category': 'Index', 'spread': 0.0003},
}

TIMEFRAMES = {
    'M5': {'mt5': mt5.TIMEFRAME_M5, 'bars': 20000, 'style': 'Scalping', 'cost_mult': 3.0},
    'M15': {'mt5': mt5.TIMEFRAME_M15, 'bars': 15000, 'style': 'Scalping', 'cost_mult': 2.0},
    'M30': {'mt5': mt5.TIMEFRAME_M30, 'bars': 10000, 'style': 'Intraday', 'cost_mult': 1.5},
    'H1': {'mt5': mt5.TIMEFRAME_H1, 'bars': 8000, 'style': 'Intraday', 'cost_mult': 1.2},
    'H4': {'mt5': mt5.TIMEFRAME_H4, 'bars': 3000, 'style': 'Swing', 'cost_mult': 1.0},
    'D1': {'mt5': mt5.TIMEFRAME_D1, 'bars': 2000, 'style': 'Position', 'cost_mult': 0.8},
}

# All strategies with their parameters
STRATEGIES = {
    # Momentum Strategies
    'MOM_12M': {
        'name': 'Momentum 12-Month',
        'category': 'Momentum',
        'params': {'lookback': 252},
        'func': 'momentum_strategy'
    },
    'MOM_6M': {
        'name': 'Momentum 6-Month',
        'category': 'Momentum',
        'params': {'lookback': 126},
        'func': 'momentum_strategy'
    },
    'MOM_3M': {
        'name': 'Momentum 3-Month',
        'category': 'Momentum',
        'params': {'lookback': 63},
        'func': 'momentum_strategy'
    },
    
    # Mean Reversion
    'MR_BB20': {
        'name': 'Mean Rev BB(20,2.5)',
        'category': 'Mean Reversion',
        'params': {'period': 20, 'std': 2.5},
        'func': 'mean_reversion_bb'
    },
    'MR_BB20_2': {
        'name': 'Mean Rev BB(20,2.0)',
        'category': 'Mean Reversion',
        'params': {'period': 20, 'std': 2.0},
        'func': 'mean_reversion_bb'
    },
    'MR_BB50': {
        'name': 'Mean Rev BB(50,2.5)',
        'category': 'Mean Reversion',
        'params': {'period': 50, 'std': 2.5},
        'func': 'mean_reversion_bb'
    },
    
    # RSI Strategies
    'RSI_2_10': {
        'name': 'RSI(2) Extremes 10/90',
        'category': 'Mean Reversion',
        'params': {'period': 2, 'oversold': 10, 'overbought': 90},
        'func': 'rsi_extremes'
    },
    'RSI_2_20': {
        'name': 'RSI(2) Extremes 20/80',
        'category': 'Mean Reversion',
        'params': {'period': 2, 'oversold': 20, 'overbought': 80},
        'func': 'rsi_extremes'
    },
    'RSI_14': {
        'name': 'RSI(14) Classic 30/70',
        'category': 'Mean Reversion',
        'params': {'period': 14, 'oversold': 30, 'overbought': 70},
        'func': 'rsi_extremes'
    },
    
    # Breakout Strategies
    'BREAK_55': {
        'name': 'Turtle Breakout 55/20',
        'category': 'Breakout',
        'params': {'entry_period': 55, 'exit_period': 20},
        'func': 'breakout_strategy'
    },
    'BREAK_20': {
        'name': 'Breakout 20/10',
        'category': 'Breakout',
        'params': {'entry_period': 20, 'exit_period': 10},
        'func': 'breakout_strategy'
    },
    
    # EMA Cross
    'EMA_8_21': {
        'name': 'EMA Cross 8/21',
        'category': 'Trend',
        'params': {'fast': 8, 'slow': 21},
        'func': 'ema_cross'
    },
    'EMA_12_26': {
        'name': 'EMA Cross 12/26 (MACD)',
        'category': 'Trend',
        'params': {'fast': 12, 'slow': 26},
        'func': 'ema_cross'
    },
    'EMA_50_200': {
        'name': 'EMA Cross 50/200 (Golden)',
        'category': 'Trend',
        'params': {'fast': 50, 'slow': 200},
        'func': 'ema_cross'
    },
    
    # Trend Following
    'TREND_SMA50': {
        'name': 'Trend Follow SMA50',
        'category': 'Trend',
        'params': {'sma_period': 50},
        'func': 'trend_following'
    },
    'TREND_SMA200': {
        'name': 'Trend Follow SMA200',
        'category': 'Trend',
        'params': {'sma_period': 200},
        'func': 'trend_following'
    },
    
    # Pullback
    'PULLBACK_RSI': {
        'name': 'RSI Pullback in Trend',
        'category': 'Pullback',
        'params': {},
        'func': 'pullback_rsi'
    },
    
    # Channel
    'KELTNER': {
        'name': 'Keltner Channel Break',
        'category': 'Breakout',
        'params': {'period': 20, 'mult': 2.0},
        'func': 'keltner_channel'
    },
}


# ============================================
# STRATEGY IMPLEMENTATIONS
# ============================================

def momentum_strategy(df, lookback=252):
    close = df['close']
    if len(close) < lookback + 50:
        return None, None
    
    returns = close.pct_change(lookback)
    entries = returns > 0
    exits = returns <= 0
    return entries, exits

def mean_reversion_bb(df, period=20, std=2.5):
    close = df['close']
    if len(close) < period + 50:
        return None, None
    
    sma = close.rolling(period).mean()
    std_dev = close.rolling(period).std()
    lower = sma - std * std_dev
    
    entries = close < lower
    exits = close > sma
    return entries, exits

def rsi_extremes(df, period=2, oversold=10, overbought=90):
    close = df['close']
    if len(close) < 100:
        return None, None
    
    rsi = vbt.RSI.run(close, window=period).rsi
    entries = rsi < oversold
    exits = rsi > 50
    return entries, exits

def breakout_strategy(df, entry_period=55, exit_period=20):
    close = df['close']
    high = df['high']
    low = df['low']
    if len(close) < entry_period + 50:
        return None, None
    
    high_entry = high.rolling(entry_period).max().shift(1)
    low_exit = low.rolling(exit_period).min().shift(1)
    
    entries = close > high_entry
    exits = close < low_exit
    return entries, exits

def ema_cross(df, fast=8, slow=21):
    close = df['close']
    if len(close) < slow + 50:
        return None, None
    
    ema_fast = close.ewm(span=fast).mean()
    ema_slow = close.ewm(span=slow).mean()
    
    entries = (ema_fast.shift(1) < ema_slow.shift(1)) & (ema_fast > ema_slow)
    exits = (ema_fast.shift(1) > ema_slow.shift(1)) & (ema_fast < ema_slow)
    return entries, exits

def trend_following(df, sma_period=50):
    close = df['close']
    if len(close) < sma_period + 50:
        return None, None
    
    sma = close.rolling(sma_period).mean()
    entries = (close.shift(1) < sma.shift(1)) & (close > sma)
    exits = close < sma
    return entries, exits

def pullback_rsi(df):
    close = df['close']
    if len(close) < 100:
        return None, None
    
    sma50 = close.rolling(50).mean()
    rsi = vbt.RSI.run(close, window=14).rsi
    
    entries = (close > sma50) & (rsi < 40) & (rsi.shift(1) >= 40)
    exits = (rsi > 70) | (close < sma50)
    return entries, exits

def keltner_channel(df, period=20, mult=2.0):
    close = df['close']
    high = df['high']
    low = df['low']
    if len(close) < period + 50:
        return None, None
    
    ema = close.ewm(span=period).mean()
    atr = (high - low).rolling(period).mean()
    upper = ema + mult * atr
    
    entries = close > upper.shift(1)
    exits = close < ema
    return entries, exits


# Strategy dispatcher
STRATEGY_FUNCS = {
    'momentum_strategy': momentum_strategy,
    'mean_reversion_bb': mean_reversion_bb,
    'rsi_extremes': rsi_extremes,
    'breakout_strategy': breakout_strategy,
    'ema_cross': ema_cross,
    'trend_following': trend_following,
    'pullback_rsi': pullback_rsi,
    'keltner_channel': keltner_channel,
}


def fetch_data(symbol, timeframe_config):
    """Fetch data from MT5"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe_config['mt5'], 0, timeframe_config['bars'])
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df


def run_single_backtest(symbol, symbol_config, tf_name, tf_config, strat_id, strat_config):
    """Run a single backtest and return results"""
    
    # Fetch data
    df = fetch_data(symbol, tf_config)
    if df is None or len(df) < 200:
        return None
    
    close = df['close']
    
    # Get strategy function
    func = STRATEGY_FUNCS.get(strat_config['func'])
    if func is None:
        return None
    
    # Run strategy
    try:
        entries, exits = func(df, **strat_config['params'])
        if entries is None:
            return None
    except Exception as e:
        return None
    
    # Calculate costs (spread-based)
    base_spread = symbol_config['spread']
    cost = base_spread * tf_config['cost_mult']
    
    # Run vectorbt portfolio
    try:
        pf = vbt.Portfolio.from_signals(
            close,
            entries=entries,
            exits=exits,
            init_cash=10000,
            fees=cost,
            slippage=cost * 0.5,
            freq='1D'
        )
        
        # Extract metrics
        total_return = pf.total_return() * 100
        sharpe = pf.sharpe_ratio()
        max_dd = pf.max_drawdown() * 100
        n_trades = pf.trades.count()
        
        if n_trades == 0:
            return None
        
        win_rate = pf.trades.win_rate() * 100
        
        # Calculate data range
        years = (df.index[-1] - df.index[0]).days / 365.25
        
        return {
            'backtest_id': f"{strat_id}_{symbol}_{tf_name}",
            'strategy_id': strat_id,
            'strategy_name': strat_config['name'],
            'strategy_category': strat_config['category'],
            'symbol': symbol,
            'symbol_category': symbol_config['category'],
            'timeframe': tf_name,
            'style': tf_config['style'],
            'data_start': df.index[0].strftime('%Y-%m-%d'),
            'data_end': df.index[-1].strftime('%Y-%m-%d'),
            'bars': len(df),
            'years': round(years, 2),
            'commission': round(cost * 100, 3),
            'total_return': round(total_return, 2) if not np.isnan(total_return) else 0,
            'sharpe': round(sharpe, 2) if not np.isnan(sharpe) else 0,
            'max_dd': round(max_dd, 2) if not np.isnan(max_dd) else 0,
            'win_rate': round(win_rate, 1) if not np.isnan(win_rate) else 0,
            'trades': int(n_trades),
            'params': strat_config['params'],
        }
    except Exception as e:
        return None


def run_comprehensive_matrix():
    """Run ALL combinations"""
    
    console.print(Panel.fit(
        "[bold cyan]COMPREHENSIVE STRATEGY MATRIX BACKTEST[/bold cyan]\n"
        "[dim]Testing ALL Strategy × Symbol × Timeframe Combinations[/dim]",
        border_style="cyan"
    ))
    
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return None
    
    # Calculate total combinations
    total_combos = len(STRATEGIES) * len(SYMBOLS) * len(TIMEFRAMES)
    
    console.print(f"\n[bold]TEST MATRIX[/bold]")
    console.print(f"  Strategies: {len(STRATEGIES)}")
    console.print(f"  Symbols: {len(SYMBOLS)}")
    console.print(f"  Timeframes: {len(TIMEFRAMES)}")
    console.print(f"  [bold cyan]Total Combinations: {total_combos}[/bold cyan]")
    
    console.print(f"\n[bold]STRATEGIES:[/bold]")
    for sid, s in STRATEGIES.items():
        console.print(f"  {sid}: {s['name']} ({s['category']})")
    
    console.print(f"\n[bold]SYMBOLS:[/bold] {', '.join(SYMBOLS.keys())}")
    console.print(f"[bold]TIMEFRAMES:[/bold] {', '.join(TIMEFRAMES.keys())}")
    
    console.print(f"\n[bold]RUNNING BACKTESTS...[/bold]\n")
    
    all_results = []
    completed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        task = progress.add_task("Testing...", total=total_combos)
        
        for strat_id, strat_config in STRATEGIES.items():
            for symbol, symbol_config in SYMBOLS.items():
                for tf_name, tf_config in TIMEFRAMES.items():
                    
                    progress.update(task, description=f"{strat_id} × {symbol} × {tf_name}")
                    
                    result = run_single_backtest(
                        symbol, symbol_config,
                        tf_name, tf_config,
                        strat_id, strat_config
                    )
                    
                    if result:
                        all_results.append(result)
                        
                        # Log to database
                        logger.log_backtest(
                            strategy_name=result['strategy_name'],
                            symbol=result['symbol'],
                            timeframe=result['timeframe'],
                            style=result['style'],
                            data_start=result['data_start'],
                            data_end=result['data_end'],
                            bars=result['bars'],
                            years=result['years'],
                            parameters=result['params'],
                            commission=result['commission'] / 100,
                            initial_capital=10000,
                            total_return=result['total_return'],
                            sharpe_ratio=result['sharpe'],
                            max_drawdown=result['max_dd'],
                            win_rate=result['win_rate'],
                            total_trades=result['trades'],
                            verdict='DEPLOY' if result['sharpe'] >= 1.0 else 'WEAK' if result['sharpe'] >= 0.5 else 'SKIP',
                            notes=f"Matrix backtest: {strat_id}"
                        )
                    
                    completed += 1
                    progress.update(task, advance=1)
    
    mt5.shutdown()
    
    console.print(f"\n[bold green]Completed: {completed} tests, {len(all_results)} valid results[/bold green]")
    
    return all_results


def generate_charts(results):
    """Generate professional charts"""
    
    if not results:
        return
    
    df = pd.DataFrame(results)
    
    # Create charts directory
    os.makedirs('docs/charts', exist_ok=True)
    
    # 1. Sharpe Distribution by Strategy Category
    fig, ax = plt.subplots(figsize=(12, 6))
    categories = df.groupby('strategy_category')['sharpe'].mean().sort_values(ascending=False)
    colors = ['green' if v >= 0.5 else 'orange' if v >= 0 else 'red' for v in categories.values]
    categories.plot(kind='bar', ax=ax, color=colors)
    ax.axhline(y=1.0, color='green', linestyle='--', label='Strong Edge (1.0)')
    ax.axhline(y=0.5, color='orange', linestyle='--', label='Weak Edge (0.5)')
    ax.axhline(y=0, color='red', linestyle='-', alpha=0.5)
    ax.set_title('Average Sharpe Ratio by Strategy Category')
    ax.set_xlabel('Strategy Category')
    ax.set_ylabel('Average Sharpe Ratio')
    ax.legend()
    plt.tight_layout()
    plt.savefig('docs/charts/sharpe_by_category.png', dpi=150)
    plt.close()
    
    # 2. Sharpe by Timeframe
    fig, ax = plt.subplots(figsize=(10, 6))
    tf_order = ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    tf_sharpe = df.groupby('timeframe')['sharpe'].mean().reindex(tf_order)
    colors = ['green' if v >= 0.5 else 'orange' if v >= 0 else 'red' for v in tf_sharpe.values]
    tf_sharpe.plot(kind='bar', ax=ax, color=colors)
    ax.axhline(y=1.0, color='green', linestyle='--', label='Strong Edge')
    ax.set_title('Average Sharpe Ratio by Timeframe')
    ax.set_xlabel('Timeframe')
    ax.set_ylabel('Average Sharpe Ratio')
    plt.tight_layout()
    plt.savefig('docs/charts/sharpe_by_timeframe.png', dpi=150)
    plt.close()
    
    # 3. Sharpe by Symbol Category
    fig, ax = plt.subplots(figsize=(10, 6))
    sym_sharpe = df.groupby('symbol_category')['sharpe'].mean().sort_values(ascending=False)
    colors = ['green' if v >= 0.5 else 'orange' if v >= 0 else 'red' for v in sym_sharpe.values]
    sym_sharpe.plot(kind='bar', ax=ax, color=colors)
    ax.axhline(y=1.0, color='green', linestyle='--')
    ax.set_title('Average Sharpe Ratio by Symbol Category')
    ax.set_xlabel('Category')
    ax.set_ylabel('Average Sharpe Ratio')
    plt.tight_layout()
    plt.savefig('docs/charts/sharpe_by_symbol_category.png', dpi=150)
    plt.close()
    
    # 4. Heatmap: Strategy vs Timeframe
    pivot = df.pivot_table(values='sharpe', index='strategy_category', columns='timeframe', aggfunc='mean')
    pivot = pivot.reindex(columns=tf_order)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(pivot.values, cmap='RdYlGn', vmin=-1, vmax=2)
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index)
    plt.colorbar(im, label='Sharpe Ratio')
    ax.set_title('Strategy Category × Timeframe Heatmap')
    
    # Add values
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            val = pivot.values[i, j]
            if not np.isnan(val):
                ax.text(j, i, f'{val:.2f}', ha='center', va='center', fontsize=8)
    
    plt.tight_layout()
    plt.savefig('docs/charts/heatmap_strategy_timeframe.png', dpi=150)
    plt.close()
    
    console.print("[green]Charts saved to docs/charts/[/green]")


def generate_summary_report(results):
    """Generate comprehensive markdown report"""
    
    if not results:
        return
    
    df = pd.DataFrame(results)
    df = df.sort_values('sharpe', ascending=False)
    
    # Statistics
    total = len(df)
    strong = len(df[df['sharpe'] >= 1.0])
    weak = len(df[(df['sharpe'] >= 0.5) & (df['sharpe'] < 1.0)])
    fail = len(df[df['sharpe'] < 0.5])
    
    report = f"""# Comprehensive Strategy Matrix Backtest Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Strategies | {len(STRATEGIES)} |
| Symbols | {len(SYMBOLS)} |
| Timeframes | {len(TIMEFRAMES)} |
| Total Combinations | {len(STRATEGIES) * len(SYMBOLS) * len(TIMEFRAMES)} |
| Valid Results | {total} |

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Backtests | {total} |
| **Strong Edge (Sharpe >= 1.0)** | **{strong}** ({strong/total*100:.1f}%) |
| Weak Edge (Sharpe 0.5-1.0) | {weak} ({weak/total*100:.1f}%) |
| No Edge (Sharpe < 0.5) | {fail} ({fail/total*100:.1f}%) |
| Average Sharpe | {df['sharpe'].mean():.2f} |
| Best Sharpe | {df['sharpe'].max():.2f} |
| Worst Sharpe | {df['sharpe'].min():.2f} |

## Charts

### Sharpe by Strategy Category
![Sharpe by Category](charts/sharpe_by_category.png)

### Sharpe by Timeframe
![Sharpe by Timeframe](charts/sharpe_by_timeframe.png)

### Sharpe by Symbol Category
![Sharpe by Symbol](charts/sharpe_by_symbol_category.png)

### Strategy × Timeframe Heatmap
![Heatmap](charts/heatmap_strategy_timeframe.png)

## Top 30 Performing Combinations

| Rank | Strategy | Symbol | TF | Sharpe | Return | MaxDD | Win% | Trades |
|------|----------|--------|-----|--------|--------|-------|------|--------|
"""
    
    for i, (_, row) in enumerate(df.head(30).iterrows(), 1):
        report += f"| {i} | {row['strategy_name']} | {row['symbol']} | {row['timeframe']} | **{row['sharpe']}** | {row['total_return']}% | {row['max_dd']}% | {row['win_rate']}% | {row['trades']} |\n"
    
    report += f"""

## Performance by Category

### By Strategy Category
"""
    cat_stats = df.groupby('strategy_category').agg({
        'sharpe': ['mean', 'max', 'count'],
        'total_return': 'mean'
    }).round(2)
    
    for cat in cat_stats.index:
        stats = cat_stats.loc[cat]
        report += f"- **{cat}**: Avg Sharpe {stats[('sharpe', 'mean')]}, Best {stats[('sharpe', 'max')]}, Tests {int(stats[('sharpe', 'count')])}\n"
    
    report += """

### By Timeframe
"""
    tf_stats = df.groupby('timeframe').agg({
        'sharpe': ['mean', 'max'],
        'trades': 'sum'
    }).round(2)
    
    for tf in ['M5', 'M15', 'M30', 'H1', 'H4', 'D1']:
        if tf in tf_stats.index:
            stats = tf_stats.loc[tf]
            report += f"- **{tf}**: Avg Sharpe {stats[('sharpe', 'mean')]}, Best {stats[('sharpe', 'max')]}\n"
    
    report += """

### By Symbol
"""
    sym_stats = df.groupby('symbol').agg({
        'sharpe': ['mean', 'max']
    }).round(2).sort_values(('sharpe', 'mean'), ascending=False)
    
    for sym in sym_stats.index:
        stats = sym_stats.loc[sym]
        report += f"- **{sym}**: Avg Sharpe {stats[('sharpe', 'mean')]}, Best {stats[('sharpe', 'max')]}\n"
    
    report += f"""

## Deployment Recommendations

### Ready for Paper Trading (Sharpe >= 1.0, 20+ trades)
"""
    deployable = df[(df['sharpe'] >= 1.0) & (df['trades'] >= 20)]
    
    if len(deployable) > 0:
        for _, row in deployable.head(10).iterrows():
            report += f"1. **{row['symbol']} × {row['strategy_name']} ({row['timeframe']})**: Sharpe {row['sharpe']}, {row['trades']} trades\n"
    else:
        report += "No combinations met deployment criteria.\n"
    
    report += f"""

## Data Quality

| Symbol | Timeframe | Bars | Years | Date Range |
|--------|-----------|------|-------|------------|
"""
    for _, row in df.drop_duplicates(['symbol', 'timeframe'])[['symbol', 'timeframe', 'bars', 'years', 'data_start', 'data_end']].iterrows():
        report += f"| {row['symbol']} | {row['timeframe']} | {row['bars']} | {row['years']} | {row['data_start']} to {row['data_end']} |\n"
    
    # Save report
    with open('docs/COMPREHENSIVE_BACKTEST_REPORT.md', 'w') as f:
        f.write(report)
    
    # Save CSV
    df.to_csv('data/comprehensive_matrix_results.csv', index=False)
    
    console.print("[green]Report saved: docs/COMPREHENSIVE_BACKTEST_REPORT.md[/green]")
    console.print("[green]CSV saved: data/comprehensive_matrix_results.csv[/green]")


if __name__ == "__main__":
    console.print("\n[bold]Starting Comprehensive Strategy Matrix Backtest...[/bold]\n")
    
    results = run_comprehensive_matrix()
    
    if results:
        console.print("\n[bold]Generating Charts...[/bold]")
        generate_charts(results)
        
        console.print("\n[bold]Generating Report...[/bold]")
        generate_summary_report(results)
        
        # Quick summary
        df = pd.DataFrame(results)
        strong = len(df[df['sharpe'] >= 1.0])
        
        console.print(f"\n[bold cyan]MATRIX COMPLETE[/bold cyan]")
        console.print(f"  Total Valid Tests: {len(df)}")
        console.print(f"  Strong Edge: {strong}")
        
        if strong > 0:
            best = df.loc[df['sharpe'].idxmax()]
            console.print(f"\n🏆 Best: {best['symbol']} × {best['strategy_name']} ({best['timeframe']})")
            console.print(f"   Sharpe: {best['sharpe']}, Return: {best['total_return']}%")
