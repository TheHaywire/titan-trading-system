import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_complete_history():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return
    
    # Get ALL history from account inception
    history = mt5.history_deals_get(datetime(2020, 1, 1), datetime.now())
    
    if not history:
        print("No trading history found")
        mt5.shutdown()
        return
    
    df = pd.DataFrame(list(history), columns=history[0]._asdict().keys())
    
    # Filter for closed positions
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['month'] = df['time'].dt.to_period('M')
    
    # Aggregate by position
    positions = []
    for pos_id, group in df.groupby('position_id'):
        entry = group[group['entry'] == mt5.DEAL_ENTRY_IN]
        if entry.empty:
            continue
            
        symbol = entry['symbol'].iloc[0]
        direction = "Buy" if entry['type'].iloc[0] == 0 else "Sell"
        profit = group['profit'].sum() + group['commission'].sum() + group['swap'].sum()
        entry_time = entry['time'].iloc[0]
        volume = entry['volume'].iloc[0]
        
        positions.append({
            'Symbol': symbol,
            'Direction': direction,
            'Profit': profit,
            'Time': entry_time,
            'Volume': volume,
            'Month': entry_time.to_period('M')
        })
    
    df_positions = pd.DataFrame(positions)
    
    # Generate comprehensive statistics
    print("=" * 100)
    print("COMPLETE ACCOUNT HISTORY ANALYSIS")
    print("=" * 100)
    
    print(f"\n📊 OVERALL STATISTICS")
    print(f"Total Trades: {len(df_positions)}")
    print(f"Date Range: {df_positions['Time'].min()} to {df_positions['Time'].max()}")
    print(f"Total Profit: ${df_positions['Profit'].sum():,.2f}")
    
    # Win/Loss Stats
    winners = df_positions[df_positions['Profit'] > 0]
    losers = df_positions[df_positions['Profit'] <= 0]
    
    print(f"\n💰 WIN/LOSS BREAKDOWN")
    print(f"Winning Trades: {len(winners)} ({len(winners)/len(df_positions)*100:.1f}%)")
    print(f"Losing Trades: {len(losers)} ({len(losers)/len(df_positions)*100:.1f}%)")
    print(f"Average Win: ${winners['Profit'].mean():,.2f}")
    print(f"Average Loss: ${losers['Profit'].mean():,.2f}")
    
    # Profit Factor
    gross_profit = winners['Profit'].sum()
    gross_loss = abs(losers['Profit'].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    print(f"Profit Factor: {profit_factor:.2f}")
    
    # Symbol Analysis
    print(f"\n📈 TOP 10 SYMBOLS BY PROFIT")
    symbol_profits = df_positions.groupby('Symbol')['Profit'].agg(['sum', 'count', 'mean'])
    symbol_profits = symbol_profits.sort_values('sum', ascending=False).head(10)
    print(symbol_profits.to_string())
    
    print(f"\n📉 WORST 10 SYMBOLS BY PROFIT")
    worst_symbols = df_positions.groupby('Symbol')['Profit'].agg(['sum', 'count', 'mean'])
    worst_symbols = worst_symbols.sort_values('sum', ascending=True).head(10)
    print(worst_symbols.to_string())
    
    # Monthly Performance
    print(f"\n📅 MONTHLY PERFORMANCE")
    monthly = df_positions.groupby('Month')['Profit'].agg(['sum', 'count'])
    print(monthly.tail(12).to_string())
    
    # Direction Bias
    print(f"\n🎯 DIRECTION ANALYSIS")
    direction_stats = df_positions.groupby('Direction')['Profit'].agg(['sum', 'count', 'mean'])
    print(direction_stats.to_string())
    
    # Save detailed report
    report_file = f"analysis/COMPLETE_HISTORY_ANALYSIS_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df_positions.to_csv(report_file, index=False)
    print(f"\n✅ Detailed data saved to: {report_file}")
    
    mt5.shutdown()
    return df_positions

if __name__ == "__main__":
    analyze_complete_history()
