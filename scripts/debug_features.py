import os
import sys
import pandas as pd
import json
import MetaTrader5 as mt5
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.feature_engine import FeatureEngine
from titan_system.core.execution import MT5Execution

class MockConfig:
    def __init__(self):
        self.mt5_login = None
        self.mt5_password = None
        self.mt5_server = None

def main():
    symbol = sys.argv[1] if len(sys.argv) > 1 else "GOLD"
    symbol = symbol.upper()
    print(f"--- TITAN FEATURE ENGINE REAL-TIME AUDIT ({symbol}) ---")
    
    # Setup connection
    execution = MT5Execution(MockConfig())
    if not execution.connect():
        print("Failed to connect to MT5")
        return

    # Fetch Data
    detector = RegimeDetector(symbol)
    df = detector.get_market_data(count=300)
    
    if df is None or df.empty:
        print("No data received")
        return

    # Fetch live spread
    s_info = mt5.symbol_info(symbol)
    spread = s_info.spread if s_info else 0

    # Add Macro Benchmarks
    sp500_df = detector.get_market_data(symbol="US500Cash", count=100)
    eurusd_df = detector.get_market_data(symbol="EURUSD", count=100)
    
    # Calculate Features for M15, H1, H4
    features = {}
    
    tfs = {"m15": mt5.TIMEFRAME_M15, "h1": mt5.TIMEFRAME_H1, "h4": mt5.TIMEFRAME_H4}
    
    for tf_name, tf_const in tfs.items():
        df_tf = detector.get_market_data(timeframe=tf_const, count=300)
        if df_tf is not None:
            eng = FeatureEngine(df_tf)
            eng.add_macro_correlation(sp500_df, "sp500")
            eng.add_macro_correlation(eurusd_df, "dxy")
            feats = eng.get_latest_features(symbol=symbol, spread_points=spread)
            
            for k, v in feats.items():
                 if k in ["spread_points", "news_proximity", "open_positions"]: 
                     features[k] = v
                 else:
                     features[f"{tf_name}_{k}"] = v

    # Print in a pretty format
    print(f"\n[LATEST INSTITUTIONAL HOLOGRAPHIC STATE]:")
    print("-" * 60)
    
    # Add open positions info
    positions = execution.get_positions()
    symbol_pos = [p for p in positions if p['symbol'] == symbol]
    features['open_positions'] = len(symbol_pos)

    # Grouping features for readability
    # Grouping features for readability (MTF View)
    base_metrics = [
        "hurst", "imbalance", "risk_prox", "ofi_smooth", "roc_20", "autocorr_1"
    ]
    
    print(f"{'METRIC':<20} | {'M15 (Tactical)':<15} | {'H1 (Intermediate)':<15} | {'H4 (Structure)':<15}")
    print("-" * 75)
    
    for metric in base_metrics:
        m15_val = features.get(f"m15_{metric}", "N/A")
        h1_val = features.get(f"h1_{metric}", "N/A")
        h4_val = features.get(f"h4_{metric}", "N/A")
        
        print(f"{metric:<20} | {str(m15_val):<15} | {str(h1_val):<15} | {str(h4_val):<15}")

    print("-" * 75)
    print(f"Spread: {features.get('spread_points')} | Open Pos: {features.get('open_positions')}")
    print("-" * 75)
    execution.shutdown()

if __name__ == "__main__":
    main()
