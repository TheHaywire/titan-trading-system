"""
VECTORBT PROFESSIONAL BACKTESTING
Industry-standard vectorized backtesting with proper metrics
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import vectorbt as vbt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def fetch_mt5_data(symbol, timeframe, bars=2000):
    """Fetch data from MT5"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def extract_metrics(pf, close, initial_capital):
    """Safely extract metrics from portfolio"""
    try:
        total_return = pf.total_return() * 100
        sharpe = pf.sharpe_ratio()
        sortino = pf.sortino_ratio()
        max_dd = pf.max_drawdown() * 100
        n_trades = pf.trades.count()
        win_rate = pf.trades.win_rate() * 100 if n_trades > 0 else 0
        
        benchmark = (close.iloc[-1] / close.iloc[0] - 1) * 100
        
        return {
            'total_return': round(total_return, 2) if not np.isnan(total_return) else 0,
            'sharpe': round(sharpe, 2) if not np.isnan(sharpe) else 0,
            'sortino': round(sortino, 2) if not np.isnan(sortino) else 0,
            'max_dd': round(max_dd, 2) if not np.isnan(max_dd) else 0,
            'win_rate': round(win_rate, 1) if not np.isnan(win_rate) else 0,
            'trades': int(n_trades),
            'benchmark': round(benchmark, 2)
        }
    except Exception as e:
        return None

