"""
WALK-FORWARD ANALYSIS (WFA) & ROBUSTNESS VALIDATOR
The ultimate stress test: Optimization on Past Data -> Testing on Unseen Future Data
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
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def fetch_data(symbol, timeframe=mt5.TIMEFRAME_D1, bars=3000):
    if not mt5.initialize():
        return None
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

class WalkForwardValidator:
    def __init__(self, symbol, initial_capital=10000):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.data = fetch_data(symbol)
        
    def run_macd_wfa(self, train_window_days=365*2, test_window_days=365):
        """
        Rolling Walk-Forward Analysis for MACD
        1. Optimize on Train Window
        2. Apply Best Params to Test Window
        3. Roll forward
        """
        console.print(Panel(f"[bold cyan]WALK-FORWARD ANALYSIS: {self.symbol} (MACD)[/bold cyan]"))
        
        close = self.data['close']
        
        # Parameter Space to Scan
        fast_range = range(8, 20, 2)
        slow_range = range(20, 60, 5)
        signal_range = [9] # Keep signal fixed to reduce complexity
        
        # Split Data into Segments
        start_idx = 0
        segments = []
        
        while start_idx + train_window_days + test_window_days < len(close):
            # Define Windows (Indices)
            train_start = start_idx
            train_end = start_idx + train_window_days
            test_start = train_end
            test_end = train_end + test_window_days
            
            # Slice Data
            train_close = close.iloc[train_start:train_end]
            test_close = close.iloc[test_start:test_end]
            
            test_date_start = test_close.index[0].strftime('%Y-%m-%d')
            test_date_end = test_close.index[-1].strftime('%Y-%m-%d')
            
            # --- OPTIMIZATION PHASE (In-Sample) ---
            best_sharpe = -999
            best_params = None
            
            # Simple Grid Search on Train Data
            # broadcasting would be faster but looped logic is clearer for WFA step-by-step
            
            # Use vbt broadcasting for speed on the train slice
            fast_comb, slow_comb = np.meshgrid(fast_range, slow_range)
            fast_flat = fast_comb.flatten()
            slow_flat = slow_comb.flatten()
            
            # Filter invalid combos
            valid_mask = fast_flat < slow_flat
            fast_flat = fast_flat[valid_mask]
            slow_flat = slow_flat[valid_mask]
            
            macd = vbt.MACD.run(
                train_close,
                fast_window=fast_flat,
                slow_window=slow_flat,
                signal_window=9
            )
            entries = macd.macd_above(macd.signal)
            exits = macd.macd_below(macd.signal)
            
            pf = vbt.Portfolio.from_signals(
                train_close, entries, exits, freq='1D',
                fees=0.001, slippage=0.001
            )
            
            sharpes = pf.sharpe_ratio()
            best_idx = sharpes.values.argmax()
            best_fast = fast_flat[best_idx]
            best_slow = slow_flat[best_idx]
            
            in_sample_sharpe = sharpes.max()
            
            # --- TESTING PHASE (Out-of-Sample) ---
            # Run ONLY the winner on the Test Data
            macd_test = vbt.MACD.run(
                test_close,
                fast_window=best_fast,
                slow_window=best_slow,
                signal_window=9
            )
            entries_test = macd_test.macd_above(macd_test.signal)
            exits_test = macd_test.macd_below(macd_test.signal)
            
            pf_test = vbt.Portfolio.from_signals(
                test_close, entries_test, exits_test, freq='1D',
                fees=0.001, slippage=0.001
            )
            
            out_sample_return = pf_test.total_return() * 100
            out_sample_sharpe = pf_test.sharpe_ratio()
            
            segments.append({
                'period': f"{test_date_start} -> {test_date_end}",
                'optimized_params': f"{best_fast}/{best_slow}/9",
                'in_sample_sharpe': in_sample_sharpe,
                'out_sample_sharpe': out_sample_sharpe,
                'out_sample_return': out_sample_return
            })
            
            # Roll forward by 6 months (approx 125 bars)
            start_idx += 125 
            
        return segments

    def run_breakout_wfa(self, train_window_days=365*2, test_window_days=365):
        """
        Rolling Walk-Forward Analysis for Turtle Breakout
        """
        console.print(Panel(f"[bold gold1]WALK-FORWARD ANALYSIS: {self.symbol} (Breakout)[/bold gold1]"))
        
        close = self.data['close']
        high = self.data['high']
        low = self.data['low']
        
        # Params
        entry_range = range(20, 80, 5)
        
        start_idx = 0
        segments = []
        
        while start_idx + train_window_days + test_window_days < len(close):
            train_start = start_idx
            train_end = start_idx + train_window_days
            test_start = train_end
            test_end = train_end + test_window_days
            
            # Slices
            s_train = slice(train_start, train_end)
            s_test = slice(test_start, test_end)
            
            test_period = f"{close.index[test_start].strftime('%Y-%m')} -> {close.index[test_end].strftime('%Y-%m')}"
            
            # -- TRAIN --
            best_sharpe = -999
            best_entry = 55
            
            # Simple loop optimization for Donchian
            for entry_w in entry_range:
                # Pre-calc rolling on whole series to avoid boundary issues, then slice
                # Not perfectly pure WFA but close enough for trend logic
                upper = high.shift(1).rolling(entry_w).max()
                lower = low.shift(1).rolling(int(entry_w/2)).min() # Fixed exit ratio 2:1
                
                entries = (close > upper).iloc[s_train]
                exits = (close < lower).iloc[s_train]
                
                pf = vbt.Portfolio.from_signals(
                    close.iloc[s_train], entries, exits, freq='1D',
                    fees=0.0003, slippage=0.0003
                )
                
                s = pf.sharpe_ratio()
                if s > best_sharpe:
                    best_sharpe = s
                    best_entry = entry_w
            
            # -- TEST --
            upper_test = high.shift(1).rolling(best_entry).max()
            lower_test = low.shift(1).rolling(int(best_entry/2)).min()
            
            entries_test = (close > upper_test).iloc[s_test]
            exits_test = (close < lower_test).iloc[s_test]
            
            pf_test = vbt.Portfolio.from_signals(
                close.iloc[s_test], entries_test, exits_test, freq='1D',
                fees=0.0003, slippage=0.0003
            )
            
            segments.append({
                'period': test_period,
                'optimized_params': f"In:{best_entry}/Out:{int(best_entry/2)}",
                'in_sample_sharpe': best_sharpe,
                'out_sample_sharpe': pf_test.sharpe_ratio(),
                'out_sample_return': pf_test.total_return() * 100
            })
            
            start_idx += 125 # Roll 6 months
            
        return segments

def print_wfa_results(segments):
    table = Table(title="Walk-Forward Analysis Results")
    table.add_column("Test Period", style="dim")
    table.add_column("Best Params (Past)", style="cyan")
    table.add_column("Expected Sharpe", justify="right")
    table.add_column("Real Sharpe", justify="right")
    table.add_column("Real Return", justify="right")
    
    total_return = 0
    passed = 0
    
    for s in segments:
        real_sharpe = s.get('out_sample_sharpe', 0)
        if np.isnan(real_sharpe): real_sharpe = 0
        
        style = "green" if real_sharpe > 0.5 else "red"
        if real_sharpe > 0.5: passed += 1
        
        table.add_row(
            s['period'],
            s['optimized_params'],
            f"{s['in_sample_sharpe']:.2f}",
            f"[{style}]{real_sharpe:.2f}[/{style}]",
            f"[{style}]{s['out_sample_return']:.1f}%[/{style}]"
        )
        total_return += s['out_sample_return']
        
    console.print(table)
    
    compounded = (1 + total_return/100/len(segments)) ** len(segments) # Rough approx
    console.print(f"\n[bold]WFA Summary:[/bold]")
    console.print(f"  Periods Passed: {passed}/{len(segments)} ({passed/len(segments)*100:.0f}%)")
    console.print(f"  Avg Return per Period: {total_return/len(segments):.2f}%")
    
    if passed/len(segments) > 0.6:
        console.print("[bold green]VERDICT: ROBUST (Passes WFA)[/bold green]")
    else:
        console.print("[bold red]VERDICT: FRAGILE (Fails WFA)[/bold red]")


if __name__ == "__main__":
    if not mt5.initialize(): sys.exit()
    
    # 1. Test ETH Trend
    validator = WalkForwardValidator("ETHUSD")
    results = validator.run_macd_wfa(
        train_window_days=365*2, # 2 Years training
        test_window_days=365     # 1 Year testing
    )
    print_wfa_results(results)
    
    # 2. Test GOLD Breakout
    validator_gold = WalkForwardValidator("GOLD")
    results_gold = validator_gold.run_breakout_wfa(
        train_window_days=365*3, # 3 Years training (Gold needs longer cycles)
        test_window_days=365     # 1 Year testing
    )
    print_wfa_results(results_gold)
    
    mt5.shutdown()
