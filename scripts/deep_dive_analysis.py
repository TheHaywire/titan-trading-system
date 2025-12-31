import pandas as pd
import numpy as np
from datetime import datetime

def deep_dive_analysis():
    """Perform granular trade-by-trade analysis."""
    print("🔬 DEEP DIVE: Trade-by-Trade Forensics\n")
    
    # Load the saved data
    df = pd.read_csv("data/trade_history_full.csv")
    df['time'] = pd.to_datetime(df['time'])
    
    exits = df[df['entry_type'] == 'EXIT'].copy()
    exits = exits.sort_values('profit', ascending=False)
    
    print("=" * 80)
    print("🏆 TOP 10 WINNING TRADES (The Money Makers)")
    print("=" * 80)
    top_winners = exits.head(10)[['time', 'symbol', 'side', 'volume', 'profit', 'comment']]
    for idx, row in top_winners.iterrows():
        print(f"\n💰 ${row['profit']:,.2f} | {row['symbol']} {row['side']}")
        print(f"   Time: {row['time']}")
        print(f"   Size: {row['volume']} lots")
        print(f"   Note: {row['comment']}")
    
    print("\n" + "=" * 80)
    print("💀 TOP 10 LOSING TRADES (The Profit Killers)")
    print("=" * 80)
    top_losers = exits.tail(10)[['time', 'symbol', 'side', 'volume', 'profit', 'comment']]
    for idx, row in top_losers.iterrows():
        print(f"\n🔴 ${row['profit']:,.2f} | {row['symbol']} {row['side']}")
        print(f"   Time: {row['time']}")
        print(f"   Size: {row['volume']} lots")
        print(f"   Note: {row['comment']}")
    
    # Analyze position sizing impact
    print("\n" + "=" * 80)
    print("📊 POSITION SIZING ANALYSIS")
    print("=" * 80)
    
    # Correlation between lot size and profit
    correlation = exits[['volume', 'profit']].corr().iloc[0, 1]
    print(f"Volume vs Profit Correlation: {correlation:.3f}")
    
    # Group by lot size buckets
    exits['lot_bucket'] = pd.cut(exits['volume'], bins=[0, 0.5, 1.0, 2.0, 5.0, 100], 
                                   labels=['Micro (<0.5)', 'Small (0.5-1)', 'Medium (1-2)', 'Large (2-5)', 'Whale (>5)'])
    
    size_analysis = exits.groupby('lot_bucket')['profit'].agg(['sum', 'count', 'mean'])
    print("\nProfit by Position Size:")
    print(size_analysis)
    
    # Symbol Deep Dive
    print("\n" + "=" * 80)
    print("🎯 SYMBOL PERFORMANCE MATRIX")
    print("=" * 80)
    
    symbol_stats = exits.groupby('symbol').agg({
        'profit': ['sum', 'count', 'mean'],
        'volume': 'mean'
    }).round(2)
    
    symbol_stats.columns = ['Total PnL', 'Trades', 'Avg PnL', 'Avg Size']
    symbol_stats = symbol_stats.sort_values('Total PnL', ascending=False)
    
    print("\nTop 15 Symbols:")
    print(symbol_stats.head(15))
    
    print("\nBottom 10 Symbols (Losers to Avoid):")
    print(symbol_stats.tail(10))
    
    # Time-based patterns
    print("\n" + "=" * 80)
    print("⏰ TIME-BASED PROFIT PATTERNS")
    print("=" * 80)
    
    exits['hour'] = exits['time'].dt.hour
    exits['day_of_week'] = exits['time'].dt.day_name()
    
    hour_pnl = exits.groupby('hour')['profit'].agg(['sum', 'count', 'mean']).round(2)
    hour_pnl.columns = ['Total PnL', 'Trades', 'Avg PnL']
    
    print("\nProfit by Hour (GMT):")
    print(hour_pnl)
    
    print("\nProfit by Day of Week:")
    day_pnl = exits.groupby('day_of_week')['profit'].agg(['sum', 'count', 'mean']).round(2)
    print(day_pnl)
    
    # Streak analysis
    print("\n" + "=" * 80)
    print("🎲 WINNING/LOSING STREAK ANALYSIS")
    print("=" * 80)
    
    exits = exits.sort_values('time')
    exits['is_winner'] = exits['profit'] > 0
    
    # Find longest streaks
    streaks = []
    current_streak = 1
    current_type = exits.iloc[0]['is_winner']
    
    for i in range(1, len(exits)):
        if exits.iloc[i]['is_winner'] == current_type:
            current_streak += 1
        else:
            streaks.append((current_type, current_streak))
            current_streak = 1
            current_type = exits.iloc[i]['is_winner']
    
    streaks.append((current_type, current_streak))
    
    winning_streaks = [s[1] for s in streaks if s[0] == True]
    losing_streaks = [s[1] for s in streaks if s[0] == False]
    
    print(f"Longest Winning Streak: {max(winning_streaks)} trades")
    print(f"Longest Losing Streak: {max(losing_streaks)} trades")
    print(f"Average Winning Streak: {np.mean(winning_streaks):.1f} trades")
    print(f"Average Losing Streak: {np.mean(losing_streaks):.1f} trades")
    
    # Save detailed report
    with open("data/deep_analysis_report.txt", "w") as f:
        f.write("DEEP TRADE ANALYSIS REPORT\n")
        f.write("=" * 80 + "\n\n")
        f.write("TOP SYMBOLS:\n")
        f.write(symbol_stats.head(15).to_string())
        f.write("\n\nWORST SYMBOLS:\n")
        f.write(symbol_stats.tail(10).to_string())
        f.write("\n\nBEST HOURS:\n")
        f.write(hour_pnl.to_string())
    
    print("\n✅ Deep Analysis Complete")
    print("💾 Detailed report saved to: data/deep_analysis_report.txt")
    
    return {
        'top_symbols': symbol_stats.head(5),
        'worst_symbols': symbol_stats.tail(5),
        'best_hours': hour_pnl.nlargest(5, 'Total PnL')
    }

if __name__ == "__main__":
    results = deep_dive_analysis()
