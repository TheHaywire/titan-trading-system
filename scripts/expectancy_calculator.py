"""
Expectancy Calculator - Analyze Trading Performance
Calculates expectancy, win rate, average R:R from trade logs
"""

import pandas as pd
import numpy as np
import sys
import os
# Ensure root is in path
sys.path.append(os.getcwd())

from datetime import datetime
from titan_system.core.symbol_mapper import mapper

def calculate_expectancy(trades_df):
    """
    Calculate trading expectancy and related metrics.
    
    Expectancy = (Win Rate × Avg Win) - (Loss Rate × Avg Loss)
    
    Returns dict with all key metrics.
    """
    
    # Filter out trades without profit data
    trades = trades_df[trades_df['profit'].notna()].copy()
    
    if len(trades) == 0:
        return {"error": "No valid trades with profit data"}
    
    # Separate wins and losses
    wins = trades[trades['profit'] > 0]
    losses = trades[trades['profit'] < 0]
    breakeven = trades[trades['profit'] == 0]
    
    total_trades = len(trades)
    win_count = len(wins)
    loss_count = len(losses)
    
    # Calculate metrics
    win_rate = (win_count / total_trades) * 100 if total_trades > 0 else 0
    loss_rate = (loss_count / total_trades) * 100 if total_trades > 0 else 0
    
    avg_win = wins['profit'].mean() if len(wins) > 0 else 0
    avg_loss = abs(losses['profit'].mean()) if len(losses) > 0 else 0
    
    # Expectancy (in currency)
    expectancy = (win_rate/100 * avg_win) - (loss_rate/100 * avg_loss)
    
    # R:R Ratio (average)
    avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
    
    # Profit Factor
    total_wins = wins['profit'].sum() if len(wins) > 0 else 0
    total_losses = abs(losses['profit'].sum()) if len(losses) > 0 else 0
    profit_factor = total_wins / total_losses if total_losses > 0 else 0
    
    # Largest win/loss
    largest_win = wins['profit'].max() if len(wins) > 0 else 0
    largest_loss = losses['profit'].min() if len(losses) > 0 else 0
    
    # Consecutive wins/losses
    trades['is_win'] = trades['profit'] > 0
    trades['streak'] = (trades['is_win'] != trades['is_win'].shift()).cumsum()
    
    win_streaks = trades[trades['is_win']].groupby('streak').size()
    loss_streaks = trades[~trades['is_win']].groupby('streak').size()
    
    max_win_streak = win_streaks.max() if len(win_streaks) > 0 else 0
    max_loss_streak = loss_streaks.max() if len(loss_streaks) > 0 else 0
    
    return {
        "total_trades": total_trades,
        "wins": win_count,
        "losses": loss_count,
        "breakeven": len(breakeven),
        "win_rate": win_rate,
        "loss_rate": loss_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "avg_rr": avg_rr,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "total_profit": trades['profit'].sum(),
        "largest_win": largest_win,
        "largest_loss": largest_loss,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak
    }


def analyze_by_symbol(trades_df):
    """Analyze expectancy per symbol"""
    symbol_stats = {}
    
    for symbol in trades_df['symbol'].unique():
        symbol_trades = trades_df[trades_df['symbol'] == symbol]
        stats = calculate_expectancy(symbol_trades)
        
        if 'error' not in stats:
            symbol_stats[symbol] = stats
    
    return symbol_stats


def analyze_by_strategy(trades_df):
    """Analyze expectancy per strategy"""
    if 'strategy' not in trades_df.columns:
        return {}
    
    strategy_stats = {}
    
    for strategy in trades_df['strategy'].unique():
        if pd.isna(strategy):
            continue
        strat_trades = trades_df[trades_df['strategy'] == strategy]
        stats = calculate_expectancy(strat_trades)
        
        if 'error' not in stats:
            strategy_stats[strategy] = stats
    
    return strategy_stats


