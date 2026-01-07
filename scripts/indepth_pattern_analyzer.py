import os
import sys
import numpy as np
import pandas as pd
import polars as pl
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import track
import MetaTrader5 as mt5

# Path Hack
sys.path.append(os.path.join(os.getcwd()))

from titan_system.ai.features import compute_features
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategy_base import BaseStrategy

console = Console()

class IndepthAnalyzer:
    def __init__(self, symbol="GOLD"):
        self.symbol = symbol
        self.results = {}

    def fetch_data(self, timeframe, days=730):
        if not mt5.initialize():
            return None
        utc_from = datetime.now() - timedelta(days=days)
        rates = mt5.copy_rates_range(self.symbol, timeframe, utc_from, datetime.now())
        mt5.shutdown()
        if rates is None:
            return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def feature_audit(self):
        """Calculate Information Coefficient of AI features"""
        console.print(f"\n[bold cyan]🧠 AUDITING AI FEATURES FOR {self.symbol}[/bold cyan]")
        
        df_pd = self.fetch_data(mt5.TIMEFRAME_H1)
        if df_pd is None: return
        
        df_pl = pl.from_pandas(df_pd)
        df_clean, matrix = compute_features(df_pl)
        
        # Calculate forward returns (next 5 bars)
        df_clean = df_clean.with_columns([
            (pl.col("close").shift(-5) / pl.col("close") - 1).alias("fwd_return")
        ]).drop_nulls()
        
        feature_cols = [c for c in df_clean.columns if c.startswith("f_")]
        
        table = Table(title="Feature Robustness (Information Coefficient)")
        table.add_column("Feature", style="cyan")
        table.add_column("IC (Correlation)", justify="right")
        table.add_column("Rank", justify="center")

        ic_results = []
        for col in feature_cols:
            corr = np.corrcoef(df_clean[col].to_numpy(), df_clean["fwd_return"].to_numpy())[0, 1]
            ic_results.append((col, corr))
            
        ic_results.sort(key=lambda x: abs(x[1]), reverse=True)
        for i, (col, ic) in enumerate(ic_results):
            style = "green" if abs(ic) > 0.05 else "white"
            table.add_row(col, f"[{style}]{ic:.4f}[/{style}]", str(i+1))
            
        console.print(table)

    def regime_profiling(self, strategy_class):
        """Analyze strategy performance across volatility regimes"""
        strategy = strategy_class()
        console.print(f"\n[bold yellow]📈 REGIME PROFILING: {strategy.name}[/bold yellow]")
        
        engine = BacktestEngine(self.symbol, mt5.TIMEFRAME_H4, datetime.now() - timedelta(days=730), datetime.now())
        result = engine.run_backtest(strategy)
        
        if not result.trades:
            console.print("[red]No trades found for regime analysis[/red]")
            return

        # Prepare Regime Data
        df = engine.data.copy()
        df['atr_norm'] = df['high'] - df['low']
        df['vol_regime'] = pd.qcut(df['atr_norm'], 3, labels=['Low', 'Medium', 'High'])
        
        regime_results = []
        for regime in ['Low', 'Medium', 'High']:
            trades_in_regime = []
            for trade in result.trades:
                # Find regime at trade entry
                match = df[df['time'] == trade.entry_time]
                if not match.empty:
                    if match.iloc[0]['vol_regime'] == regime:
                        trades_in_regime.append(trade.profit)
            
            if trades_in_regime:
                win_rate = len([p for p in trades_in_regime if p > 0]) / len(trades_in_regime)
                avg_profit = np.mean(trades_in_regime)
                regime_results.append({
                    'Regime': regime,
                    'Trades': len(trades_in_regime),
                    'WinRate': win_rate * 100,
                    'AvgProfit': avg_profit
                })

        table = Table(title=f"Regime Sensitivity: {strategy.name}")
        table.add_column("Regime")
        table.add_column("Trades", justify="right")
        table.add_column("Win Rate", justify="right")
        table.add_column("Avg P&L", justify="right")

        for res in regime_results:
            table.add_row(
                res['Regime'], 
                str(res['Trades']), 
                f"{res['WinRate']:.1f}%", 
                f"{res['AvgProfit']:.2f}"
            )
        console.print(table)

    def monte_carlo_verification(self, strategy_class, iterations=1000):
        """Run Monte Carlo simulations by shuffling trade order"""
        strategy = strategy_class()
        console.print(f"\n[bold magenta]🎲 MONTE CARLO VERIFICATION: {strategy.name}[/bold magenta]")
        
        engine = BacktestEngine(self.symbol, mt5.TIMEFRAME_H1, datetime.now() - timedelta(days=730), datetime.now())
        result = engine.run_backtest(strategy)
        
        if not result.trades:
            return
            
        profits = [t.profit for t in result.trades]
        final_returns = []
        
        for _ in range(iterations):
            shuffled = np.random.choice(profits, size=len(profits), replace=True)
            final_returns.append(np.sum(shuffled))
            
        prob_positive = len([r for r in final_returns if r > 0]) / iterations
        
        console.print(f"Original Profit: {np.sum(profits):.2f}")
        console.print(f"Probability of Positive Return: [bold]{prob_positive*100:.1f}%[/bold]")
        
        if prob_positive < 0.6:
            console.print("[red]WARNING: High probability of luck-based performance![/red]")
        else:
            console.print("[green]CONFIRMED: Strategy shows statistical robustness.[/green]")

    def cross_symbol_validation(self, strategy_class, other_symbol="SILVER"):
        """Verify if Gold pattern works on Silver too"""
        strategy = strategy_class()
        console.print(f"\n[bold blue]🔗 CROSS-SYMBOL VALIDATION: {strategy.name} on {other_symbol}[/bold blue]")
        
        try:
            engine = BacktestEngine(other_symbol, mt5.TIMEFRAME_H1, datetime.now() - timedelta(days=365), datetime.now())
            result = engine.run_backtest(strategy)
            
            style = "green" if result.sharpe_ratio > 0.5 else "yellow"
            console.print(f"Result on {other_symbol}: Sharpe [{style}]{result.sharpe_ratio:.2f}[/{style}] | Trades: {result.total_trades}")
        except Exception as e:
            console.print(f"[dim]Failed to run on {other_symbol}: {str(e)}[/dim]")

    def verify_high_sharpe(self, strategy_name, tf_str="D1"):
        """Deep audit of outliers (e.g. Sharpe 147)"""
        console.print(f"\n[bold magenta]🔍 AUDITING OUTLIER: {strategy_name} ({tf_str})[/bold magenta]")
        
        # Load existing results
        try:
            results_df = pd.read_csv('gold_multi_timeframe_results.csv')
            match = results_df[(results_df['strategy'] == strategy_name) & (results_df['timeframe'] == tf_str)]
            if match.empty:
                console.print(f"[red]Strategy {strategy_name} not found in results[/red]")
                return
            
            orig_sharpe = match.iloc[0]['sharpe']
            trades_count = match.iloc[0]['trades']
            
            console.print(f"Original Result: Sharpe {orig_sharpe:.2f} | Trades: {trades_count}")
            
            if trades_count < 10:
                console.print(f"[yellow]CAUTION:[/yellow] Sample size too small for statistical significance.")
            
            if orig_sharpe > 20:
                console.print(f"[red]WARNING:[/red] Sharpe > 20 is likely a backtest artifact (lookahead or zero-variance).")
                
        except:
            console.print("[dim]Note: Could not load existing CSV. Running fresh audit...[/dim]")

    def run_all(self):
        self.feature_audit()
        
        # Profile top strategies if they exist
        from titan_system.backtest.strategies_patterns import DojiReversal_Strategy
        self.regime_profiling(DojiReversal_Strategy)
        self.monte_carlo_verification(DojiReversal_Strategy)
        self.cross_symbol_validation(DojiReversal_Strategy, "SILVER")
        
        self.verify_high_sharpe("Hidden Divergence", "D1")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GOLD")
    args = parser.parse_args()
    
    analyzer = IndepthAnalyzer(args.symbol)
    analyzer.run_all()
