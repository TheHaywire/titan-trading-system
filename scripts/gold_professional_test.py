"""
PROFESSIONAL GOLD STRATEGY TEST - WITH VALIDATION
==================================================
Extended period: 24 months (not 6)
Critic validation: 30+ trades minimum
Statistical rigor: Multiple filters
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


class ProfessionalGoldTester:
    """Professional GOLD testing with validation"""
    
    # PROFESSIONAL STANDARDS (Critic requirements)
    MIN_TRADES = 30  # Minimum statistically valid
    MIN_SHARPE = 1.0  # Conservative threshold
    MIN_WIN_RATE = 0.35  # At least 35%
    MAX_DRAWDOWN = 25  # Max 25% DD
    
    def __init__(self):
        self.symbol = "GOLD"
        
        # Extended timeframes for more trades
        self.timeframes = [
            (mt5.TIMEFRAME_M15, "M15"),  # More active
            (mt5.TIMEFRAME_M30, "M30"),
            (mt5.TIMEFRAME_H1, "H1"),
            (mt5.TIMEFRAME_H4, "H4"),
            (mt5.TIMEFRAME_D1, "D1")
        ]
        
        self.all_strategies = self.get_all_strategies()
        
        # EXTENDED PERIOD - 24 months
        self.days_back = 730  # 2 years!
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=self.days_back)
        
        self.results = []
    
    def get_all_strategies(self):
        """All 40 strategies"""
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
        """Run comprehensive test"""
        
        console.print("\n")
        console.print(Panel.fit(
            "[bold yellow]🥇 PROFESSIONAL GOLD ANALYSIS[/bold yellow]\n"
            f"Period: {self.days_back} days (2 YEARS) - Extended for reliability\n"
            f"Strategies: {len(self.all_strategies)} | Timeframes: {len(self.timeframes)}\n"
            f"Validation: {self.MIN_TRADES}+ trades, Sharpe > {self.MIN_SHARPE}",
            border_style="yellow"
        ))
        console.print("\n")
        
        total_tests = len(self.all_strategies) * len(self.timeframes)
        console.print(f"[yellow]Total backtests: {total_tests}[/yellow]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            task = progress.add_task("[yellow]Testing GOLD (2 years)...", total=total_tests)
            
            for tf, tf_name in self.timeframes:
                for strategy in self.all_strategies:
                    try:
                        progress.update(
                            task,
                            description=f"[yellow]{strategy.name} on {self.symbol} {tf_name}..."
                        )
                        
                        engine = BacktestEngine(self.symbol, tf, self.start_date, self.end_date)
                        result = engine.run_backtest(strategy)
                        self.results.append(result)
                        
                    except Exception as e:
                        console.print(f"[red]Error: {tf_name} {strategy.name}: {str(e)}[/red]")
                    
                    progress.advance(task)
        
        console.print("\n[bold green]✓ Testing complete![/bold green]\n")
    
    def apply_critic_validation(self):
        """CRITIC validation with professional standards"""
        
        console.print(Panel.fit(
            "[bold red]🔍 CRITIC VALIDATION[/bold red]\n"
            "Applying professional quantitative standards",
            border_style="red"
        ))
        console.print("\n")
        
        # Initial filter
        initial = [r for r in self.results if r.p_value < 0.05]
        console.print(f"1. Statistical significance (p<0.05): {len(initial)}/{len(self.results)}")
        
        # Sample size
        sufficient_trades = [r for r in initial if r.total_trades >= self.MIN_TRADES]
        console.print(f"2. Sufficient trades (>={self.MIN_TRADES}): {len(sufficient_trades)}/{len(initial)}")
        
        # Positive Sharpe
        positive_sharpe = [r for r in sufficient_trades if r.sharpe_ratio >= self.MIN_SHARPE]
        console.print(f"3. Adequate Sharpe (>={self.MIN_SHARPE}): {len(positive_sharpe)}/{len(sufficient_trades)}")
        
        # Win rate
        good_win_rate = [r for r in positive_sharpe if r.win_rate >= self.MIN_WIN_RATE]
        console.print(f"4. Acceptable win rate (>={self.MIN_WIN_RATE*100}%): {len(good_win_rate)}/{len(positive_sharpe)}")
        
        # Drawdown
        validated = [r for r in good_win_rate if r.max_drawdown_pct <= self.MAX_DRAWDOWN]
        console.print(f"5. Acceptable drawdown (<={self.MAX_DRAWDOWN}%): {len(validated)}/{len(good_win_rate)}")
        
        console.print(f"\n[bold]FINAL: {len(validated)} strategies VALIDATED ✓[/bold]\n")
        
        return validated
    
    def show_results(self, validated):
        """Display validated results"""
        
        if len(validated) == 0:
            console.print("[red]❌ NO STRATEGIES PASSED VALIDATION[/red]\n")
            console.print("[yellow]This suggests:[/yellow]")
            console.print("  1. GOLD may need specialized strategies")
            console.print("  2. Parameter optimization required")
            console.print("  3. More complex multi-condition setups needed")
            return
        
        # Sort by Sharpe
        validated = sorted(validated, key=lambda x: x.sharpe_ratio, reverse=True)
        
        console.print(Panel.fit(
            f"[bold green]✓ {len(validated)} VALIDATED STRATEGIES[/bold green]\n"
            "These meet ALL professional standards",
            border_style="green"
        ))
        console.print("\n")
        
        table = Table(title="VALIDATED GOLD Strategies (Professional Standards)", box=box.ROUNDED)
        table.add_column("Rank", justify="right", style="cyan")
        table.add_column("Strategy", style="yellow")
        table.add_column("TF", style="blue")
        table.add_column("Sharpe", justify="right", style="green")
        table.add_column("Win%", justify="right")
        table.add_column("Trades", justify="right")
        table.add_column("Return%", justify="right")
        table.add_column("Max DD%", justify="right", style="red")
        
        for i, r in enumerate(validated, 1):
            table.add_row(
                str(i),
                r.strategy_name,
                r.timeframe,
                f"{r.sharpe_ratio:.2f}",
                f"{r.win_rate*100:.1f}%",
                str(r.total_trades),
                f"{r.total_return_pct:+.1f}%",
                f"{r.max_drawdown_pct:.1f}%"
            )
        
        console.print(table)
        console.print("\n")
        
        # Export
        data = []
        for r in validated:
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
        filename = f"gold_VALIDATED_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        console.print(f"[green]✓ Validated results exported to {filename}[/green]\n")


if __name__ == "__main__":
    tester = ProfessionalGoldTester()
    tester.run_test()
    validated = tester.apply_critic_validation()
    tester.show_results(validated)
