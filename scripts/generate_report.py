import sys
import os
import json
import MetaTrader5 as mt5
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.feature_engine import FeatureEngine
from scripts.ai_professional_analyst import analyze_symbol

def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_report.py [SYMBOL]")
        return
        
    symbol = sys.argv[1].upper()
    print(f"\n🧠 GENERATING INSTITUTIONAL REPORT FOR [{symbol}]...")
    
    # 1. Initialize MT5 & Data
    detector = RegimeDetector(symbol)
    
    # 2. Build Holographic Feature Matrix
    print("  → Building MTF Holographic Matrix...")
    sp500_df = detector.get_market_data(symbol="US500Cash", count=100)
    eurusd_df = detector.get_market_data(symbol="EURUSD", count=100)
    
    s_info = mt5.symbol_info(symbol)
    spread = s_info.spread if s_info else 0
    
    quant_features = {}
    timeframes = {
        "m15": mt5.TIMEFRAME_M15,
        "h1": mt5.TIMEFRAME_H1,
        "h4": mt5.TIMEFRAME_H4
    }
    
    for tf_name, tf_const in timeframes.items():
        df_tf = detector.get_market_data(timeframe=tf_const, count=300)
        if df_tf is None or len(df_tf) < 100:
            continue
            
        eng = FeatureEngine(df_tf)
        eng.add_macro_correlation(sp500_df, "sp500")
        eng.add_macro_correlation(eurusd_df, "dxy")
        
        # Determine Hurst/OFI/etc for this timeframe
        lev_feats = eng.get_latest_features(symbol=symbol, spread_points=spread)
        
        for k, v in lev_feats.items():
            if k in ["spread_points", "open_positions"]: 
                quant_features[k] = v
            else:
                quant_features[f"{tf_name}_{k}"] = v

    # 3. Request AI Analysis
    print("  → Sending to Titan Central Intelligence...")
    result = analyze_symbol(symbol, quant_features)
    
    if result:
        filename, verdict = result
        
        # Read the file content to display it
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("\n" + "="*60)
        print(content)
        print("="*60)
        print(f"\n📂 Report Saved: {filename}")
    else:
        print("❌ Analysis Failed.")

if __name__ == "__main__":
    main()
