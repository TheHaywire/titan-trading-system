"""
Analyze Historical Trading Performance
Reviews past 412 trades to identify what's working and what's not.
"""

import sys
import os
sys.path.append(os.getcwd())

import sqlite3
import pandas as pd
import numpy as np
from config.settings import settings as Config

def analyze_historical_performance():
    """Generate comprehensive performance report from database."""
    
    conn = sqlite3.connect(Config.db_path)
    
    # Load all trades
    df = pd.read_sql_query("""
        SELECT * FROM trades 
        WHERE profit IS NOT NULL
        ORDER BY open_time DESC
    """, conn)
    
    if len(df) == 0:
        print("❌ No trades with profit data found")
        return
    
    print("="*60)
    print("📊 HISTORICAL TRADING PERFORMANCE ANALYSIS")
    print("="*60)
    print(f"\nTotal Trades: {len(df)}")
    print(f"Date Range: {df['open_time'].min()} to {df['open_time'].max()}")
    
    # Overall Performance
    total_pnl = df['profit'].sum()
    winners = df[df['profit'] > 0]
    losers = df[df['profit'] <= 0]
    
    win_rate = len(winners) / len(df) * 100
    avg_win = winners['profit'].mean() if len(winners) > 0 else 0
    avg_loss = losers['profit'].mean() if len(losers) > 0 else 0
    expectancy = df['profit'].mean()
    
    print(f"\n{'='*60}")
    print("OVERALL METRICS")
    print(f"{'='*60}")
    print(f"Total P&L: ${total_pnl:,.2f}")
    print(f"Win Rate: {win_rate:.1f}% ({len(winners)}/{len(df)})")
    print(f"Avg Winner: ${avg_win:.2f}")
    print(f"Avg Loser: ${avg_loss:.2f}")
    print(f"Expectancy: ${expectancy:.2f} per trade")
    print(f"Profit Factor: {abs(winners['profit'].sum() / losers['profit'].sum()):.2f}" if len(losers) > 0 else "N/A")
    
    # Performance by Symbol
    print(f"\n{'='*60}")
    print("PERFORMANCE BY SYMBOL (Top 10)")
    print(f"{'='*60}")
    
    symbol_stats = df.groupby('symbol').agg({
        'profit': ['sum', 'mean', 'count'],
        'volume': 'sum'
    }).round(2)
    
    symbol_stats.columns = ['Total P&L', 'Avg P&L', 'Trades', 'Volume']
    symbol_stats = symbol_stats.sort_values('Total P&L', ascending=False)
    
    print(symbol_stats.head(10).to_string())
    
    # Winners and Losers
    print(f"\n{'='*60}")
    print("🏆 TOP 5 PROFITABLE SYMBOLS")
    print(f"{'='*60}")
    winners_by_symbol = symbol_stats[symbol_stats['Total P&L'] > 0].head(5)
    for symbol, row in winners_by_symbol.iterrows():
        wr = len(df[(df['symbol'] == symbol) & (df['profit'] > 0)]) / len(df[df['symbol'] == symbol]) * 100
        print(f"{symbol:12} | P&L: ${row['Total P&L']:>8.2f} | Trades: {int(row['Trades']):>4} | WR: {wr:>5.1f}%")
    
    print(f"\n{'='*60}")
    print("⚠️  TOP 5 LOSING SYMBOLS (Account Killers)")
    print(f"{'='*60}")
    losers_by_symbol = symbol_stats[symbol_stats['Total P&L'] < 0].tail(5).sort_values('Total P&L')
    for symbol, row in losers_by_symbol.iterrows():
        wr = len(df[(df['symbol'] == symbol) & (df['profit'] > 0)]) / len(df[df['symbol'] == symbol]) * 100
        print(f"{symbol:12} | P&L: ${row['Total P&L']:>8.2f} | Trades: {int(row['Trades']):>4} | WR: {wr:>5.1f}%")
    
    # Performance by Strategy
    if 'strategy_name' in df.columns and df['strategy_name'].notna().any():
        print(f"\n{'='*60}")
        print("PERFORMANCE BY STRATEGY")
        print(f"{'='*60}")
        
        strategy_stats = df.groupby('strategy_name').agg({
            'profit': ['sum', 'mean', 'count']
        }).round(2)
        
        strategy_stats.columns = ['Total P&L', 'Avg P&L', 'Trades']
        strategy_stats = strategy_stats.sort_values('Total P&L', ascending=False)
        
        print(strategy_stats.to_string())
    
    # Recent Performance Trend
    df['open_time'] = pd.to_datetime(df['open_time'])
    df['date'] = df['open_time'].dt.date
    
    daily_pnl = df.groupby('date')['profit'].sum()
    
    print(f"\n{'='*60}")
    print("RECENT PERFORMANCE (Last 10 Days)")
    print(f"{'='*60}")
    
    for date, pnl in daily_pnl.tail(10).items():
        emoji = "📈" if pnl > 0 else "📉"
        print(f"{date} {emoji} ${pnl:>8.2f}")
    
    # Actionable Recommendations
    print(f"\n{'='*60}")
    print("🎯 ACTIONABLE RECOMMENDATIONS")
    print(f"{'='*60}")
    
    # Identify symbols for winner scaling
    profitable_symbols = symbol_stats[symbol_stats['Total P&L'] > 200].index.tolist()
    if profitable_symbols:
        print(f"\n✅ SCALE UP (Winner Scaling 1.5x):")
        for sym in profitable_symbols[:5]:
            print(f"   - {sym}: ${symbol_stats.loc[sym, 'Total P&L']:.2f} total profit")
    
    # Identify symbols to blacklist
    consistent_losers = symbol_stats[
        (symbol_stats['Total P&L'] < -100) & 
        (symbol_stats['Trades'] >= 5)
    ].index.tolist()
    
    if consistent_losers:
        print(f"\n🚫 BLACKLIST (Account Killers):")
        for sym in consistent_losers:
            print(f"   - {sym}: ${symbol_stats.loc[sym, 'Total P&L']:.2f} loss over {int(symbol_stats.loc[sym, 'Trades'])} trades")
    
    # Risk Assessment
    if expectancy > 50:
        print(f"\n✅ SYSTEM EDGE DETECTED: ${expectancy:.2f} expectancy is profitable")
    elif expectancy > 0:
        print(f"\n⚠️  WEAK EDGE: ${expectancy:.2f} expectancy is barely profitable")
    else:
        print(f"\n🚨 NO EDGE: ${expectancy:.2f} negative expectancy - system losing money")
    
    if win_rate > 50:
        print(f"✅ WIN RATE HEALTHY: {win_rate:.1f}% is above 50%")
    else:
        print(f"⚠️  WIN RATE LOW: {win_rate:.1f}% - need R:R > {1/(win_rate/100):.1f}:1 to profit")
    
    conn.close()
    
    return {
        'total_trades': len(df),
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'expectancy': expectancy,
        'top_symbols': profitable_symbols[:3] if profitable_symbols else [],
        'blacklist': consistent_losers
    }

if __name__ == "__main__":
    results = analyze_historical_performance()
    
    print(f"\n{'='*60}")
    print("📝 NEXT STEPS")
    print(f"{'='*60}")
    print("1. Review the performance by symbol")
    print("2. Update AlphaOptimizer with winner/loser data")
    print("3. Run paper trading to validate current system")
    print("4. Backtest individual strategies on clean data")
