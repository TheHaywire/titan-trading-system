"""
TITAN MEGA-VECTORBT BACKTESTER
==============================
Vectorized multi-strategy backtesting across 1,500+ symbols.
Optimized for MT5 history retrieval and high-concurrency analysis.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import vectorbt as vbt
from datetime import datetime, timedelta
import logging
import os
import concurrent.futures
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn, MofNCompleteColumn

# Setup
console = Console()
logging.getLogger("vectorbt").setLevel(logging.ERROR)

class MegaBacktester:
    def __init__(self, timeframe=mt5.TIMEFRAME_M15, bars=5000):
        self.timeframe = timeframe
        self.bars = bars
        self.results = []
        self.data_cache = {}

    def fetch_data(self, symbol):
        """Fetch historical data from MT5."""
        try:
            rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, self.bars)
            if rates is None or len(rates) < 200:
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            return df
        except Exception:
            return None

    def backtest_orb(self, symbol, df):
        """Vectorized ORB Backtest."""
        try:
            close = df['close']
            high = df['high']
            low = df['low']
            
            # Identify first bar of each day (Simplistic ORB for vectorization)
            is_new_day = df.index.date != np.roll(df.index.date, 1)
            is_new_day[0] = True # First bar
            
            # Get daily high/low of first bar
            orb_high = high.where(is_new_day).ffill()
            orb_low = low.where(is_new_day).ffill()
            
            # Signals: Breakout of first bar
            entries = close > orb_high
            exits = close < orb_low
            
            pf = vbt.Portfolio.from_signals(
                close, entries, exits, 
                fees=0.001, slippage=0.001, freq='15min',
                init_cash=10000
            )
            return self.extract_metrics(pf, symbol, "ORB")
        except Exception:
            return None

    def backtest_mean_reversion(self, symbol, df):
        """Vectorized Mean Reversion (Bollinger) Backtest."""
        try:
            close = df['close']
            sma = close.rolling(20).mean()
            std = close.rolling(20).std()
            lower = sma - 2.5 * std
            upper = sma + 2.5 * std
            
            entries = (close < lower)
            exits = (close > sma)
            
            pf = vbt.Portfolio.from_signals(
                close, entries, exits, 
                fees=0.001, slippage=0.001, freq='15min',
                init_cash=10000
            )
            return self.extract_metrics(pf, symbol, "MeanReversion")
        except Exception:
            return None

    def extract_metrics(self, pf, symbol, strategy):
        """Extract key metrics from vectorbt portfolio."""
        sharpe = pf.sharpe_ratio()
        if np.isnan(sharpe) or pf.trades.count() < 5:
            return None
            
        # Calculate Average Hold Time in HOURS (M15 bars)
        avg_bars = pf.trades.duration.mean()
        avg_hold_hours = (avg_bars * 15) / 60 if not np.isnan(avg_bars) else 0
        
        # Calculate Velocity (Return % per Hour held)
        total_return = pf.total_return() * 100
        velocity = total_return / avg_hold_hours if avg_hold_hours > 0 else 0

        return {
            "Symbol": symbol,
            "Strategy": strategy,
            "Trades": pf.trades.count(),
            "WinRate": f"{pf.trades.win_rate()*100:.1f}%",
            "Return": f"{total_return:.1f}%",
            "MaxDD": f"{pf.max_drawdown()*100:.1f}%",
            "Sharpe": round(sharpe, 2),
            "Hold (Hrs)": round(avg_hold_hours, 1),
            "Velocity": round(velocity, 3)
        }

    def run_mega_audit(self, limit=100):
        if not mt5.initialize():
            console.print("[red]MT5 Init Failed[/red]")
            return

        symbols = [s.name for s in mt5.symbols_get() if s.visible or "USD" in s.name or "GOLD" in s.name]
        symbols = symbols[:limit] # Start with a limit for the demo

        console.print(f"🚀 Starting Mega-Audit on {len(symbols)} symbols...")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Auditing Universe...", total=len(symbols))
            
            for symbol in symbols:
                df = self.fetch_data(symbol)
                if df is not None:
                    # Run Strategies
                    orb_res = self.backtest_orb(symbol, df)
                    mr_res = self.backtest_mean_reversion(symbol, df)
                    
                    if orb_res: self.results.append(orb_res)
                    if mr_res: self.results.append(mr_res)
                
                progress.update(task, advance=1)

        mt5.shutdown()
        self.report()

    def report(self):
        if not self.results:
            console.print("[yellow]No profitable strategies found in audit.[/yellow]")
            return

        df_res = pd.DataFrame(self.results).sort_values("Velocity", ascending=False)
        
        table = Table(title="🏆 TITAN MEGA-BACKTEST HALL OF FAME", border_style="green")
        for col in df_res.columns:
            table.add_column(col)
        
        for _, row in df_res.head(20).iterrows():
            table.add_row(*[str(v) for v in row.values])
        
        console.print(table)
        
        # Save to markdown
        df_res.to_markdown("MEGA_ALPHA_REPORT.md", index=False)
        console.print(f"\n✅ Full report saved to [bold]MEGA_ALPHA_REPORT.md[/bold]")

if __name__ == "__main__":
    tester = MegaBacktester(bars=2000) # Last ~20 days of M15
    tester.run_mega_audit(limit=200) # Audit top 200 first
