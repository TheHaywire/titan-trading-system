"""
🌍 GLOBAL ALPHA SCANNER (v3.0)
==============================
High-throughput vectorized backtesting for 1,500+ symbols.
Categorizes assets into families and identifies "Triple-A" Alphas.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import vectorbt as vbt
import logging
import os
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn

# Setup
console = Console()
logging.getLogger("vectorbt").setLevel(logging.ERROR)

class GlobalAlphaScanner:
    def __init__(self, timeframes=[mt5.TIMEFRAME_D1, mt5.TIMEFRAME_H4], bars=1000):
        self.timeframes = timeframes
        self.bars = bars
        self.results = []
        
    def get_asset_family(self, path):
        """Categorize symbols based on MT5 path."""
        p = path.lower()
        if "forex" in p: return "Forex"
        if "crypto" in p: return "Crypto"
        if "stock" in p: return "Stocks"
        if "index" in p or "indices" in p: return "Indices"
        if "commodity" in p or "metals" in p: return "Commodities"
        return "Others"

    def fetch_data(self, symbol, tf):
        """Fetch historical data."""
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, self.bars)
            if rates is None or len(rates) < 100:
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        except Exception:
            return None

    def run_backtests(self, symbol, family, tf_name, df):
        """Run a suite of vectorized strategies."""
        close = df['close']
        
        # 1. Trend Following (SMA Cross)
        sma_fast = close.rolling(20).mean()
        sma_slow = close.rolling(50).mean()
        entries_trend = (sma_fast > sma_slow) & (sma_fast.shift(1) <= sma_slow.shift(1))
        exits_trend = (sma_fast < sma_slow) & (sma_fast.shift(1) >= sma_slow.shift(1))
        self.evaluate(symbol, family, tf_name, "TrendFollowing", close, entries_trend, exits_trend)

        # 2. Mean Reversion (Bollinger)
        sma = close.rolling(20).mean()
        std = close.rolling(20).std()
        lower = sma - 2.5 * std
        upper = sma + 2.5 * std
        entries_mr = (close < lower)
        exits_mr = (close > sma)
        self.evaluate(symbol, family, tf_name, "MeanReversion", close, entries_mr, exits_mr)

        # 3. Volatility Breakout (Donchian/ATR)
        high10 = df['high'].rolling(10).max().shift(1)
        low10 = df['low'].rolling(10).min().shift(1)
        entries_vb = (close > high10)
        exits_vb = (close < low10)
        self.evaluate(symbol, family, tf_name, "VolBreakout", close, entries_vb, exits_vb)

    def evaluate(self, symbol, family, tf, strategy, close, entries, exits):
        """Extract portfolio metrics."""
        try:
            pf = vbt.Portfolio.from_signals(
                close, entries, exits, 
                fees=0.0005, slippage=0.0005, 
                init_cash=10000, freq='D' if "D1" in tf else '4H'
            )
            sharpe = pf.sharpe_ratio()
            if not np.isnan(sharpe) and sharpe > 1.0 and pf.trades.count() >= 10:
                self.results.append({
                    "Symbol": symbol,
                    "Family": family,
                    "TF": tf,
                    "Strategy": strategy,
                    "Trades": pf.trades.count(),
                    "WinRate": f"{pf.trades.win_rate()*100:.1f}%",
                    "Return": f"{pf.total_return()*100:.1f}%",
                    "MaxDD": f"{pf.max_drawdown()*100:.1f}%",
                    "Sharpe": round(sharpe, 2)
                })
        except Exception:
            pass

    def run_all(self, limit=None):
        if not mt5.initialize():
            console.print("[red]MT5 Init Failed[/red]")
            return

        all_symbols = mt5.symbols_get()
        if limit:
            all_symbols = all_symbols[:limit]
            
        console.print(f"🚀 Scanning {len(all_symbols)} symbols across {len(self.timeframes)} timeframes...")

        tf_map = {mt5.TIMEFRAME_D1: "D1", mt5.TIMEFRAME_H4: "H4"}

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Global Audit...", total=len(all_symbols))
            
            for s in all_symbols:
                family = self.get_asset_family(s.path)
                for tf in self.timeframes:
                    df = self.fetch_data(s.name, tf)
                    if df is not None:
                        self.run_backtests(s.name, family, tf_map[tf], df)
                
                # Incremental Save every 10 symbols
                if progress.tasks[task].completed % 10 == 0 and self.results:
                    pd.DataFrame(self.results).to_csv("data/global_alpha_results.csv", index=False)
                    
                progress.update(task, advance=1)

        self.report()
        mt5.shutdown()

    def report(self):
        if not self.results:
            console.print("[yellow]No 'Triple-A' Alphas found.[/yellow]")
            return

        df_res = pd.DataFrame(self.results).sort_values("Sharpe", ascending=False)
        
        # Save results
        df_res.to_csv("data/global_alpha_results.csv", index=False)
        df_res.to_markdown("GLOBAL_ALPHA_REPORT.md", index=False)
        
        table = Table(title="🏆 GLOBAL ALPHA HALL OF FAME", border_style="bold green")
        for col in df_res.columns:
            table.add_column(col)
        
        for _, row in df_res.head(25).iterrows():
            table.add_row(*[str(v) for v in row.values])
        
        console.print(table)
        console.print(f"\n✅ Found {len(df_res)} Validated Alphas.")
        console.print(f"📂 Reports saved: [bold]data/global_alpha_results.csv[/bold], [bold]GLOBAL_ALPHA_REPORT.md[/bold]")

if __name__ == "__main__":
    # Ensure data dir exists
    os.makedirs("data", exist_ok=True)
    
    scanner = GlobalAlphaScanner(bars=1000)
    # Target top 300 symbols for a comprehensive but efficient initial run
    scanner.run_all(limit=300)
