import logging
import sys
import pandas as pd
from titan_system.research.strategies.trend_surfer import TrendSurferStrategy
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

# Simple logger for script
logging.basicConfig(level=logging.WARNING)

def audit(symbol="GOLD"):
    print("\n" + "="*70)
    print(f"   STRATEGY AUDIT: {symbol} (Last 48 Hours)")
    print("="*70 + "\n")
    
    strategy = TrendSurferStrategy()
    
    # 1. Ensure data
    ingest_history(symbol, "H4", days=40)
    ingest_history(symbol, "H1", days=10)
    
    h4_df = load_data(symbol, "H4")
    h1_df = load_data(symbol, "H1")
    
    if h4_df.empty or h1_df.empty:
        print("Error: Could not load data for audit.")
        return

    # 2. Loop back through the last 20 H1 candles
    print(f"{'TIMESTAMP':<20} | {'SCORE':<5} | {'SIGNAL':<8} | {'REASON'}")
    print("-" * 70)
    
    for i in range(20, 0, -1):
        # Create 'snapshots' of data leading up to that point
        # We need a decent window for SMA (e.g. 50 bars)
        
        # This is a bit complex for a simple script, so we'll simplify:
        # Just run the analyze_mtf at each historical point.
        
        # Find H1 timestamp
        h1_point = h1_df.iloc[-i]
        ts = h1_point.name
        
        # Subsets of data up to this point
        h1_view = h1_df.iloc[:-i+1] # Includes the current candle
        
        # Find corresponding H4 data (aligned by time)
        # Note: In a real system we'd use index-based mapping, here we'll just slice
        h4_view = h4_df[h4_df.index <= ts]
        
        if len(h4_view) < 50 or len(h1_view) < 50: continue
        
        analysis = strategy.analyze_mtf(symbol, {'H4': h4_view, 'H1': h1_view})
        
        print(f"{str(ts):<20} | {analysis['score']:<5} | {analysis['order_type']:<8} | {analysis['comment']}")

    print("\n" + "="*70)
    print("Use this to see why the bot didn't trade (e.g. Counter-trend or Choppy).")
    print("="*70)

if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "GOLD"
    audit(sym)
