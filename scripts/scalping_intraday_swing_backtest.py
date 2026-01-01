"""
SCALPING, INTRADAY & SWING STRATEGY BACKTEST
Professional testing on M15, H1, H4 timeframes
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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

def fetch_data(symbol, timeframe, bars=5000):
    """Fetch data from MT5"""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def extract_metrics(pf, close, initial_capital=10000):
    """Safely extract metrics"""
    try:
        total_return = pf.total_return() * 100
        sharpe = pf.sharpe_ratio()
        max_dd = pf.max_drawdown() * 100
        n_trades = pf.trades.count()
        win_rate = pf.trades.win_rate() * 100 if n_trades > 0 else 0
        benchmark = (close.iloc[-1] / close.iloc[0] - 1) * 100
        
        return {
            'total_return': round(total_return, 2) if not np.isnan(total_return) else 0,
            'sharpe': round(sharpe, 2) if not np.isnan(sharpe) else 0,
            'max_dd': round(max_dd, 2) if not np.isnan(max_dd) else 0,
            'win_rate': round(win_rate, 1) if not np.isnan(win_rate) else 0,
            'trades': int(n_trades),
            'benchmark': round(benchmark, 2)
        }
    except:
        return None


# ========== SCALPING STRATEGIES (M15) ==========

def scalping_rsi_bounce(df):
    """RSI(7) bounce from 30/70 levels - quick scalps"""
    close = df['close']
    rsi = vbt.RSI.run(close, window=7).rsi
    
    entries = (rsi.shift(1) < 30) & (rsi > 30)  # RSI bounces from oversold
    exits = (rsi > 70) | (close < close.shift(1) * 0.995)  # TP at 70 or -0.5% SL
    
    return entries, exits

def scalping_ema_cross(df):
    """Fast EMA crossover - 8/21 EMA"""
    close = df['close']
    ema8 = close.ewm(span=8).mean()
    ema21 = close.ewm(span=21).mean()
    
    entries = (ema8.shift(1) < ema21.shift(1)) & (ema8 > ema21)  # Golden cross
    exits = (ema8.shift(1) > ema21.shift(1)) & (ema8 < ema21)  # Death cross
    
    return entries, exits

def scalping_breakout(df):
    """15-bar high breakout with quick exit"""
    close = df['close']
    high_15 = df['high'].rolling(15).max().shift(1)
    low_10 = df['low'].rolling(10).min().shift(1)
    
    entries = close > high_15  # Break above 15-bar high
    exits = close < low_10  # Drop below 10-bar low
    
    return entries, exits


# ========== INTRADAY STRATEGIES (H1) ==========

def intraday_orb(df):
    """Opening Range Breakout - first hour range"""
    close = df['close']
    high = df['high']
    low = df['low']
    
    # Use 4-bar range as "opening range" for H1
    range_high = high.rolling(4).max().shift(1)
    range_low = low.rolling(4).min().shift(1)
    
    entries = close > range_high
    exits = (close < range_low) | (close > range_high * 1.01)  # 1% profit target
    
    return entries, exits

def intraday_vwap_reversion(df):
    """Price reverts to VWAP (SMA20 as proxy)"""
    close = df['close']
    vwap = close.rolling(20).mean()  # Using SMA as VWAP proxy
    
    entries = close < vwap * 0.99  # 1% below VWAP
    exits = close > vwap  # Return to VWAP
    
    return entries, exits

def intraday_momentum(df):
    """Momentum continuation - 20-bar momentum"""
    close = df['close']
    momentum = close.pct_change(20)
    atr = (df['high'] - df['low']).rolling(14).mean()
    
    entries = momentum > 0.02  # 2% momentum in 20 bars
    exits = (momentum < 0) | (close < close.shift(1) - atr.shift(1))  # Momentum reverses or ATR stop
    
    return entries, exits


# ========== SWING STRATEGIES (H4) ==========

def swing_trend_follow(df):
    """Trend following - price above 50 SMA with momentum"""
    close = df['close']
    sma50 = close.rolling(50).mean()
    sma20 = close.rolling(20).mean()
    
    entries = (close > sma50) & (sma20 > sma50) & (close > close.shift(10))
    exits = (close < sma20) | (close < sma50)
    
    return entries, exits

def swing_pullback(df):
    """Buy pullback in uptrend"""
    close = df['close']
    sma50 = close.rolling(50).mean()
    rsi = vbt.RSI.run(close, window=14).rsi
    
    # Uptrend + RSI pullback
    entries = (close > sma50) & (rsi < 40) & (rsi.shift(1) >= 40)
    exits = (rsi > 70) | (close < sma50)
    
    return entries, exits

def swing_channel_break(df):
    """Keltner channel breakout"""
    close = df['close']
    ema20 = close.ewm(span=20).mean()
    atr = (df['high'] - df['low']).rolling(20).mean()
    
    upper = ema20 + 2 * atr
    lower = ema20 - 2 * atr
    
    entries = close > upper.shift(1)  # Break above channel
    exits = close < ema20  # Return to middle
    
    return entries, exits


def run_comprehensive_backtest():
    """Test all strategies across timeframes"""
    
    console.print(Panel.fit(
        "[bold cyan]SCALPING / INTRADAY / SWING BACKTEST[/bold cyan]\n"
        "[dim]Testing short-term strategies on M15, H1, H4[/dim]",
        border_style="cyan"
    ))
    
    if not mt5.initialize():
        console.print("[red]MT5 initialization failed[/red]")
        return
    
    # Configuration
    symbols = ["BTCUSD", "ETHUSD", "GOLD", "EURUSD", "GBPUSD", "US500Cash"]
    
    initial_capital = 10000
    
    # Costs scale with frequency
    costs = {
        'M15': {'commission': 0.0005, 'slippage': 0.0002},  # 0.05% + 0.02%
        'H1': {'commission': 0.0003, 'slippage': 0.0001},   # 0.03% + 0.01%
        'H4': {'commission': 0.0002, 'slippage': 0.0001},   # 0.02% + 0.01%
    }
    
    timeframes = {
        'M15': (mt5.TIMEFRAME_M15, 10000),  # ~100 days
        'H1': (mt5.TIMEFRAME_H1, 5000),      # ~200 days
        'H4': (mt5.TIMEFRAME_H4, 2000),      # ~330 days
    }
    
    strategies = {
        'M15': [
            ('RSI Bounce', scalping_rsi_bounce),
            ('EMA Cross', scalping_ema_cross),
            ('Breakout 15', scalping_breakout),
        ],
        'H1': [
            ('ORB', intraday_orb),
            ('VWAP Rev', intraday_vwap_reversion),
            ('Momentum', intraday_momentum),
        ],
        'H4': [
            ('Trend Follow', swing_trend_follow),
            ('Pullback', swing_pullback),
            ('Channel Break', swing_channel_break),
        ]
    }
    
    all_results = []
    
    # Print configuration
    console.print("\n[bold]CONFIGURATION[/bold]")
    console.print(f"  Capital: ${initial_capital:,}")
    console.print(f"  Symbols: {', '.join(symbols)}")
    console.print("\n  Costs by timeframe:")
    for tf, cost in costs.items():
        console.print(f"    {tf}: Commission {cost['commission']*100:.2f}%, Slippage {cost['slippage']*100:.2f}%")
    
    console.print("\n[bold]RUNNING BACKTESTS...[/bold]\n")
    
    for tf_name, (tf, bars) in timeframes.items():
        console.print(f"\n[bold magenta]--- {tf_name} TIMEFRAME ---[/bold magenta]\n")
        
        for symbol in symbols:
            df = fetch_data(symbol, tf, bars)
            
            if df is None or len(df) < 500:
                continue
            
            close = df['close']
            years = (df.index[-1] - df.index[0]).days / 365.25
            
            console.print(f"  {symbol}: {len(df)} bars, {years:.1f} years")
            
            cost = costs[tf_name]
            
            for strat_name, strat_func in strategies[tf_name]:
                try:
                    entries, exits = strat_func(df)
                    
                    pf = vbt.Portfolio.from_signals(
                        close,
                        entries=entries,
                        exits=exits,
                        init_cash=initial_capital,
                        fees=cost['commission'],
                        slippage=cost['slippage'],
                        freq='1D'
                    )
                    
                    metrics = extract_metrics(pf, close, initial_capital)
                    
                    if metrics and metrics['trades'] > 0:
                        metrics['symbol'] = symbol
                        metrics['strategy'] = strat_name
                        metrics['timeframe'] = tf_name
                        metrics['style'] = 'Scalping' if tf_name == 'M15' else 'Intraday' if tf_name == 'H1' else 'Swing'
                        all_results.append(metrics)
                        
                        # Quick indicator
                        if metrics['sharpe'] >= 1.0:
                            console.print(f"    [green]{strat_name}: Sharpe {metrics['sharpe']}[/green]")
                        elif metrics['sharpe'] >= 0.5:
                            console.print(f"    [yellow]{strat_name}: Sharpe {metrics['sharpe']}[/yellow]")
                        else:
                            console.print(f"    [dim]{strat_name}: Sharpe {metrics['sharpe']}[/dim]")
                
                except Exception as e:
                    console.print(f"    [red]{strat_name}: Error - {str(e)[:50]}[/red]")
    
    mt5.shutdown()
    
    if not all_results:
        console.print("\n[red]No results generated[/red]")
        return
    
    # Sort by Sharpe
    all_results.sort(key=lambda x: x['sharpe'], reverse=True)
    
    # Results table
    console.print("\n[bold]COMPLETE RESULTS[/bold]\n")
    
    table = Table(title="Scalping / Intraday / Swing Performance", box=box.DOUBLE_EDGE)
    table.add_column("Style", style="cyan")
    table.add_column("TF")
    table.add_column("Symbol")
    table.add_column("Strategy", style="magenta")
    table.add_column("Sharpe", justify="right")
    table.add_column("Return", justify="right")
    table.add_column("MaxDD", justify="right")
    table.add_column("Win%", justify="right")
    table.add_column("Trades", justify="right")
    
    for r in all_results[:30]:  # Top 30
        sharpe_style = "[green bold]" if r['sharpe'] >= 1.0 else "[yellow]" if r['sharpe'] >= 0.5 else "[red]"
        
        table.add_row(
            r['style'],
            r['timeframe'],
            r['symbol'],
            r['strategy'],
            f"{sharpe_style}{r['sharpe']}[/{sharpe_style.split('[')[1]}",
            f"{r['total_return']}%",
            f"{r['max_dd']}%",
            f"{r['win_rate']}%",
            str(r['trades'])
        )
    
    console.print(table)
    
    # Summary by style
    console.print("\n[bold]SUMMARY BY TRADING STYLE[/bold]\n")
    
    for style in ['Scalping', 'Intraday', 'Swing']:
        style_results = [r for r in all_results if r['style'] == style]
        if style_results:
            avg_sharpe = np.mean([r['sharpe'] for r in style_results])
            best = max(style_results, key=lambda x: x['sharpe'])
            strong = len([r for r in style_results if r['sharpe'] >= 1.0])
            
            console.print(f"[bold]{style}[/bold]:")
            console.print(f"  Tests: {len(style_results)}")
            console.print(f"  Avg Sharpe: {avg_sharpe:.2f}")
            console.print(f"  Strong Edge (Sharpe>=1.0): {strong}")
            console.print(f"  Best: {best['symbol']} x {best['strategy']} (Sharpe {best['sharpe']})")
            console.print()
    
    # Recommendations
    console.print("\n[bold]DEPLOYMENT RECOMMENDATIONS[/bold]\n")
    
    deployable = [r for r in all_results if r['sharpe'] >= 1.0 and r['trades'] >= 20]
    
    if deployable:
        console.print("[green]READY FOR PAPER TRADING:[/green]\n")
        for r in deployable[:5]:
            console.print(f"  {r['style']} | {r['timeframe']} | {r['symbol']} x {r['strategy']}")
            console.print(f"    Sharpe: {r['sharpe']} | Return: {r['total_return']}% | Trades: {r['trades']}")
            console.print()
    else:
        console.print("[yellow]No strategies met deployment threshold (Sharpe >= 1.0 with 20+ trades)[/yellow]")
        
        # Show best options
        console.print("\n[dim]Best alternatives:[/dim]")
        for r in all_results[:3]:
            console.print(f"  {r['symbol']} x {r['strategy']} ({r['timeframe']}): Sharpe {r['sharpe']}")
    
    # Save results
    df_results = pd.DataFrame(all_results)
    df_results.to_csv('data/scalping_intraday_swing_results.csv', index=False)
    console.print(f"\n[dim]Results saved to: data/scalping_intraday_swing_results.csv[/dim]")
    
    return all_results


if __name__ == "__main__":
    results = run_comprehensive_backtest()
