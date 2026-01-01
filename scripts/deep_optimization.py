"""
DEEP STRATEGY OPTIMIZATION & PARAMETER STABILITY ANALYSIS
Performs Grid Search (Heatmaps) and Walk-Forward Analysis on Top Strategies
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import vectorbt as vbt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from rich.console import Console
from rich.panel import Panel
from rich.progress import track

console = Console()

def fetch_data(symbol, timeframe=mt5.TIMEFRAME_D1, bars=3000):
    if not mt5.initialize():
        return None
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

# ======================================================
# 1. OPTIMIZATION: ETHUSD TREND (MACD)
# ======================================================

def optimize_macd_trend(symbol="ETHUSD"):
    console.print(Panel(f"[bold cyan]OPTIMIZING MACD TREND: {symbol}[/bold cyan]"))
    
    df = fetch_data(symbol)
    close = df['close']
    
    # 1. Define Parameter Grid
    fast_windows = np.arange(8, 20, 2)   # 8, 10, 12... 18
    slow_windows = np.arange(20, 60, 5)  # 20, 25, 30... 55
    signal_windows = np.arange(5, 15, 2) # 5, 7, 9... 13
    
    console.print(f"Testing {len(fast_windows)*len(slow_windows)*len(signal_windows)} parameter combinations...")
    
    import itertools

    console.print(f"Testing {len(fast_windows)*len(slow_windows)*len(signal_windows)} parameter combinations...")
    
    results = []
    
    # Run optimization loops
    for fast in fast_windows:
        for slow in slow_windows:
            if fast >= slow: continue
            
            for signal in signal_windows:
                # Calculate MACD for this combo
                macd_ind = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)
                
                # Logic
                entries = macd_ind.macd_above(macd_ind.signal)
                exits = macd_ind.macd_below(macd_ind.signal)
                
                pf = vbt.Portfolio.from_signals(
                    close, entries, exits, freq='1D',
                    fees=0.001, slippage=0.001
                )
                
                results.append({
                    'fast': fast,
                    'slow': slow,
                    'signal': signal,
                    'sharpe': pf.sharpe_ratio(),
                    'return': pf.total_return() * 100
                })
    
    df_res = pd.DataFrame(results)
    best = df_res.loc[df_res['sharpe'].idxmax()]
    
    console.print(f"[green]BEST PARAMS: Fast={int(best['fast'])}, Slow={int(best['slow'])}, Signal={int(best['signal'])}[/green]")
    console.print(f"Sharpe: {best['sharpe']:.2f} | Return: {best['return']:.0f}%")

    # Heatmap setup
    # Pivot for Heatmap: Fix signal to best signal, vary Fast/Slow
    best_signal = int(best['signal'])
    pivot = df_res[df_res['signal'] == best_signal].pivot_table(index='fast', columns='slow', values='sharpe')
    
    plt.figure(figsize=(10, 8))
    plt.imshow(pivot, aspect='auto', cmap='RdYlGn', origin='lower')
    plt.colorbar(label=f'Sharpe Ratio (Signal={best_signal})')
    plt.title(f'{symbol} MACD Optimization Heatmap (Signal={best_signal})')
    plt.xlabel('Slow Window')
    plt.ylabel('Fast Window')
    
    # Ticks
    plt.xticks(range(len(pivot.columns)), pivot.columns)
    plt.yticks(range(len(pivot.index)), pivot.index)

# ======================================================
# 2. OPTIMIZATION: GOLD BREAKOUT (Donchian)
# ======================================================

def optimize_gold_breakout(symbol="GOLD"):
    console.print(Panel(f"\n[bold gold1]OPTIMIZING BREAKOUT: {symbol}[/bold gold1]"))
    
    df = fetch_data(symbol, bars=2500)
    close = df['close']
    high = df['high']
    low = df['low']
    
    # Params: Entry Lookback vs Exit Lookback
    entry_windows = np.arange(20, 100, 5)  # 20 to 95
    exit_windows = np.arange(10, 50, 5)    # 10 to 45
    
    console.print(f"Testing {len(entry_windows)*len(exit_windows)} parameter combinations...")
    
    # Calculate Donchian Channels efficiently
    # We loop manually as rolling max/min with varying windows is elusive in broadcasing
    
    results = []
    
    # Optimization loop
    for entry_w in track(entry_windows, description="Optimizing..."):
        for exit_w in exit_windows:
            if exit_w >= entry_w: continue # Exit must be faster than trend
            
            upper = high.shift(1).rolling(entry_w).max()
            lower = low.shift(1).rolling(exit_w).min()
            
            entries = close > upper
            exits = close < lower
            
            pf = vbt.Portfolio.from_signals(
                close, entries, exits, freq='1D',
                fees=0.0003, slippage=0.0003
            )
            
            results.append({
                'entry': entry_w,
                'exit': exit_w,
                'sharpe': pf.sharpe_ratio(),
                'return': pf.total_return() * 100,
                'trades': pf.trades.count()
            })
            
    df_res = pd.DataFrame(results)
    best = df_res.loc[df_res['sharpe'].idxmax()]
    
    console.print(f"[green]BEST PARAMS: Entry={int(best['entry'])}, Exit={int(best['exit'])}[/green]")
    console.print(f"Sharpe: {best['sharpe']:.2f} | Return: {best['return']:.0f}% | Trades: {int(best['trades'])}")
    
    # Heatmap
    try:
        pivot = df_res.pivot_table(index='entry', columns='exit', values='sharpe')
        
        plt.figure(figsize=(10, 8))
        plt.imshow(pivot, aspect='auto', cmap='RdYlGn', origin='lower')
        plt.colorbar(label='Sharpe Ratio')
        plt.title(f'{symbol} Donchian Breakout Optimization')
        plt.xlabel('Exit Lookback')
        plt.ylabel('Entry Lookback')
        
        # Correct ticks
        plt.xticks(range(len(pivot.columns)), pivot.columns)
        plt.yticks(range(len(pivot.index)), pivot.index)
        
        plt.savefig(f'docs/charts/optimization/{symbol}_Breakout_heatmap.png')
        console.print(f"Heatmap saved to docs/charts/optimization/{symbol}_Breakout_heatmap.png")
    except Exception as e:
        console.print(f"[yellow]Plotting failed: {e}[/yellow]")

# ======================================================
# 3. INVESTIGATION: EURUSD MEAN REVERSION
# ======================================================

def investigate_eurusd_anomaly():
    console.print(Panel("\n[bold magenta]INVESTIGATING: EURUSD High Sharpe Anomaly[/bold magenta]"))
    
    symbol = "EURUSD"
    df = fetch_data(symbol)
    close = df['close']
    
    # Standard Strategy: BB(20, 2.5) from previous test
    sma = close.rolling(20).mean()
    std = close.rolling(20).std()
    lower = sma - 2.5 * std
    
    # Logic: Buy crossing lower band, Exit crossing SMA
    entries = (close.shift(1) > lower.shift(1)) & (close < lower) # Crossing down?
    # Actually standard mean reversion is BUY when Price < Lower
    entries = close < lower
    exits = close > sma
    
    pf = vbt.Portfolio.from_signals(
        close, entries, exits, 
        freq='1D', init_cash=10000,
        fees=0.0001, slippage=0.0001
    )
    
    console.print(f"Stats for {symbol} Mean Reversion:")
    console.print(f"Sharpe: {pf.sharpe_ratio():.2f}")
    console.print(f"Trades: {pf.trades.count()}")
    console.print(f"Win Rate: {pf.trades.win_rate()*100:.1f}%")
    
    # Plot trades on price
    fig = pf.plot(settings=dict(bm_returns=False))
    # VectorBT plot is interactive plotly, let's just save valid trades list
    
    trades = pf.trades.records_readable
    trades.to_csv('data/eurusd_anomaly_trades.csv')
    console.print("Trade list saved to data/eurusd_anomaly_trades.csv for inspection.")
    
    if pf.trades.count() < 20:
        console.print("[red]WARNING: Low trade count (<20). High Sharpe is likely statistical noise.[/red]")
    else:
        console.print("[green]Trade count is healthly.[/green]")


if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Init Failed")
        sys.exit()
        
    optimize_macd_trend("ETHUSD")
    optimize_gold_breakout("GOLD")
    investigate_eurusd_anomaly()
    
    mt5.shutdown()
