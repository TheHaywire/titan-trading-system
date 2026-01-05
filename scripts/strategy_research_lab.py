"""
STRATEGY RESEARCH LAB - MASTER TESTER
======================================
Tests 1000s of strategy combinations and generates comprehensive reports.
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
from titan_system.backtest.strategies_meanreversion import *
from titan_system.backtest.strategies_breakout import *
from titan_system.backtest.strategies_smc import *
from titan_system.backtest.strategies_timebased import *
from titan_system.backtest.strategies_mtf import *
from titan_system.backtest.strategies_volatility import *

console = Console()


class StrategyResearchLab:
    """
    Comprehensive strategy testing framework.
    Tests 1000s of strategies across symbols and timeframes.
    """
    
    def __init__(self):
        # Test configuration - EXPANDED FOR 1000+ TESTS
        self.symbols = [
            # Forex Major Pairs
            "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
            "USDCHF", "NZDUSD", "EURJPY", "GBPJPY", "EURGBP",
            # Metals
            "GOLD", "XAUUSD", "SILVER",
            # Indices
            "US100", "US30", "GER40", "UK100", "JPN225",
            # Crypto
            "BTCUSD", "ETHUSD"
        ]
        
        self.timeframes = [
            (mt5.TIMEFRAME_M1, "M1"),
            (mt5.TIMEFRAME_M5, "M5"),
            (mt5.TIMEFRAME_M15, "M15"),
            (mt5.TIMEFRAME_M30, "M30"),
            (mt5.TIMEFRAME_H1, "H1"),
            (mt5.TIMEFRAME_H4, "H4"),
            (mt5.TIMEFRAME_D1, "D1")
        ]
        
        # Initialize strategies with PARAMETER VARIATIONS
        self.momentum_strategies = [
            # EMA variations
            EMA_Cross_9_21(),
            EMA_Cross_21_50(),
            
            MACD_Signal(),
            RSI_Momentum(),
            ADX_Trend(),
            Stochastic_Momentum()
        ]
        
        self.meanreversion_strategies = [
            BB_Reversal(),
            RSI_Extreme_Reversal(),
            Support_Resistance_Bounce(),
            Range_Trading(),
            Stochastic_Reversal()
        ]
        
        self.breakout_strategies = [
            # Multiple period variations
            HighLow_Breakout(10),
            HighLow_Breakout(20),
            HighLow_Breakout(30),
            HighLow_Breakout(50),
            
            ATR_Breakout(),
            BB_Squeeze_Breakout(),
            Volume_Breakout(),
            Opening_Range_Breakout()
        ]
        
        # NEW CATEGORIES
        self.smc_strategies = [
            OrderBlock_Strategy(),
            FairValueGap_Strategy(),
            BreakOfStructure_Strategy(),
            LiquidityGrab_Strategy()
        ]
        
        self.timebased_strategies = [
            LondonOpen_Breakout(),
            NewYorkOpen_Breakout(),
            AsianSession_Range()
        ]
        
        self.mtf_strategies = [
            H4_Trend_M15_Entry(),
            Daily_Bias_H1_Entry()
        ]
        
        self.volatility_strategies = [
            KeltnerChannel_Breakout(),
            VolatilityContraction_Expansion(),
            DonchianChannel_Breakout(20),
            DonchianChannel_Breakout(55)  # Turtle traders period
        ]
        
        self.all_strategies = (
            self.momentum_strategies +
            self.meanreversion_strategies +
            self.breakout_strategies +
            self.smc_strategies +
            self.timebased_strategies +
            self.mtf_strategies +
            self.volatility_strategies
        )
        
        # Results storage
        self.results = []
        
        # Backtest period
        self.days_back = 180  # 6 months
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=self.days_back)
    
    def run_comprehensive_test(self):
        """Run all strategies on all symbols and timeframes"""
        
        console.print("\n")
        console.print(Panel.fit(
            "[bold cyan]🔬 STRATEGY RESEARCH LAB[/bold cyan]\n"
            f"Testing {len(self.all_strategies)} strategies on {len(self.symbols)} symbols\n"
            f"Timeframes: {len(self.timeframes)} | Period: {self.days_back} days",
            border_style="cyan"
        ))
        console.print("\n")
        
        total_tests = len(self.all_strategies) * len(self.symbols) * len(self.timeframes)
        
        console.print(f"[yellow]Total backtests to run: {total_tests}[/yellow]")
        console.print("\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task("[cyan]Running backtests...", total=total_tests)
            
            for symbol in self.symbols:
                for tf, tf_name in self.timeframes:
                    for strategy in self.all_strategies:
                        try:
                            progress.update(
                                task,
                                description=f"[cyan]Testing {strategy.name} on {symbol} {tf_name}..."
                            )
                            
                            # Run backtest
                            engine = BacktestEngine(symbol, tf, self.start_date, self.end_date)
                            result = engine.run_backtest(strategy)
                            
                            self.results.append(result)
                            
                        except Exception as e:
                            console.print(f"[red]Error: {symbol} {tf_name} {strategy.name}: {str(e)}[/red]")
                        
                        progress.advance(task)
        
        console.print("\n[bold green]✓ Backtesting complete![/bold green]\n")
    
    def generate_report(self):
        """Generate comprehensive report"""
        
        if len(self.results) == 0:
            console.print("[red]No results to report[/red]")
            return
        
        # Filter to statistically significant results
        significant_results = [r for r in self.results if r.p_value < 0.05 and r.total_trades >= 10]
        
        # Sort by Sharpe Ratio
        top_results = sorted(significant_results, key=lambda x: x.sharpe_ratio, reverse=True)[:50]
        
        console.print(Panel.fit(
            f"[bold green]📊 RESEARCH RESULTS[/bold green]\n"
            f"Total tests: {len(self.results)}\n"
            f"Statistically significant (p<0.05): {len(significant_results)}\n"
            f"Showing top 50 strategies",
            border_style="green"
        ))
        console.print("\n")
        
        # Create results table
        table = Table(title="Top 50 Strategies (Ranked by Sharpe Ratio)", box=box.ROUNDED)
        
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Strategy", style="yellow")
        table.add_column("Symbol", style="magenta")
        table.add_column("TF", style="blue")
        table.add_column("Sharpe", justify="right", style="green")
        table.add_column("Win%", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("Return%", justify="right", style="green")
        table.add_column("Max DD%", justify="right", style="red")
        table.add_column("PF", justify="right")
        table.add_column("p-val", justify="right", style="dim")
        
        for i, result in enumerate(top_results[:50], 1):
            table.add_row(
                str(i),
                result.strategy_name,
                result.symbol,
                result.timeframe,
                f"{result.sharpe_ratio:.2f}",
                f"{result.win_rate*100:.1f}%",
                str(result.total_trades),
                f"{result.total_return_pct:+.1f}%",
                f"{result.max_drawdown_pct:.1f}%",
                f"{result.profit_factor:.2f}",
                f"{result.p_value:.3f}"
            )
        
        console.print(table)
        console.print("\n")
        
        # Category analysis
        self.analyze_by_category(top_results)
        
        # Best combinations
        self.analyze_best_combinations(top_results)
        
        # Export to file
        self.export_results(top_results)
    
    def analyze_by_category(self, results):
        """Analyze results by strategy category"""
        
        table = Table(title="Performance by Strategy Category", box=box.SIMPLE)
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")
        table.add_column("Avg Sharpe", justify="right", style="green")
        table.add_column("Avg Win%", justify="right")
        table.add_column("Avg Return%", justify="right")
        
        categories = {
            "Momentum": ["EMA", "MACD", "RSI Momentum", "ADX", "Stochastic Momentum"],
            "Mean Reversion": ["BB Reversal", "RSI Extreme", "S/R Bounce", "Range", "Stochastic Reversal"],
            "Breakout": ["Breakout", "Squeeze", "Volume", "Opening"]
        }
        
        for cat_name, keywords in categories.items():
            cat_results = [r for r in results if any(kw in r.strategy_name for kw in keywords)]
            
            if cat_results:
                avg_sharpe = np.mean([r.sharpe_ratio for r in cat_results])
                avg_win = np.mean([r.win_rate for r in cat_results]) * 100
                avg_return = np.mean([r.total_return_pct for r in cat_results])
                
                table.add_row(
                    cat_name,
                    str(len(cat_results)),
                    f"{avg_sharpe:.2f}",
                    f"{avg_win:.1f}%",
                    f"{avg_return:+.1f}%"
                )
        
        console.print(table)
        console.print("\n")
    
    def analyze_best_combinations(self, results):
        """Find best symbol-timeframe combinations"""
        
        table = Table(title="Best Symbol-Timeframe Combinations", box=box.SIMPLE)
        table.add_column("Symbol", style="magenta")
        table.add_column("Timeframe", style="blue")
        table.add_column("Count", justify="right")
        table.add_column("Avg Sharpe", justify="right", style="green")
        
        combinations = {}
        for r in results:
            key = f"{r.symbol}-{r.timeframe}"
            if key not in combinations:
                combinations[key] = []
            combinations[key].append(r)
        
        # Sort by average Sharpe
        sorted_combos = sorted(
            combinations.items(),
            key=lambda x: np.mean([r.sharpe_ratio for r in x[1]]),
            reverse=True
        )[:10]
        
        for key, combo_results in sorted_combos:
            symbol, tf = key.split('-')
            avg_sharpe = np.mean([r.sharpe_ratio for r in combo_results])
            
            table.add_row(
                symbol,
                tf,
                str(len(combo_results)),
                f"{avg_sharpe:.2f}"
            )
        
        console.print(table)
        console.print("\n")
    
    def export_results(self, results):
        """Export results to CSV"""
        
        data = []
        for r in results:
            data.append({
                'strategy': r.strategy_name,
                'symbol': r.symbol,
                'timeframe': r.timeframe,
                'sharpe_ratio': r.sharpe_ratio,
                'sortino_ratio': r.sortino_ratio,
                'win_rate': r.win_rate,
                'total_trades': r.total_trades,
                'total_return_pct': r.total_return_pct,
                'max_drawdown_pct': r.max_drawdown_pct,
                'profit_factor': r.profit_factor,
                'avg_win': r.avg_win,
                'avg_loss': r.avg_loss,
                'avg_rr': r.avg_rr,
                'expectancy': r.expectancy,
                'p_value': r.p_value
            })
        
        df = pd.DataFrame(data)
        filename = f"strategy_research_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        console.print(f"[green]✓ Results exported to {filename}[/green]")
        console.print("\n")


if __name__ == "__main__":
    lab = StrategyResearchLab()
    lab.run_comprehensive_test()
    lab.generate_report()
