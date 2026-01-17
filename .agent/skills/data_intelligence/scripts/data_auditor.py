"""
DATA AUDITOR (TICK PHYSICS)
===========================
Institutional data cleaning.
Detects unrealistic spikes and candle anomalies.
"""

import pandas as pd
import numpy as np
import json
import MetaTrader5 as mt5
from datetime import datetime

def audit_ohlcv(df, threshold_sigma=4.0):
    if df.empty:
        return {"status": "EMPTY_DATA"}
        
    df = df.copy()
    
    # 1. Calculate Typical Volatility (ATR-like)
    df['body_size'] = (df['close'] - df['open']).abs()
    df['candle_range'] = df['high'] - df['low']
    
    # Standard deviation of ranges
    range_mean = df['candle_range'].rolling(20).mean()
    range_std = df['candle_range'].rolling(20).std()
    
    # 2. Identify Spikes (Tick Physics violation)
    # If candle_range > mean + (sigma * std)
    df['is_spike'] = df['candle_range'] > (range_mean + threshold_sigma * range_std)
    
    spikes = df[df['is_spike']]
    
    # 3. Audit Result
    result = {
        "total_candles": len(df),
        "spikes_detected": len(spikes),
        "spike_details": [],
        "verdict": "CLEAN" if len(spikes) == 0 else "CAUTION"
    }
    
    for idx, row in spikes.tail(10).iterrows():
        result["spike_details"].append({
            "time": str(row['time']) if 'time' in row else str(idx),
            "range": round(row['candle_range'], 5),
            "dev_sigma": round((row['candle_range'] - range_mean.loc[idx]) / range_std.loc[idx], 2)
        })
        
    return result

if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Not Connected")
    else:
        # Test on GOLD
        rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M15, 0, 500)
        if rates is not None:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            report = audit_ohlcv(df)
            print(json.dumps(report, indent=2))
        mt5.shutdown()