def print_report(metrics, title="TRADING PERFORMANCE"):
    """Pretty print the metrics"""
    
    if 'error' in metrics:
        print(f"\n❌ {metrics['error']}")
        return
    
    print("\n" + "="*70)
    print(f" {title}")
    print("="*70)
    
    print(f"\n📊 OVERALL STATISTICS")
    print(f"   Total Trades: {metrics['total_trades']}")
    print(f"   Wins: {metrics['wins']} | Losses: {metrics['losses']} | Breakeven: {metrics['breakeven']}")
    print(f"   Win Rate: {metrics['win_rate']:.1f}%")
    print(f"   Loss Rate: {metrics['loss_rate']:.1f}%")
    
    print(f"\n💰 PROFIT METRICS")
    print(f"   Total Profit: ${metrics['total_profit']:.2f}")
    print(f"   Average Win: ${metrics['avg_win']:.2f}")
    print(f"   Average Loss: ${metrics['avg_loss']:.2f}")
    print(f"   Profit Factor: {metrics['profit_factor']:.2f}")
    
    print(f"\n🎯 EXPECTANCY & R:R")
    print(f"   Average R:R: {metrics['avg_rr']:.2f}:1")
    
    expectancy_color = "✅" if metrics['expectancy'] > 0 else "❌"
    print(f"   {expectancy_color} EXPECTANCY: ${metrics['expectancy']:.2f} per trade")
    
    if metrics['expectancy'] > 0:
        print(f"   💡 This system makes ${metrics['expectancy']:.2f} per trade on average")
    else:
        print(f"   ⚠️ This system LOSES ${abs(metrics['expectancy']):.2f} per trade on average")
    
    print(f"\n📈 EXTREMES")
    print(f"   Largest Win: ${metrics['largest_win']:.2f}")
    print(f"   Largest Loss: ${metrics['largest_loss']:.2f}")
    print(f"   Max Win Streak: {int(metrics['max_win_streak'])} trades")
    print(f"   Max Loss Streak: {int(metrics['max_loss_streak'])} trades")
    
    # Assessment
    print(f"\n🎓 ASSESSMENT")
    
    if metrics['expectancy'] > 0:
        if metrics['win_rate'] > 50:
            assessment = "EXCELLENT - High win rate + positive expectancy"
        else:
            assessment = "GOOD - Trend-following profile (low win rate, high R:R)"
    else:
        assessment = "NEEDS WORK - Negative expectancy means losing money over time"
    
    print(f"   Strategy Type: {assessment}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    
    if metrics['expectancy'] < 0:
        print("   - STOP TRADING - System has negative expectancy")
        print("   - Analyze what's not working (signals, execution, risk management)")
    elif metrics['expectancy'] < 0.5:
        print("   - Expectancy is positive but low - optimize win rate or R:R")
    elif metrics['expectancy'] < 1.0:
        print("   - Decent expectancy - can scale position sizes moderately")
    else:
        print("   - STRONG expectancy - this is a profitable system")
        print("   - Focus on consistency and proper risk management")
    
    print("="*70 + "\n")


def main():
    """Main entry point"""
    
    # Check for CSV file argument
    if len(sys.argv) < 2:
        print("\n❌ Usage: python scripts/expectancy_calculator.py <trades_csv_file>")
        print("\nExample: python scripts/expectancy_calculator.py data/trades.csv")
        print("\nCSV should have columns: symbol, profit, (optional: strategy)\n")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not os.path.exists(csv_file):
        print(f"\n❌ File not found: {csv_file}\n")
        sys.exit(1)
    
    # Load trades
    print(f"\n📂 Loading trades from: {csv_file}")
    
    try:
        trades_df = pd.read_csv(csv_file)
    except Exception as e:
        print(f"\n❌ Error reading CSV: {e}\n")
        sys.exit(1)
    
    # Validate and normalize column names
    columns = [c.lower() for c in trades_df.columns]
    
    # Detect profit column (could be 'profit', 'P&L', 'pnl', etc.)
    profit_col = None
    for col in trades_df.columns:
        if col.lower() in ['profit', 'p&l', 'pnl', 'pl']:
            profit_col = col
            break
    
    # Detect symbol column
    symbol_col = None  
    for col in trades_df.columns:
        if col.lower() in ['symbol', 'instrument', 'pair']:
            symbol_col = col
            break
    
    if not profit_col:
        print(f"\n❌ Could not find profit column")
        print(f"Looking for: profit, P&L, pnl, pl")
        print(f"Available columns: {list(trades_df.columns)}\n")
        sys.exit(1)
    
    if not symbol_col:
        print(f"\n❌ Could not find symbol column")
        print(f"Looking for: symbol, instrument, pair")
        print(f"Available columns: {list(trades_df.columns)}\n")
        sys.exit(1)
    
    # Normalize column names
    trades_df = trades_df.rename(columns={profit_col: 'profit', symbol_col: 'symbol'})
    
    # NEW: Resolve symbol aliases via SymbolMapper
    def resolve_log_symbol(s):
        res, _ = mapper.resolve(str(s))
        return res if res else s
    
    trades_df['symbol'] = trades_df['symbol'].apply(resolve_log_symbol)
    
    print(f"✅ Loaded {len(trades_df)} trades")
    
    # Overall analysis
    overall_metrics = calculate_expectancy(trades_df)
    print_report(overall_metrics, "OVERALL TRADING PERFORMANCE")
    
    # Per-symbol analysis
    symbol_stats = analyze_by_symbol(trades_df)
    
    if symbol_stats:
        print("\n" + "="*70)
        print(" PER-SYMBOL BREAKDOWN")
        print("="*70)
        
        # Sort by expectancy
        sorted_symbols = sorted(
            symbol_stats.items(), 
            key=lambda x: x[1]['expectancy'], 
            reverse=True
        )
        
        for symbol, stats in sorted_symbols:
            status = "✅" if stats['expectancy'] > 0 else "❌"
            print(f"\n{status} {symbol}")
            print(f"   Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%")
            print(f"   Expectancy: ${stats['expectancy']:.2f} | Profit: ${stats['total_profit']:.2f}")
    
    # Per-strategy analysis
    strategy_stats = analyze_by_strategy(trades_df)
    
    if strategy_stats:
        print("\n" + "="*70)
        print(" PER-STRATEGY BREAKDOWN")
        print("="*70)
        
        sorted_strategies = sorted(
            strategy_stats.items(),
            key=lambda x: x[1]['expectancy'],
            reverse=True
        )
        
        for strategy, stats in sorted_strategies:
            status = "✅" if stats['expectancy'] > 0 else "❌"
            print(f"\n{status} {strategy}")
            print(f"   Trades: {stats['total_trades']} | Win Rate: {stats['win_rate']:.1f}%")
            print(f"   Expectancy: ${stats['expectancy']:.2f} | R:R: {stats['avg_rr']:.2f}:1")
    
    print("\n📈 Analysis complete!\n")


if __name__ == "__main__":
    main()
