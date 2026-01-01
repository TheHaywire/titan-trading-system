"""
Strategy Research Dashboard
Real-time Rich terminal UI showing backtest results across all strategy/symbol combinations
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich import box
import time

console = Console()

class StrategyBacktester:
    """Quick backtest engine for multiple strategies"""
    
    def __init__(self):
        self.results = {}
        
    def backtest_momentum(self, symbol, df, lookback=252):
        """Dual Momentum strategy backtest"""
        if len(df) < lookback + 50:
            return None
            
        capital = 10000
        position = 0
        trades = []
        
        for i in range(lookback, len(df), 21):  # Monthly
            if i >= len(df):
                break
                
            momentum = (df['close'].iloc[i] / df['close'].iloc[i-lookback]) - 1
            
            if momentum > 0 and position == 0:
                position = 1
                entry_price = df['close'].iloc[i]
                entry_idx = i
                
            elif momentum <= 0 and position == 1:
                exit_price = df['close'].iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)
                position = 0
        
        if len(trades) == 0:
            return None
            
        returns = np.array(trades)
        return {
            'win_rate': np.sum(returns > 0) / len(returns),
            'avg_return': np.mean(returns),
            'sharpe': np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(12),
            'total_return': np.sum(returns),
            'trades': len(trades),
            'max_dd': np.min(returns)
        }
    
    def backtest_rsi_extremes(self, symbol, df, period=2, oversold=10, overbought=90):
        """RSI Extremes (Larry Connors) backtest"""
        if len(df) < 200:
            return None
        
        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / (loss + 0.0001)
        rsi = 100 - (100 / (1 + rs))
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(20, len(df)):
            if rsi.iloc[i] < oversold and position == 0:
                position = 1
                entry_price = df['close'].iloc[i]
            elif rsi.iloc[i] > 50 and position == 1:
                exit_price = df['close'].iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)
                position = 0
        
        if len(trades) == 0:
            return None
            
        returns = np.array(trades)
        return {
            'win_rate': np.sum(returns > 0) / len(returns),
            'avg_return': np.mean(returns),
            'sharpe': np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(252),
            'total_return': np.sum(returns),
            'trades': len(trades),
            'max_dd': np.min(returns)
        }
    
    def backtest_mean_reversion(self, symbol, df, period=20, std_mult=2.5):
        """Bollinger Band Mean Reversion"""
        if len(df) < 200:
            return None
            
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        upper = sma + std_mult * std
        lower = sma - std_mult * std
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(period + 5, len(df)):
            if df['close'].iloc[i] < lower.iloc[i] and position == 0:
                position = 1
                entry_price = df['close'].iloc[i]
            elif df['close'].iloc[i] > sma.iloc[i] and position == 1:
                exit_price = df['close'].iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)
                position = 0
        
        if len(trades) == 0:
            return None
            
        returns = np.array(trades)
        return {
            'win_rate': np.sum(returns > 0) / len(returns),
            'avg_return': np.mean(returns),
            'sharpe': np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(252),
            'total_return': np.sum(returns),
            'trades': len(trades),
            'max_dd': np.min(returns)
        }
    
    def backtest_breakout(self, symbol, df, period=55):
        """Turtle Breakout strategy"""
        if len(df) < period + 50:
            return None
        
        trades = []
        position = 0
        entry_price = 0
        
        for i in range(period, len(df)):
            high_55 = df['high'].iloc[i-period:i].max()
            low_20 = df['low'].iloc[i-20:i].min() if i > 20 else df['low'].iloc[:i].min()
            
            if df['close'].iloc[i] > high_55 and position == 0:
                position = 1
                entry_price = df['close'].iloc[i]
            elif df['close'].iloc[i] < low_20 and position == 1:
                exit_price = df['close'].iloc[i]
                pnl = (exit_price - entry_price) / entry_price
                trades.append(pnl)
                position = 0
        
        if len(trades) == 0:
            return None
            
        returns = np.array(trades)
        return {
            'win_rate': np.sum(returns > 0) / len(returns),
            'avg_return': np.mean(returns),
            'sharpe': np.mean(returns) / (np.std(returns) + 0.0001) * np.sqrt(12),
            'total_return': np.sum(returns),
            'trades': len(trades),
            'max_dd': np.min(returns)
        }

def create_results_table(results):
    """Create a rich table from backtest results"""
    table = Table(title="📊 Strategy × Symbol Matrix", box=box.ROUNDED, show_lines=True)
    
    table.add_column("Symbol", style="cyan bold", width=12)
    table.add_column("Strategy", style="magenta", width=15)
    table.add_column("Sharpe", justify="right", width=8)
    table.add_column("Win Rate", justify="right", width=10)
    table.add_column("Return", justify="right", width=10)
    table.add_column("Trades", justify="right", width=8)
    table.add_column("Status", justify="center", width=12)
    
    for key, data in sorted(results.items()):
        if data is None:
            continue
            
        symbol, strategy = key
        sharpe = data['sharpe']
        
        # Status based on Sharpe
        if sharpe >= 1.0:
            status = "[green]✅ STRONG[/green]"
        elif sharpe >= 0.5:
            status = "[yellow]⚠️ WEAK[/yellow]"
        else:
            status = "[red]❌ FAIL[/red]"
        
        # Color code Sharpe
        if sharpe >= 1.0:
            sharpe_str = f"[green]{sharpe:.2f}[/green]"
        elif sharpe >= 0.5:
            sharpe_str = f"[yellow]{sharpe:.2f}[/yellow]"
        else:
            sharpe_str = f"[red]{sharpe:.2f}[/red]"
        
        # Color code win rate
        wr = data['win_rate'] * 100
        if wr >= 60:
            wr_str = f"[green]{wr:.1f}%[/green]"
        elif wr >= 45:
            wr_str = f"[yellow]{wr:.1f}%[/yellow]"
        else:
            wr_str = f"[red]{wr:.1f}%[/red]"
        
        # Color code return
        ret = data['total_return'] * 100
        if ret > 0:
            ret_str = f"[green]+{ret:.1f}%[/green]"
        else:
            ret_str = f"[red]{ret:.1f}%[/red]"
        
        table.add_row(
            symbol,
            strategy,
            sharpe_str,
            wr_str,
            ret_str,
            str(data['trades']),
            status
        )
    
    return table

def create_ranking_table(results):
    """Create ranking of best strategies"""
    table = Table(title="🏆 Top Performing Combinations", box=box.DOUBLE_EDGE)
    
    table.add_column("Rank", style="bold", width=6)
    table.add_column("Symbol", style="cyan", width=12)
    table.add_column("Strategy", style="magenta", width=15)
    table.add_column("Sharpe", justify="right", width=10)
    table.add_column("Expectancy", justify="right", width=12)
    
    # Sort by Sharpe
    sorted_results = []
    for key, data in results.items():
        if data is not None:
            symbol, strategy = key
            sorted_results.append((symbol, strategy, data))
    
    sorted_results.sort(key=lambda x: x[2]['sharpe'], reverse=True)
    
    for i, (symbol, strategy, data) in enumerate(sorted_results[:10], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"#{i}"
        
        table.add_row(
            medal,
            symbol,
            strategy,
            f"[green bold]{data['sharpe']:.2f}[/green bold]" if data['sharpe'] >= 1.0 else f"{data['sharpe']:.2f}",
            f"${data['avg_return'] * 10000:.0f}"
        )
    
    return table

def create_summary_panel(results):
    """Create summary statistics panel"""
    total = len([r for r in results.values() if r is not None])
    profitable = len([r for r in results.values() if r is not None and r['sharpe'] >= 1.0])
    marginal = len([r for r in results.values() if r is not None and 0.5 <= r['sharpe'] < 1.0])
    failed = len([r for r in results.values() if r is not None and r['sharpe'] < 0.5])
    
    avg_sharpe = np.mean([r['sharpe'] for r in results.values() if r is not None])
    avg_winrate = np.mean([r['win_rate'] for r in results.values() if r is not None])
    
    text = Text()
    text.append("Strategy Research Summary\n\n", style="bold underline")
    text.append(f"Total Combinations Tested: ", style="dim")
    text.append(f"{total}\n", style="bold")
    text.append(f"✅ Strong Edge (Sharpe ≥1.0): ", style="green")
    text.append(f"{profitable}\n", style="green bold")
    text.append(f"⚠️ Weak Edge (Sharpe 0.5-1.0): ", style="yellow")
    text.append(f"{marginal}\n", style="yellow bold")
    text.append(f"❌ No Edge (Sharpe <0.5): ", style="red")
    text.append(f"{failed}\n\n", style="red bold")
    text.append(f"Average Sharpe: {avg_sharpe:.2f}\n", style="dim")
    text.append(f"Average Win Rate: {avg_winrate:.1%}\n", style="dim")
    
    return Panel(text, title="📈 Overview", border_style="blue")

def run_dashboard():
    """Main dashboard function"""
    
    console.clear()
    console.print(Panel.fit(
        "[bold cyan]🔬 TITAN STRATEGY RESEARCH DASHBOARD[/bold cyan]\n"
        "[dim]Real-time backtesting across strategies × symbols[/dim]",
        border_style="cyan"
    ))
    
    if not mt5.initialize():
        console.print("[red]❌ MT5 initialization failed[/red]")
        return
    
    # Define test universe
    symbols = [
        ("BTCUSD", "Crypto"),
        ("ETHUSD", "Crypto"),
        ("GOLD", "Commodity"),
        ("EURUSD", "Forex"),
        ("GBPUSD", "Forex"),
        ("USDJPY", "Forex"),
        ("US500Cash", "Index"),
        ("NAS100", "Index"),
        ("GER40", "Index"),
    ]
    
    strategies = [
        ("Momentum", "backtest_momentum"),
        ("RSI Extremes", "backtest_rsi_extremes"),
        ("Mean Reversion", "backtest_mean_reversion"),
        ("Breakout", "backtest_breakout"),
    ]
    
    bt = StrategyBacktester()
    results = {}
    
    # Run backtests with progress
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        
        total_tests = len(symbols) * len(strategies)
        task = progress.add_task("Running backtests...", total=total_tests)
        
        for symbol, category in symbols:
            # Fetch data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 2000)
            
            if rates is None or len(rates) < 300:
                for strat_name, _ in strategies:
                    results[(symbol, strat_name)] = None
                    progress.update(task, advance=1)
                continue
            
            df = pd.DataFrame(rates)
            
            for strat_name, method_name in strategies:
                progress.update(task, description=f"Testing {symbol} × {strat_name}...")
                
                method = getattr(bt, method_name)
                result = method(symbol, df)
                
                results[(symbol, strat_name)] = result
                progress.update(task, advance=1)
                time.sleep(0.1)  # Visual effect
    
    console.print()
    
    # Display results
    console.print(create_summary_panel(results))
    console.print()
    console.print(create_results_table(results))
    console.print()
    console.print(create_ranking_table(results))
    
    # Show recommendation
    console.print()
    best_combos = [(k, v) for k, v in results.items() if v is not None and v['sharpe'] >= 1.0]
    
    if best_combos:
        console.print(Panel(
            "[bold green]🎯 RECOMMENDED FOR DEPLOYMENT[/bold green]\n\n" +
            "\n".join([f"  • {k[0]} × {k[1]} (Sharpe: {v['sharpe']:.2f})" for k, v in sorted(best_combos, key=lambda x: x[1]['sharpe'], reverse=True)[:5]]),
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[yellow]⚠️ No combinations met Sharpe ≥1.0 threshold[/yellow]\n"
            "Consider: Optimizing parameters or testing on different symbols",
            border_style="yellow"
        ))
    
    mt5.shutdown()
    
    # Export results to files
    export_results(results)
    
    return results

def export_results(results):
    """Export results to CSV and HTML files"""
    
    # Create export data
    export_data = []
    for key, data in results.items():
        if data is not None:
            symbol, strategy = key
            export_data.append({
                'Symbol': symbol,
                'Strategy': strategy,
                'Sharpe': round(data['sharpe'], 2),
                'Win_Rate': f"{data['win_rate']*100:.1f}%",
                'Total_Return': f"{data['total_return']*100:.1f}%",
                'Trades': data['trades'],
                'Avg_Return': f"{data['avg_return']*100:.2f}%",
                'Status': 'STRONG' if data['sharpe'] >= 1.0 else 'WEAK' if data['sharpe'] >= 0.5 else 'FAIL'
            })
    
    if export_data:
        df = pd.DataFrame(export_data)
        df = df.sort_values('Sharpe', ascending=False)
        
        # Save to CSV
        csv_path = 'data/backtest_results.csv'
        df.to_csv(csv_path, index=False)
        console.print(f"\n[dim]Results exported to: {csv_path}[/dim]")
        
        # Print summary to console
        console.print("\n[bold]Export Preview (Top 10):[/bold]")
        print(df.head(10).to_string())

if __name__ == "__main__":
    run_dashboard()
