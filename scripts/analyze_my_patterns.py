"""
HISTORICAL PATTERN MINER - The Missing Link
Analyzes YOUR past trades to find what actually worked
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

def analyze_historical_patterns():
    print("="*70)
    print("📊 HISTORICAL PATTERN INSIGHTS - YOUR ACTUAL EDGE")
    print("="*70)
    
    if not mt5.initialize():
        print("MT5 init failed")
        return
    
    # Get last 30 days of history
    from_date = datetime.now() - timedelta(days=30)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    if not deals:
        print("No trade history found")
        mt5.shutdown()
        return
    
    # Convert to dataframe
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time_dt'] = pd.to_datetime(df['time'], unit='s')
    df['hour'] = df['time_dt'].dt.hour
    df['day_of_week'] = df['time_dt'].dt.day_name()
    
    # Filter out balance operations
    df = df[df['profit'] != 0]
    
    if len(df) == 0:
        print("No closed trades found in last 30 days")
        mt5.shutdown()
        return
    
    print(f"\n📈 ANALYZED: {len(df)} trades from last 30 days")
    print(f"Total P&L: ${df['profit'].sum():,.2f}")
    print()
    
    # === PATTERN 1: Symbol Performance ===
    print("="*70)
    print("🎯 PATTERN 1: Which Symbols Make You Money?")
    print("="*70)
    
    symbol_stats = df.groupby('symbol').agg({
        'profit': ['sum', 'count', 'mean'],
    }).round(2)
    symbol_stats.columns = ['Total P&L', 'Trades', 'Avg P&L']
    symbol_stats = symbol_stats.sort_values('Total P&L', ascending=False)
    
    print(symbol_stats.head(10))
    print()
    
    winners = symbol_stats[symbol_stats['Total P&L'] > 0]
    losers = symbol_stats[symbol_stats['Total P&L'] < 0]
    
    print(f"✅ Profitable Symbols: {', '.join(winners.index.tolist())}")
    print(f"❌ Losing Symbols: {', '.join(losers.index.tolist())}")
    print()
    
    # === PATTERN 2: Time of Day ===
    print("="*70)
    print("⏰ PATTERN 2: When Do You Win?")
    print("="*70)
    
    hour_stats = df.groupby('hour').agg({
        'profit': ['sum', 'count', 'mean']
    }).round(2)
    hour_stats.columns = ['Total P&L', 'Trades', 'Avg P&L']
    hour_stats = hour_stats.sort_values('Total P&L', ascending=False)
    
    print(hour_stats.head(10))
    print()
    
    best_hours = hour_stats[hour_stats['Total P&L'] > 0].index.tolist()
    worst_hours = hour_stats[hour_stats['Total P&L'] < 0].index.tolist()
    
    print(f"🟢 POWER HOURS: {best_hours}")
    print(f"🔴 DEATH ZONES: {worst_hours}")
    print()
    
    # === PATTERN 3: Day of Week ===
    print("="*70)
    print("📅 PATTERN 3: Best Days to Trade?")
    print("="*70)
    
    day_stats = df.groupby('day_of_week').agg({
        'profit': ['sum', 'count', 'mean']
    }).round(2)
    day_stats.columns = ['Total P&L', 'Trades', 'Avg P&L']
    day_stats = day_stats.sort_values('Total P&L', ascending=False)
    
    print(day_stats)
    print()
    
    # === PATTERN 4: Direction Bias ===
    print("="*70)
    print("📊 PATTERN 4: BUY vs SELL Performance")
    print("="*70)
    
    df['direction'] = df['type'].apply(lambda x: 'BUY' if x == 0 else 'SELL')
    direction_stats = df.groupby('direction').agg({
        'profit': ['sum', 'count', 'mean']
    }).round(2)
    direction_stats.columns = ['Total P&L', 'Trades', 'Avg P&L']
    
    print(direction_stats)
    print()
    
    # === PATTERN 5: Volume Analysis ===
    print("="*70)
    print("💰 PATTERN 5: Position Size Impact")
    print("="*70)
    
    df['size_category'] = pd.cut(df['volume'], bins=[0, 1, 5, 10, 100], 
                                   labels=['Small (0-1)', 'Medium (1-5)', 'Large (5-10)', 'Huge (10+)'])
    
    size_stats = df.groupby('size_category').agg({
        'profit': ['sum', 'count', 'mean']
    }).round(2)
    size_stats.columns = ['Total P&L', 'Trades', 'Avg P&L']
    
    print(size_stats)
    print()
    
    # === ACTIONABLE INSIGHTS ===
    print("="*70)
    print("💡 ACTIONABLE RULES (Based on YOUR Data)")
    print("="*70)
    
    print("\n✅ WHAT TO DO MORE:")
    if len(winners) > 0:
        print(f"1. Focus on: {', '.join(winners.index[:3].tolist())}")
    if len(best_hours) > 0:
        print(f"2. Trade during hours: {best_hours[:3]}")
    if direction_stats.loc['BUY', 'Total P&L'] > direction_stats.loc['SELL', 'Total P&L']:
        print(f"3. Favor LONG positions (BUYs are more profitable)")
    else:
        print(f"3. Favor SHORT positions (SELLs are more profitable)")
    
    print("\n❌ WHAT TO AVOID:")
    if len(losers) > 0:
        print(f"1. Blacklist: {', '.join(losers.index[:3].tolist())}")
    if len(worst_hours) > 0:
        print(f"2. Don't trade hours: {worst_hours[:3]}")
    
    # Win Rate
    wins = len(df[df['profit'] > 0])
    total = len(df)
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    print(f"\n📊 Overall Win Rate: {win_rate:.1f}%")
    if win_rate < 50:
        print("⚠️ Below 50% - Need better entries or position sizing")
    
    # Generate report
    report_file = "analysis/HISTORICAL_PATTERNS_REPORT.md"
    os.makedirs("analysis", exist_ok=True)
    
    with open(report_file, "w") as f:
        f.write("# Historical Pattern Analysis Report\n\n")
        f.write(f"Generated: {datetime.now()}\n\n")
        f.write(f"## Summary\n")
        f.write(f"- Trades Analyzed: {len(df)}\n")
        f.write(f"- Total P&L: ${df['profit'].sum():,.2f}\n")
        f.write(f"- Win Rate: {win_rate:.1f}%\n\n")
        f.write(f"## Best Symbols\n")
        f.write(symbol_stats.head(5).to_markdown())
        f.write(f"\n\n## Best Trading Hours\n")
        f.write(hour_stats.head(5).to_markdown())
    
    print(f"\n📄 Full report saved: {report_file}")
    
    mt5.shutdown()

if __name__ == "__main__":
    analyze_historical_patterns()
