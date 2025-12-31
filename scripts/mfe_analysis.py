import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def analyze_mfe_mae():
    """Analyze peak profits (MFE) and peak losses (MAE) for individual trades."""
    print("🔬 STARTING VELOCITY & EXCURSION FORENSICS...")
    
    if not mt5.initialize():
        print("❌ MT5 Init failed")
        return

    # Load history
    history_file = "data/trade_history_full.csv"
    if not os.path.exists(history_file):
        print("❌ History file not found")
        return
        
    df_raw = pd.read_csv(history_file)
    df_raw['time'] = pd.to_datetime(df_raw['time'])
    
    # Pair Entries and Exits by Ticket
    # Note: MT5 deals use 'position_id' to link related entries/exits
    deals = df_raw.sort_values('time')
    positions = {}
    
    trade_results = []
    
    # Simple pairing logic based on position_id
    for pos_id, group in deals.groupby('position_id'):
        if len(group) < 2: continue
        
        entry_deal = group[group['entry_type'] == 'ENTRY']
        exit_deal = group[group['entry_type'] == 'EXIT']
        
        if entry_deal.empty or exit_deal.empty: continue
        
        entry_time = entry_deal.iloc[0]['time']
        exit_time = exit_deal.iloc[-1]['time']
        symbol = entry_deal.iloc[0]['symbol']
        side = entry_deal.iloc[0]['side']
        entry_price = entry_deal.iloc[0]['price']
        exit_price = exit_deal.iloc[-1]['price']
        volume = entry_deal.iloc[0]['volume']
        final_profit = group['profit'].sum()
        
        # Now fetch M1 price path during this trade
        # Buffer of 1 min
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M1, 
                                    entry_time - timedelta(minutes=1), 
                                    exit_time + timedelta(minutes=1))
        
        if rates is None or len(rates) == 0: continue
        
        path = pd.DataFrame(rates)
        path['time'] = pd.to_datetime(path['time'], unit='s')
        
        # Calculate Excursion
        if side == 'BUY':
            peak_price = path['high'].max()
            trough_price = path['low'].min()
            mfe_pips = (peak_price - entry_price) 
            mae_pips = (entry_price - trough_price)
        else: # SELL
            peak_price = path['low'].min()
            trough_price = path['high'].max()
            mfe_pips = (entry_price - peak_price)
            mae_pips = (trough_price - entry_price)
            
        # Get point value for pips
        symbol_info = mt5.symbol_info(symbol)
        point = symbol_info.point if symbol_info else 0.0001
        
        mfe_points = mfe_pips / point
        mae_points = mae_pips / point
        
        # Time to peak
        peak_time = path.loc[path['high' if side == 'BUY' else 'low'] == peak_price, 'time'].iloc[0]
        duration_to_peak = (peak_time - entry_time).total_seconds() / 60 # minutes
        total_duration = (exit_time - entry_time).total_seconds() / 60

        trade_results.append({
            'symbol': symbol,
            'side': side,
            'profit': final_profit,
            'mfe_points': mfe_points,
            'mae_points': mae_points,
            'peak_time_min': duration_to_peak,
            'total_time_min': total_duration,
            'was_profit_turned_loss': (mfe_points > 50 and final_profit < 0)
        })
        
        if len(trade_results) >= 500: break # Limit for speed
        print(f"Processed {len(trade_results)} trades...", end="\r")

    results_df = pd.DataFrame(trade_results)
    
    # 🔍 LEARNINGS
    print("\n\n📊 THE 'GHOST PROFIT' ANALYSIS")
    print("=" * 60)
    
    turned_loss = results_df[results_df['was_profit_turned_loss'] == True]
    print(f"1. Trades that reached >50pts profit BUT ended in loss: {len(turned_loss)} ({len(turned_loss)/len(results_df)*100:.1f}%)")
    
    fast_profits = results_df[results_df['peak_time_min'] < 5]
    print(f"2. 'Instant' Profits (Hit peak in <5 min): {len(fast_profits)} trades")
    print(f"   Avg Profit of Instant trades: ${fast_profits['profit'].mean():.2f}")
    
    efficiency = results_df['profit'] / (results_df['mfe_points'] * 10) # rough USD mapping
    print(f"3. Exit Efficiency: {results_df['mfe_points'].mean() / results_df['profit'].mean():.2f}x (Peak vs Final)")

    # Save
    results_df.to_csv("data/mfe_mae_analysis.csv", index=False)
    print("\n✅ Deep Forensic Data saved to: data/mfe_mae_analysis.csv")

if __name__ == "__main__":
    analyze_mfe_mae()
