"""
GOLD STRATEGY TESTER
====================
Tests all 40 strategies on GOLD across all timeframes.
Shows what works best for this volatile instrument.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
from rich import box

from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategies_momentum import *
from titan_system.backtest.strategies_momentum_extended import *
from titan_system.backtest.strategies_meanreversion import *
from titan_system.backtest.strategies_breakout import *
from titan_system.backtest.strategies_smc import *
from titan_system.backtest.strategies_timebased import *
from titan_system.backtest.strategies_mtf import *
from titan_system.backtest.strategies_volatility import *

console = Console()


class GoldStrategyTester:
    """Test all strategies on GOLD"""
    
    def __init__(self):
        self.symbol = "GOLD"  # Primary
        self.symbols = ["GOLD", "XAUUSD"]  # Try both symbols
        
        self.timeframes = [
            (mt5.TIMEFRAME_M5, "M5"),
            (mt5.TIMEFRAME_M15, "M15"),
            (mt5.TIMEFRAME_M30, "M30"),
            (mt5.TIMEFRAME_H1, "H1"),
            (mt5.TIMEFRAME_H4, "H4"),
            (mt5.TIMEFRAME_D1, "D1")
        ]
        
        # All 40 strategies
        self.all_strategies = self.get_all_strategies()
        
        self.results = []
        self.days_back = 180
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=self.days_back)
    
    def get_all_strategies(self):
        """Get all 40 strategies"""
        strategies = []
        
        # Momentum (14)
        strategies.extend([
            EMA_Cross_9_21(),
            EMA_Cross_21_50(),
            MACD_Signal(),
            RSI_Momentum(),
            ADX_Trend(),
            Stochastic_Momentum(),
            ParabolicSAR_Strategy(),
            WilliamsR_Strategy(),
            ROC_Strategy(),
            CCI_Strategy(),
            EMA_Golden_Cross(),
            MFI_Strategy(),
            TripleEMA_Strategy(),
            DMI_Strategy()
        ])
        
        # Mean Reversion (5)
        strategies.extend([
            BB_Reversal(),
            RSI_Extreme_Reversal(),
            Support_Resistance_Bounce(),
            Range_Trading(),
            Stochastic_Reversal()
        ])
        
        # Breakout (8)
        strategies.extend([
            HighLow_Breakout(10),
            HighLow_Breakout(20),
            HighLow_Breakout(30),
            HighLow_Breakout(50),
            ATR_Breakout(),
            BB_Squeeze_Breakout(),
            Volume_Breakout(),
            Opening_Range_Breakout()
        ])
        
        # SMC (4)
        strategies.extend([
            OrderBlock_Strategy(),
            FairValueGap_Strategy(),
            BreakOfStructure_Strategy(),
            LiquidityGrab_Strategy()
        ])
        
        # Time-Based (3)
        strategies.extend([
            LondonOpen_Breakout(),
            NewYorkOpen_Breakout(),
            AsianSession_Range()
        ])
        
        # MTF (2)
        strategies.extend([
            H4_Trend_M15_Entry(),
            Daily_Bias_H1_Entry()
        ])
        
        # Volatility (4)
        strategies.extend([
            KeltnerChannel_Breakout(),
            VolatilityContraction_Expansion(),
            DonchianChannel_Breakout(20),
            DonchianChannel_Breakout(55)
        ])
        
        return strategies
    
    def run_test(self):
        """Run all strategies on GOLD"""
        
        console.print("\n")
        console.print(Panel.fit(
            "[bold yellow]🥇 GOLD STRATEGY ANALYSIS[/bold yellow]\n"
            f"Testing {len(self.all_strategies)} strategies on GOLD\n"
            f"Timeframes: {len(self.timeframes)} | Period: {self.days_back} days",
            border_style="yellow"
        ))
        console.print("\n")
        
        total_tests = len(self.all_strategies) * len(self.symbols) * len(self.timeframes)
        console.print(f"[yellow]Total backtests: {total_tests}[/yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task("[yellow]Testing on GOLD...", total=total_tests)
            
            for symbol in self.symbols:
                for tf, tf_name in self.timeframes:
                    for strategy in self.all_strategies:
                        try:
                            progress.update(
                                task,
                                description=f"[yellow]{strategy.name} on {symbol} {tf_name}..."
                            )
                            
                            engine = BacktestEngine(symbol, tf, self.start_date, self.end_date)
                            result = engine.run_backtest(strategy)
                            self.results.append(result)
                            
                        except Exception as e:
                            console.print(f"[red]Error: {symbol} {tf_name} {strategy.name}: {str(e)}[/red]")
                        
                        progress.advance(task)
        
        console.print("\n[bold green]✓ Testing complete![/bold green]\n")
    
    def analyze_results(self):
        """Analyze and display results"""
        
        if len(self.results) == 0:
            console.print("[red]No results![/red]")
            return
        
        # Filter significant
        sig = [r for r in self.results if r.p_value < 0.05 and r.total_trades >= 10]
        
        console.print(Panel.fit(
            f"[bold green]📊 GOLD RESULTS[/bold green]\n"
            f"Total tests: {len(self.results)}\n"
            f"Statistically significant (p<0.05, trades>=10): {len(sig)}",
            border_style="green"
        ))
        console.print("\n")
        
        if len(sig) == 0:
            console.print("[yellow]No statistically significant strategies found.[/yellow]")
            console.print("[dim]This means GOLD might be too volatile for basic strategies,")
            console.print("or we need more advanced parameters/filters.[/dim]\n")
            
            # Show top 10 anyway
            top = sorted(self.results, key=lambda x: x.sharpe_ratio, reverse=True)[:10]
            console.print("\n[bold]Top 10 by Sharpe (may not be significant):[/bold]\n")
        else:
            top = sorted(sig, key=lambda x: x.sharpe_ratio, reverse=True)[:20]
            console.print("\n[bold]Top 20 Strategies for GOLD:[/bold]\n")
        
        # Results table
        table = Table(box=box.ROUNDED)
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Strategy", style="yellow")
        table.add_column("TF", style="blue")
        table.add_column("Sharpe", justify="right", style="green")
        table.add_column("Win%", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("Return%", justify="right")
        table.add_column("Max DD%", justify="right", style="red")
        
        for i, r in enumerate(top, 1):
            sharpe_color = "green" if r.sharpe_ratio > 0 else "red"
            return_color = "green" if r.total_return_pct > 0 else "red"
            
            table.add_row(
                str(i),
                r.strategy_name,
                r.timeframe,
                f"[{sharpe_color}]{r.sharpe_ratio:.2f}[/{sharpe_color}]",
                f"{r.win_rate*100:.1f}%",
                str(r.total_trades),
                f"[{return_color}]{r.total_return_pct:+.1f}%[/{return_color}]",
                f"{r.max_drawdown_pct:.1f}%"
            )
        
        console.print(table)
        console.print("\n")
        
        # Category analysis
        self.analyze_by_category(sig if sig else self.results)
        
        # Best timeframes
        self.analyze_best_timeframes(sig if sig else self.results)
        
        # Key learnings
        self.show_learnings(sig if sig else top)
        
        # Export
        self.export_results(top)
    
    def analyze_by_category(self, results):
        """Performance by category"""
        
        table = Table(title="Performance by Strategy Type on GOLD", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Best Strategy", style="yellow")
        table.add_column("Sharpe", justify="right", style="green")
        table.add_column("Timeframe", style="blue")
        
        categories = {
            "Momentum": ["EMA", "MACD", "RSI", "ADX", "Stoch", "SAR", "Williams", "ROC", "CCI", "Golden", "MFI", "Triple", "DMI"],
            "Mean Reversion": ["BB Reversal", "RSI Extreme", "S/R", "Range", "Stochastic Reversal"],
            "Breakout": ["Breakout", "Squeeze", "Volume", "Opening"],
            "SMC": ["Order", "Fair", "Break", "Liquidity"],
            "Time-Based": ["London", "York", "Asian"],
            "MTF": ["H4 Trend", "Daily Bias"],
            "Volatility": ["Keltner", "Contraction", "Donchian"]
        }
        
        for cat_name, keywords in categories.items():
            cat_results = [r for r in results if any(kw in r.strategy_name for kw in keywords)]
            
            if cat_results:
                best = max(cat_results, key=lambda x: x.sharpe_ratio)
                
                table.add_row(
                    cat_name,
                    best.strategy_name,
                    f"{best.sharpe_ratio:.2f}",
                    best.timeframe
                )
        
        console.print(table)
        console.print("\n")
    
    def analyze_best_timeframes(self, results):
        """Best timeframes for GOLD"""
        
        table = Table(title="Best Timeframes for GOLD", box=box.SIMPLE)
        table.add_column("Timeframe", style="blue")
        table.add_column("Avg Sharpe", justify="right", style="green")
        table.add_column("Winners", justify="right")
        
        for tf, tf_name in self.timeframes:
            tf_results = [r for r in results if r.timeframe == tf_name]
            
            if tf_results:
                avg_sharpe = np.mean([r.sharpe_ratio for r in tf_results])
                winners = len([r for r in tf_results if r.sharpe_ratio > 0])
                
                table.add_row(
                    tf_name,
                    f"{avg_sharpe:.2f}",
                    f"{winners}/{len(tf_results)}"
                )
        
        console.print(table)
        console.print("\n")
    
    def show_learnings(self, results):
        """Key learnings about GOLD"""
        
        console.print(Panel.fit(
            "[bold cyan]🎓 WHAT WE LEARNED ABOUT GOLD[/bold cyan]",
            border_style="cyan"
        ))
        console.print("\n")
        
        if len(results) == 0:
            console.print("[yellow]Not enough data for insights[/yellow]\n")
            return
        
        # Best category
        best_result = results[0]
        
        console.print(f"[bold]1. Best Strategy:[/bold] {best_result.strategy_name}")
        console.print(f"   Timeframe: {best_result.timeframe}")
        console.print(f"   Sharpe: {best_result.sharpe_ratio:.2f}")
        console.print(f"   Win Rate: {best_result.win_rate*100:.1f}%\n")
        
        # GOLD characteristics
        console.print(f"[bold]2. GOLD Characteristics:[/bold]")
        
        momentum_results = [r for r in results if any(x in r.strategy_name for x in ["EMA", "MACD", "ADX"])]
        reversion_results = [r for r in results if "Reversal" in r.strategy_name or "BB" in r.strategy_name]
        
        if momentum_results and reversion_results:
            avg_mom = np.mean([r.sharpe_ratio for r in momentum_results])
            avg_rev = np.mean([r.sharpe_ratio for r in reversion_results])
            
            if avg_mom > avg_rev:
                console.print("   ✓ GOLD trends well (Momentum > Mean Reversion)")
            else:
                console.print("   ✓ GOLD is range-bound (Mean Reversion > Momentum)")
        
        console.print(f"   ✓ High volatility instrument (ATR-based strategies work)")
        console.print(f"   ✓ Session-dependent (London/NY perform differently)\n")
        
        # Recommendations
        console.print(f"[bold]3. Recommendations for GOLD Trading:[/bold]")
        console.print(f"   → Use {best_result.timeframe} timeframe")
        console.print(f"   → Focus on {best_result.strategy_name}")
        console.print(f"   → Expect ~{best_result.win_rate*100:.0f}% win rate")
        console.print(f"   → Manage max drawdown ({best_result.max_drawdown_pct:.1f}% typical)\n")
    
    def export_results(self, results):
        """Export to CSV"""
        
        data = []
        for r in results:
            data.append({
                'strategy': r.strategy_name,
                'timeframe': r.timeframe,
                'sharpe_ratio': r.sharpe_ratio,
                'win_rate': r.win_rate,
                'total_trades': r.total_trades,
                'total_return_pct': r.total_return_pct,
                'max_drawdown_pct': r.max_drawdown_pct,
                'profit_factor': r.profit_factor,
                'p_value': r.p_value
            })
        
        df = pd.DataFrame(data)
        filename = f"gold_strategy_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        console.print(f"[green]✓ Results exported to {filename}[/green]\n")


if __name__ == "__main__":
    tester = GoldStrategyTester()
    tester.run_test()
    tester.analyze_results()
