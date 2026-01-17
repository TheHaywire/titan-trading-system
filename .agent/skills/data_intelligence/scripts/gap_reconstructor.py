"""
GAP RECONSTRUCTOR
=================
Ensures time-series continuity.
Detects missing bars and performs interpolation.
"""

import pandas as pd
import numpy as np
import json
import MetaTrader5 as mt5
from datetime import datetime, timedelta

def reconstruct_gaps(df, timeframe_minutes):
    if df.empty:
        return df, {"status": "EMPTY"}
        
    df = df.copy()
    df['time'] = pd.to_datetime(df['time'])
    df.set_index('time', inplace=True)
    
    # 1. Detect Gaps
    # Calculate expected frequency
    expected_freq = f"{timeframe_minutes}T"
    
    # Reindex to fill missing time steps
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq=expected_freq)
    
    gaps_count = len(full_range) - len(df)
    
    if gaps_count > 0:
        # 2. Perform Reconstruction
        df_reconstructed = df.reindex(full_range)
        
        # Record where gaps were
        missing_mask = df_reconstructed['close'].isna()
        
        # Forward fill OHLC (to keep it realistic, prices stay same until next quote)
        df_reconstructed = df_reconstructed.ffill()
        
        # Reset index and return
        df_reconstructed.index.name = 'time'
        df_reconstructed.reset_index(inplace=True)
        
        report = {
            "status": "RECONSTRUCTED",
            "gaps_filled": gaps_count,
            "continuity_score": round((len(df) / len(full_range)) * 100, 2)
        }
        return df_reconstructed, report
    else:
        df.reset_index(inplace=True)
        return df, {"status": "CONTINUOUS", "gaps_filled": 0, "continuity_score": 100.0}

if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Not Connected")
    else:
        # Test on GOLD
        rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M15, 0, 500)
        if rates is not None:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df_clean, report = reconstruct_gaps(df, 15)
            print(json.dumps(report, indent=2))
        mt5.shutdown()
