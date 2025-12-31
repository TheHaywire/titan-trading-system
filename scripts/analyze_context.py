import pandas as pd
import numpy as np
import logging
import sys
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

logging.basicConfig(level=logging.INFO)

def analyze_context(symbol="GOLD", timeframe="H1", lookback_days=180):
    print(f"\n{'='*70}")
    print(f"   DATA-DRIVEN CONTEXT AUDIT: {symbol} ({timeframe})")
    print(f"   Analyzing last {lookback_days} days of data...")
    print(f"{'='*70}\n")

    # 1. Fetch/Load Data
    ingest_history(symbol, timeframe, days=lookback_days)
    df = load_data(symbol, timeframe)
    
    if df.empty:
        print("Error: No data available for analysis.")
        return

    # 2. Hourly Volatility Profile (ATR per Hour)
    # Calculate True Range
    df['high_low'] = df['high'] - df['low']
    df['high_prev_close'] = abs(df['high'] - df['close'].shift(1))
    df['low_prev_close'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
    
    # Group by hour
    hourly_vol = df.groupby(df.index.hour)['tr'].mean()
    
    print(f"{'HOUR (UTC)':<10} | {'IST (Local)':<12} | {'RANGE (PIP)':<10} | {'CLIMATE'}       | {'INTENSITY'}")
    print("-" * 85)
    
    max_vol = hourly_vol.max()
    for hour, vol in hourly_vol.items():
        # IST is UTC + 5:30
        ist_hour = (hour + 5) % 24
        ist_min = "30" if hour + 5 < 24 else "30" # Simple enough for hours
        # More robust IST calculation
        ist_total_min = (hour * 60) + 330
        ist_h = (ist_total_min // 60) % 24
        ist_m = ist_total_min % 60
        ist_str = f"{ist_h:02d}:{ist_m:02d}"

        intensity_val = int((vol / max_vol) * 15)
        bar = "=" * intensity_val + "-" * (15 - intensity_val)
        
        climate = "POWER" if vol > hourly_vol.mean() * 1.2 else "QUIET"
        if vol < hourly_vol.mean() * 0.7: climate = "DEATH ZONE"
        
        print(f"{hour:02d}:00     | {ist_str:<12} | {vol:<10.3f} | {climate:<12} | {bar}")

    # 3. Session Statistics (Assumed vs Reality)
    def get_session(h):
        if 0 <= h < 8: return "Asian Session"
        if 8 <= h < 13: return "London Opening"
        if 13 <= h < 17: return "London/NY Overlap"
        if 17 <= h < 22: return "NY Afternoon"
        return "Day End Gap"

    df['session'] = df.index.hour.map(get_session)
    session_stats = df.groupby('session')['tr'].mean().sort_values(ascending=False)
    
    print("\n" + "="*70)
    print("   SESSION VELOCITY (REAL DATA)")
    print("="*70)
    for sess, val in session_stats.items():
        sess_intensity = int((val / session_stats.max()) * 20)
        sess_bar = "#" * sess_intensity
        print(f"{sess:<18} | {val:.3f} | {sess_bar}")

    print("\n" + "="*70)
    print("   CONCLUSION")
    print("-" * 70)
    top_hour = hourly_vol.idxmax()
    print(f"Highest Volatility Hour: {top_hour:02d}:00 UTC")
    print(f"Lowest Volatility Hour:  {hourly_vol.idxmin():02d}:00 UTC")
    print("Recommendation: Optimize bot to trigger ONLY during Power Hours.")
    print("="*70)

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "GOLD"
    analyze_context(sym)