def run_vectorbt_backtest():
    """Run professional backtest using vectorbt"""
    
    console.print(Panel.fit(
        "[bold cyan]VECTORBT PROFESSIONAL BACKTESTING[/bold cyan]\n"
        "[dim]Industry-standard vectorized backtesting library[/dim]",
        border_style="cyan"
    ))
    
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return
    
    # Configuration
    symbols = ["BTCUSD", "ETHUSD", "GOLD", "EURUSD", "GBPUSD", "US500Cash"]
    initial_capital = 10000
    commission = 0.001  # 0.1% commission per trade
    slippage = 0.001    # 0.1% slippage
    
    all_results = []
    
    console.print("\n[bold]CONFIGURATION[/bold]")
    console.print(f"  Initial Capital: ${initial_capital:,}")
    console.print(f"  Commission: {commission*100}% per trade")
    console.print(f"  Slippage: {slippage*100}%")
    console.print(f"  Timeframe: Daily (D1)")
    console.print(f"  Symbols: {', '.join(symbols)}")
    
    console.print("\n[bold]RUNNING BACKTESTS...[/bold]\n")
    
    for symbol in symbols:
        console.print(f"  Processing {symbol}...")
        
        # Fetch data
        df = fetch_mt5_data(symbol, mt5.TIMEFRAME_D1, 2000)
        
        if df is None or len(df) < 300:
            console.print(f"    [yellow]Skipping - insufficient data[/yellow]")
            continue
        
        close = df['close']
        
        # Data info
        years = (df.index[-1] - df.index[0]).days / 365.25
        console.print(f"    Data: {len(df)} bars, {years:.1f} years")
        console.print(f"    Range: {df.index[0].strftime('%Y-%m-%d')} to {df.index[-1].strftime('%Y-%m-%d')}")
        
        # Strategy 1: Dual Momentum (12-month lookback)
        try:
            momentum_12m = close.pct_change(252)
            entries_mom = momentum_12m > 0
            exits_mom = momentum_12m <= 0
            
            pf_momentum = vbt.Portfolio.from_signals(
                close,
                entries=entries_mom,
                exits=exits_mom,
                init_cash=initial_capital,
                fees=commission,
                slippage=slippage,
                freq='1D'
            )
            
            metrics = extract_metrics(pf_momentum, close, initial_capital)
            if metrics:
                metrics['symbol'] = symbol
                metrics['strategy'] = 'Momentum'
                all_results.append(metrics)
                console.print(f"    [green]Momentum: Sharpe {metrics['sharpe']}[/green]")
        except Exception as e:
            console.print(f"    [red]Momentum error: {e}[/red]")
        
        # Strategy 2: Mean Reversion (Bollinger Bands)
        try:
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            lower_band = sma - 2.5 * std
            
            entries_mr = close < lower_band
            exits_mr = close > sma
            
            pf_mean_rev = vbt.Portfolio.from_signals(
                close,
                entries=entries_mr,
                exits=exits_mr,
                init_cash=initial_capital,
                fees=commission,
                slippage=slippage,
                freq='1D'
            )
            
            metrics = extract_metrics(pf_mean_rev, close, initial_capital)
            if metrics:
                metrics['symbol'] = symbol
                metrics['strategy'] = 'Mean Reversion'
                all_results.append(metrics)
                console.print(f"    [green]Mean Rev: Sharpe {metrics['sharpe']}[/green]")
        except Exception as e:
            console.print(f"    [red]Mean Reversion error: {e}[/red]")
        
        # Strategy 3: RSI Extremes
        try:
            rsi = vbt.RSI.run(close, window=2).rsi
            
            entries_rsi = rsi < 10
            exits_rsi = rsi > 50
            
            pf_rsi = vbt.Portfolio.from_signals(
                close,
                entries=entries_rsi,
                exits=exits_rsi,
                init_cash=initial_capital,
                fees=commission,
                slippage=slippage,
                freq='1D'
            )
            
            metrics = extract_metrics(pf_rsi, close, initial_capital)
            if metrics:
                metrics['symbol'] = symbol
                metrics['strategy'] = 'RSI Extremes'
                all_results.append(metrics)
                console.print(f"    [green]RSI: Sharpe {metrics['sharpe']}[/green]")
        except Exception as e:
            console.print(f"    [red]RSI error: {e}[/red]")
    
    mt5.shutdown()
    
    if not all_results:
        console.print("[red]No results generated[/red]")
        return
    
    # Sort by Sharpe ratio
    all_results.sort(key=lambda x: x['sharpe'], reverse=True)
    
    # Display results
    console.print("\n[bold]BACKTEST RESULTS (vectorbt)[/bold]\n")
    
    table = Table(title="Strategy Performance Matrix", box=box.DOUBLE_EDGE)
    table.add_column("Symbol", style="cyan")
    table.add_column("Strategy", style="magenta")
    table.add_column("Return", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Sortino", justify="right")
    table.add_column("Max DD", justify="right")
    table.add_column("Win %", justify="right")
    table.add_column("Trades", justify="right")
    table.add_column("vs B&H", justify="right")
    
    for r in all_results:
        # Color code Sharpe
        if r['sharpe'] >= 1.0:
            sharpe_str = f"[green bold]{r['sharpe']}[/green bold]"
        elif r['sharpe'] >= 0.5:
            sharpe_str = f"[yellow]{r['sharpe']}[/yellow]"
        else:
            sharpe_str = f"[red]{r['sharpe']}[/red]"
        
        # vs Benchmark
        outperf = r['total_return'] - r['benchmark']
        if outperf > 0:
            vs_bh = f"[green]+{outperf:.1f}%[/green]"
        else:
            vs_bh = f"[red]{outperf:.1f}%[/red]"
        
        table.add_row(
            r['symbol'],
            r['strategy'],
            f"{r['total_return']}%",
            sharpe_str,
            f"{r['sortino']}",
            f"{r['max_dd']}%",
            f"{r['win_rate']}%",
            str(r['trades']),
            vs_bh
        )
    
    console.print(table)
    
    # Summary
    console.print("\n[bold]METHODOLOGY (vectorbt)[/bold]")
    console.print("- Vectorized backtesting (fast & accurate)", style="dim")
    console.print("- Commission: 0.1% per trade", style="dim")
    console.print("- Slippage: 0.1%", style="dim")
    console.print("- Position sizing: Full capital per trade", style="dim")
    console.print("- No leverage", style="dim")
    console.print("- Timeframe: Daily", style="dim")
    console.print("- Data: Last 2000 bars (6-8 years)", style="dim")
    
    # Recommendations
    console.print("\n[bold]DEPLOYMENT RECOMMENDATIONS[/bold]\n")
    
    strong_edge = [r for r in all_results if r['sharpe'] >= 1.0 and r['trades'] >= 10]
    
    if strong_edge:
        console.print("[green]STRATEGIES WITH STRONG EDGE (Sharpe >= 1.0):[/green]\n")
        for r in strong_edge[:5]:
            console.print(f"  [cyan]{r['symbol']}[/cyan] x {r['strategy']}")
            console.print(f"    Sharpe: {r['sharpe']} | Return: {r['total_return']}% | Win: {r['win_rate']}%")
            console.print(f"    Max DD: {r['max_dd']}% | Trades: {r['trades']} | vs B&H: {r['total_return'] - r['benchmark']:.1f}%")
            console.print()
    else:
        console.print("[yellow]No strategies met Sharpe >= 1.0 with sufficient trades[/yellow]")
    
    # Export to CSV
    df_results = pd.DataFrame(all_results)
    df_results.to_csv('data/vectorbt_backtest_results.csv', index=False)
    console.print(f"\n[dim]Results saved to: data/vectorbt_backtest_results.csv[/dim]")
    
    return all_results


if __name__ == "__main__":
    results = run_vectorbt_backtest()
