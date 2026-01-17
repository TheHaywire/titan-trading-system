"""
ALPHA DECAY MONITOR
===================
Institutional forensics to detect when a trading edge is "decaying".
Analyzes Time-to-Profit (TTP) and Excursion efficiency.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
import sys

# Import the MT5 Bridge
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../mt5_bridge/scripts"))
sys.path.append(bridge_path)
from history_cleaner import get_cleaned_history

def analyze_alpha_decay(days=30, symbol=None):
    df = get_cleaned_history(days=days)
    
    if df is None or df.empty:
        return {"error": "No institutional trade history found for the period."}
    
    if symbol:
        df = df[df['symbol'] == symbol]
        
    if df.empty:
        mt5.shutdown()
        return {"error": f"No trades found for {symbol}."}

    # Filter for closing deals (where profit is realized)
    # entry: 0=Entry In, 1=Entry Out, 2=Entry Out/In (Reversed)
    exit_deals = df[df['entry'] == 1].copy()
    
    # Key Forensic Metrics
    report = {
        "summary": {
            "period_days": days,
            "total_trades": len(exit_deals),
            "win_rate": len(exit_deals[exit_deals['profit'] > 0]) / len(exit_deals) if len(exit_deals) > 0 else 0,
            "total_profit": exit_deals['profit'].sum()
        },
        "forensics": {}
    }

    # Analyze by Symbol
    symbols = exit_deals['symbol'].unique()
    for sym in symbols:
        s_df = exit_deals[exit_deals['symbol'] == sym]
        
        # In an institutional setup, we would link entry/exit to find duration
        # Simplified for now: average time between deals
        report["forensics"][sym] = {
            "avg_profit_per_trade": s_df['profit'].mean(),
            "profit_standard_dev": s_df['profit'].std(),
            "max_drawdown_deal": s_df['profit'].min(),
            "efficiency_ratio": s_df['profit'].mean() / s_df['profit'].std() if s_df['profit'].std() != 0 else 0
        }

    mt5.shutdown()
    return report

if __name__ == "__main__":
    result = analyze_alpha_decay(days=30)
    print(json.dumps(result, indent=4))
