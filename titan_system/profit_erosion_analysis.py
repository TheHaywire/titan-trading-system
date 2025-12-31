"""
Profit Erosion Analysis - Deep Psychological & Technical Trade Review
======================================================================
Identifies specific patterns causing profit erosion:
1. Position sizing issues (oversizing after wins, undersizing after losses)
2. Revenge trading patterns
3. Time-based performance breakdowns
4. Symbol-specific issues
5. Holding time analysis
6. Win/Loss sequences
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def analyze_profit_erosion(csv_path: str):
    """Comprehensive profit erosion analysis."""
    
    print("=" * 80)
    print("  PROFIT EROSION FORENSIC ANALYSIS")
    print("  Understanding Why Profits Are Given Back")
    print("=" * 80)
    print()
    
    # Load and clean data
    df = pd.read_csv(csv_path)
    
    # Filter to actual trades (not Other/deposits)
    trades = df[df['Symbol'].notna() & (df['Symbol'] != '')].copy()
    trades = trades[trades['P&L'] != 0].copy()  # Only closed trades with P&L
    
    # Parse datetime
    trades['DateTime'] = pd.to_datetime(trades['Date'] + ' ' + trades['Time'])
    trades['Hour'] = trades['DateTime'].dt.hour
    trades['DayOfWeek'] = trades['DateTime'].dt.day_name()
    trades['Month'] = trades['DateTime'].dt.month
    trades['IsWin'] = trades['P&L'] > 0
    
    print(f"📊 Total Trades Analyzed: {len(trades)}")
    print(f"📅 Date Range: {trades['DateTime'].min()} to {trades['DateTime'].max()}")
    print()
    
    # ========================================================================
    # SECTION 1: OVERALL STATISTICS
    # ========================================================================
    print("═" * 80)
    print("  1️⃣  OVERALL STATISTICS")
    print("═" * 80)
    
    total_profit = trades[trades['P&L'] > 0]['P&L'].sum()
    total_loss = abs(trades[trades['P&L'] < 0]['P&L'].sum())
    net_pnl = trades['P&L'].sum()
    win_rate = (trades['IsWin'].sum() / len(trades)) * 100 if len(trades) > 0 else 0
    
    print(f"  💚 Total Gross Profit: ${total_profit:,.2f}")
    print(f"  🔴 Total Gross Loss:   ${total_loss:,.2f}")
    print(f"  📈 Net P&L:            ${net_pnl:,.2f}")
    print(f"  🎯 Win Rate:           {win_rate:.1f}%")
    print(f"  📊 Profit Factor:      {total_profit/total_loss:.2f}" if total_loss > 0 else "  📊 Profit Factor: N/A")
    print()
    
    # ========================================================================
    # SECTION 2: THE BIG LOSERS - Where Did The Money Go?
    # ========================================================================
    print("═" * 80)
    print("  2️⃣  THE BIG LOSERS - Where Did The Money Go?")
    print("═" * 80)
    
    # Top 20 biggest losses
    biggest_losses = trades[trades['P&L'] < 0].nlargest(20, 'P&L', keep='first').iloc[::-1]
    
    if len(biggest_losses) > 0:
        print("\n  🚨 TOP 20 BIGGEST SINGLE LOSSES:")
        print("  " + "-" * 75)
        total_big_loss = 0
        for _, row in biggest_losses.head(20).iterrows():
            print(f"  {row['DateTime']} | {row['Symbol']:12} | Vol: {row['Quantity']:>6.2f} | P&L: ${row['P&L']:>12,.2f}")
            total_big_loss += row['P&L']
        print("  " + "-" * 75)
        print(f"  💀 Total from Top 20 Losses: ${total_big_loss:,.2f}")
        print(f"  📉 This is {abs(total_big_loss/total_loss)*100:.1f}% of all losses!")
    print()
    
    # ========================================================================
    # SECTION 3: POSITION SIZING ISSUES
    # ========================================================================
    print("═" * 80)
    print("  3️⃣  POSITION SIZING ANALYSIS")
    print("═" * 80)
    
    # Analyze volume distribution
    vol_stats = trades.groupby('Symbol')['Quantity'].agg(['mean', 'std', 'min', 'max'])
    
    # Find trades where volume was 5x+ average
    trades['SymbolAvgVol'] = trades.groupby('Symbol')['Quantity'].transform('mean')
    oversized = trades[trades['Quantity'] > trades['SymbolAvgVol'] * 5]
    
    if len(oversized) > 0:
        print(f"\n  ⚠️ OVERSIZED TRADES (>5x Average Volume): {len(oversized)} trades")
        oversized_pnl = oversized['P&L'].sum()
        print(f"  📊 Net P&L from Oversized Trades: ${oversized_pnl:,.2f}")
        
        # Show breakdown
        oversized_losses = oversized[oversized['P&L'] < 0]['P&L'].sum()
        oversized_wins = oversized[oversized['P&L'] > 0]['P&L'].sum()
        print(f"  💚 Wins:   ${oversized_wins:,.2f}")
        print(f"  🔴 Losses: ${oversized_losses:,.2f}")
        
        if oversized_pnl < 0:
            print(f"\n  🚨 CRITICAL: Oversizing is a MAJOR problem!")
            print(f"     You're losing ${abs(oversized_pnl):,.2f} from position sizing alone!")
    print()
    
    # ========================================================================
    # SECTION 4: REVENGE TRADING DETECTION
    # ========================================================================
    print("═" * 80)
    print("  4️⃣  REVENGE TRADING PATTERN ANALYSIS")
    print("═" * 80)
    
    # Sort by datetime for sequence analysis
    trades_sorted = trades.sort_values('DateTime').reset_index(drop=True)
    
    # Detect rapid trading after losses
    trades_sorted['PrevPnL'] = trades_sorted['P&L'].shift(1)
    trades_sorted['PrevTime'] = trades_sorted['DateTime'].shift(1)
    trades_sorted['TimeSincePrev'] = (trades_sorted['DateTime'] - trades_sorted['PrevTime']).dt.total_seconds() / 60
    
    # Trades within 5 minutes of a loss
    revenge_candidates = trades_sorted[
        (trades_sorted['PrevPnL'] < 0) & 
        (trades_sorted['TimeSincePrev'] < 5)
    ]
    
    if len(revenge_candidates) > 0:
        revenge_pnl = revenge_candidates['P&L'].sum()
        print(f"\n  🔥 RAPID TRADES AFTER LOSSES (<5 min): {len(revenge_candidates)} trades")
        print(f"  📊 Net P&L from these trades: ${revenge_pnl:,.2f}")
        
        if revenge_pnl < 0:
            print(f"\n  🚨 CRITICAL: Revenge trading is costing you ${abs(revenge_pnl):,.2f}!")
            print("     RECOMMENDATION: Implement a 5-minute cooling period after any loss.")
    print()
    
    # ========================================================================
    # SECTION 5: TIME-BASED ANALYSIS
    # ========================================================================
    print("═" * 80)
    print("  5️⃣  TIME-BASED PERFORMANCE BREAKDOWN")
    print("═" * 80)
    
    print("\n  📊 P&L BY HOUR (UTC):")
    print("  " + "-" * 50)
    hourly = trades.groupby('Hour').agg({
        'P&L': ['sum', 'count'],
        'IsWin': 'mean'
    })
    hourly.columns = ['Net_PnL', 'Trades', 'WinRate']
    hourly = hourly.sort_values('Net_PnL')
    
    # Death hours (worst 5)
    print("\n  💀 DEATH HOURS (Worst Performance):")
    for hr, row in hourly.head(5).iterrows():
        symbol = "🔴" if row['Net_PnL'] < 0 else "💚"
        print(f"  {symbol} Hour {hr:02d}:00 UTC | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}%")
    
    # Power hours (best 5)
    print("\n  💰 POWER HOURS (Best Performance):")
    for hr, row in hourly.tail(5).iloc[::-1].iterrows():
        symbol = "🔴" if row['Net_PnL'] < 0 else "💚"
        print(f"  {symbol} Hour {hr:02d}:00 UTC | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}%")
    
    # Day of week
    print("\n  📊 P&L BY DAY OF WEEK:")
    print("  " + "-" * 50)
    daily = trades.groupby('DayOfWeek').agg({
        'P&L': ['sum', 'count'],
        'IsWin': 'mean'
    })
    daily.columns = ['Net_PnL', 'Trades', 'WinRate']
    
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    for day in day_order:
        if day in daily.index:
            row = daily.loc[day]
            symbol = "🔴" if row['Net_PnL'] < 0 else "💚"
            print(f"  {symbol} {day:12} | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}%")
    print()
    
    # ========================================================================
    # SECTION 6: SYMBOL PERFORMANCE
    # ========================================================================
    print("═" * 80)
    print("  6️⃣  SYMBOL PERFORMANCE BREAKDOWN")
    print("═" * 80)
    
    symbol_stats = trades.groupby('Symbol').agg({
        'P&L': ['sum', 'count', 'mean'],
        'IsWin': 'mean',
        'Quantity': 'mean'
    })
    symbol_stats.columns = ['Net_PnL', 'Trades', 'Avg_PnL', 'WinRate', 'Avg_Vol']
    symbol_stats = symbol_stats.sort_values('Net_PnL')
    
    print("\n  🔴 WORST PERFORMING SYMBOLS:")
    print("  " + "-" * 70)
    for sym, row in symbol_stats.head(10).iterrows():
        print(f"  {sym:15} | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}% | Avg Vol: {row['Avg_Vol']:.2f}")
    
    print("\n  💚 BEST PERFORMING SYMBOLS:")
    print("  " + "-" * 70)
    for sym, row in symbol_stats.tail(5).iloc[::-1].iterrows():
        print(f"  {sym:15} | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}% | Avg Vol: {row['Avg_Vol']:.2f}")
    print()
    
    # ========================================================================
    # SECTION 7: CONSECUTIVE WIN/LOSS SEQUENCES
    # ========================================================================
    print("═" * 80)
    print("  7️⃣  STREAK ANALYSIS - Emotional Trading Detection")
    print("═" * 80)
    
    trades_sorted['WinLossGroup'] = (trades_sorted['IsWin'] != trades_sorted['IsWin'].shift()).cumsum()
    streaks = trades_sorted.groupby('WinLossGroup').agg({
        'IsWin': 'first',
        'P&L': ['sum', 'count']
    })
    streaks.columns = ['IsWin', 'Total_PnL', 'Streak_Length']
    
    # Worst losing streaks
    losing_streaks = streaks[streaks['IsWin'] == False].nlargest(5, 'Streak_Length')
    print("\n  😰 WORST LOSING STREAKS:")
    for _, row in losing_streaks.iterrows():
        print(f"  🔴 {int(row['Streak_Length'])} consecutive losses = ${row['Total_PnL']:,.2f}")
    
    # After big losing streaks, what happens?
    print("\n  📊 BEHAVIOR AFTER 3+ CONSECUTIVE LOSSES:")
    # Find trades immediately after 3+ loss streaks
    after_streak_losses = []
    for i in range(len(trades_sorted)):
        if i >= 3:
            prev_3 = trades_sorted.iloc[i-3:i]['IsWin']
            if not prev_3.any():  # All losses
                after_streak_losses.append(trades_sorted.iloc[i])
    
    if after_streak_losses:
        after_df = pd.DataFrame(after_streak_losses)
        after_pnl = after_df['P&L'].sum()
        after_winrate = after_df['IsWin'].mean() * 100
        print(f"  Number of trades after 3+ loss streaks: {len(after_df)}")
        print(f"  Net P&L from these trades: ${after_pnl:,.2f}")
        print(f"  Win Rate: {after_winrate:.1f}%")
        
        if after_pnl < 0:
            print("\n  🚨 CRITICAL: You're making bad decisions after losing streaks!")
            print("     RECOMMENDATION: Stop trading completely after 3 consecutive losses.")
    print()
    
    # ========================================================================
    # SECTION 8: GOLD SPECIFIC ANALYSIS (Major culprit from data)
    # ========================================================================
    print("═" * 80)
    print("  8️⃣  GOLD DEEP DIVE - Your Main Instrument")
    print("═" * 80)
    
    gold_trades = trades[trades['Symbol'] == 'GOLD']
    if len(gold_trades) > 0:
        gold_profit = gold_trades[gold_trades['P&L'] > 0]['P&L'].sum()
        gold_loss = abs(gold_trades[gold_trades['P&L'] < 0]['P&L'].sum())
        gold_net = gold_trades['P&L'].sum()
        
        print(f"\n  📊 GOLD Statistics:")
        print(f"  Total Trades: {len(gold_trades)}")
        print(f"  💚 Gross Profit: ${gold_profit:,.2f}")
        print(f"  🔴 Gross Loss:   ${gold_loss:,.2f}")
        print(f"  📈 Net P&L:      ${gold_net:,.2f}")
        
        # Volume analysis for GOLD
        gold_by_vol = gold_trades.groupby(pd.cut(gold_trades['Quantity'], 
                                                   bins=[0, 1, 5, 10, 25, 50, 100])).agg({
            'P&L': ['sum', 'count'],
            'IsWin': 'mean'
        })
        gold_by_vol.columns = ['Net_PnL', 'Trades', 'WinRate']
        
        print("\n  📊 GOLD P&L BY POSITION SIZE:")
        print("  " + "-" * 60)
        for vol_range, row in gold_by_vol.iterrows():
            if row['Trades'] > 0:
                symbol = "🔴" if row['Net_PnL'] < 0 else "💚"
                print(f"  {symbol} Vol {vol_range} | P&L: ${row['Net_PnL']:>12,.2f} | Trades: {row['Trades']:>4.0f} | WR: {row['WinRate']*100:.1f}%")
        
        # GOLD by hour
        gold_hourly = gold_trades.groupby('Hour')['P&L'].sum().sort_values()
        print("\n  📊 GOLD WORST HOURS:")
        for hr in gold_hourly.head(5).index:
            pnl = gold_hourly[hr]
            print(f"  🔴 Hour {hr:02d}:00 UTC | P&L: ${pnl:>12,.2f}")
    print()
    
    # ========================================================================
    # SECTION 9: THE VERDICT - Root Causes
    # ========================================================================
    print("═" * 80)
    print("  🎯 THE VERDICT - ROOT CAUSES OF PROFIT EROSION")
    print("═" * 80)
    
    issues = []
    
    # Check for oversizing
    if len(oversized) > 0 and oversized['P&L'].sum() < -10000:
        issues.append(f"🔴 OVERSIZING: Losing ${abs(oversized['P&L'].sum()):,.0f} from trades 5x+ average size")
    
    # Check for revenge trading
    if len(revenge_candidates) > 0 and revenge_candidates['P&L'].sum() < -5000:
        issues.append(f"🔴 REVENGE TRADING: Losing ${abs(revenge_candidates['P&L'].sum()):,.0f} from rapid trades after losses")
    
    # Check for bad time windows
    worst_hours = hourly.head(3)
    if worst_hours['Net_PnL'].sum() < -20000:
        bad_hrs = ', '.join([f"{h}:00" for h in worst_hours.index])
        issues.append(f"🔴 BAD TIMING: Losing ${abs(worst_hours['Net_PnL'].sum()):,.0f} in hours {bad_hrs}")
    
    # Check for symbol issues
    worst_symbols = symbol_stats.head(3)
    if worst_symbols['Net_PnL'].sum() < -20000:
        bad_syms = ', '.join(worst_symbols.index[:3])
        issues.append(f"🔴 BAD SYMBOLS: Losing ${abs(worst_symbols['Net_PnL'].sum()):,.0f} on {bad_syms}")
    
    print()
    for issue in issues:
        print(f"  {issue}")
    
    print("\n  " + "=" * 70)
    print("  📋 TOP RECOMMENDATIONS:")
    print("  " + "=" * 70)
    
    recommendations = [
        "1. POSITION SIZING: Cap max volume to 2x your average trade size",
        "2. COOLING PERIOD: Wait 5+ minutes after any loss before trading again",
        "3. DAILY LOSS LIMIT: Stop trading after 3 consecutive losses",
        "4. SESSION FOCUS: Trade only during your profitable hours",
        "5. SYMBOL SELECTION: Consider avoiding or reducing size on losing symbols",
        "6. JOURNAL: Document your emotional state before each trade"
    ]
    
    for rec in recommendations:
        print(f"  ✅ {rec}")
    
    print("\n" + "=" * 80)
    print("  Analysis Complete!")
    print("=" * 80)
    
    return {
        'net_pnl': net_pnl,
        'win_rate': win_rate,
        'issues': issues,
        'worst_symbols': symbol_stats.head(5).to_dict(),
        'worst_hours': hourly.head(5).to_dict()
    }


if __name__ == "__main__":
    # Run analysis on latest export
    csv_path = Path(__file__).parent / "trades_export_20251229.csv"
    if csv_path.exists():
        results = analyze_profit_erosion(str(csv_path))
    else:
        # Try the data folder
        csv_path = Path(__file__).parent.parent / "data" / "trade_history_full.csv"
        if csv_path.exists():
            results = analyze_profit_erosion(str(csv_path))
        else:
            print("❌ No trade history file found!")
