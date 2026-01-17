"""
Titan Deep Forensic Analyzer
============================
Separates Manual vs. Automated trades and provides a detailed teaching report.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
import os

def run_forensic_analysis():
    print("🧠 Starting Deep Forensic Analysis...")
    
    if not mt5.initialize():
        print("Error: MT5 Init Failed")
        return

    # Fetch history from 1 month ago to now
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=30)
    
    deals = mt5.history_deals_get(start_date, end_date)
    
    if not deals or len(deals) == 0:
        print("No history found.")
        mt5.shutdown()
        return

    # Convert to DataFrame
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Filter only ENTRY and EXIT deals
    df = df[df['entry'].isin([mt5.DEAL_ENTRY_IN, mt5.DEAL_ENTRY_OUT])]
    
    # Pair entries and exits by position_id
    positions = {}
    for _, deal in df.iterrows():
        pid = deal['position_id']
        if pid not in positions:
            positions[pid] = {'deals': [], 'symbol': deal['symbol']}
        positions[pid]['deals'].append(deal)

    completed_trades = []
    
    for pid, data in positions.items():
        deals = sorted(data['deals'], key=lambda x: x['time'])
        if len(deals) >= 2:
            entry = deals[0]
            exit_deal = deals[-1]
            
            # Classification
            magic = entry['magic']
            comment = str(entry['comment']).lower()
            
            is_auto = False
            if magic != 0 or any(kw in comment for kw in ['titan', 'auto', 'orb', 'smc', 'rsi']):
                is_auto = True
            
            origin = "AUTOMATED" if is_auto else "MANUAL"
            
            # Metrics
            profit = sum(d['profit'] for d in deals)
            commission = sum(d['commission'] for d in deals)
            swap = sum(d['swap'] for d in deals)
            net_pnl = profit + commission + swap
            
            duration = exit_deal['time'] - entry['time']
            
            completed_trades.append({
                'symbol': data['symbol'],
                'origin': origin,
                'pnl': net_pnl,
                'duration_mins': duration.total_seconds() / 60,
                'hour': entry['time'].hour,
                'type': 'BUY' if entry['type'] == mt5.DEAL_TYPE_BUY else 'SELL'
            })

    if not completed_trades:
        print("No completed trades found to analyze.")
        mt5.shutdown()
        return

    report_df = pd.DataFrame(completed_trades)
    
    # AGGREGATED REPORT
    print("\n" + "="*60)
    print("BATTLE OF THE MINDS: MANUAL VS. AUTOMATED")
    print("="*60)
    
    summary = report_df.groupby('origin')['pnl'].agg(['count', 'sum', 'mean']).rename(columns={'count': 'Trades', 'sum': 'Net P&L', 'mean': 'Avg/Trade'})
    
    # Calculate Win Rates
    win_rates = report_df[report_df['pnl'] > 0].groupby('origin').size() / report_df.groupby('origin').size() * 100
    summary['Win Rate %'] = win_rates
    
    print(summary.to_string())
    
    print("\n" + "="*60)
    print("TEACHING INSIGHTS")
    print("="*60)
    
    # Insight 1: Hold Times
    durations = report_df.groupby('origin')['duration_mins'].mean()
    print(f"PATIENCE: Manual trades are held for {durations.get('MANUAL', 0):.1f} mins on avg, while the Bot holds for {durations.get('AUTOMATED', 0):.1f} mins.")
    
    # Insight 2: Symbol Strength
    best_manual = report_df[report_df['origin'] == 'MANUAL'].groupby('symbol')['pnl'].sum().sort_values(ascending=False).head(1)
    best_auto = report_df[report_df['origin'] == 'AUTOMATED'].groupby('symbol')['pnl'].sum().sort_values(ascending=False).head(1)
    
    if not best_manual.empty:
        print(f"MANUAL STRENGTH: You are best at trading {best_manual.index[0]} (+${best_manual.values[0]:.2f})")
    if not best_auto.empty:
        print(f"BOT STRENGTH: The algorithm dominates in {best_auto.index[0]} (+${best_auto.values[0]:.2f})")

    # Insight 3: Time of Day
    bad_hour = report_df.groupby('hour')['pnl'].sum().sort_values().head(1)
    print(f"DANGER ZONE: Most money is lost during Hour {bad_hour.index[0]}:00 UTC. Check if this is the Asian Open or NY Reversal.")

    mt5.shutdown()

if __name__ == "__main__":
    run_forensic_analysis()
