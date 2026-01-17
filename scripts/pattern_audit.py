"""
Titan Deep Pattern Audit
========================
Scans the last 100 bars of all liquid symbols and reports 
on institutional fingerprints (Liquidity Sweeps, Wicks, Squeezes).
"""

import os
import sys
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.pattern_intelligence import PatternMiner

SYMBOLS = ["GOLD", "BTCUSD", "US100Cash", "US30Cash", "EURUSD", "GBPUSD"]

def run_audit():
    print("🔍 RUNNING DEEP PATTERN AUDIT (Institutional Footprints)...")
    if not mt5.initialize():
        print("❌ MT5 Init Failed")
        return

    report = []
    
    for symbol in SYMBOLS:
        print(f"  📡 Scanning {symbol}...")
        detector = RegimeDetector(symbol)
        df = detector.get_market_data(count=100)
        
        if df is None:
            continue
            
        miner = PatternMiner(df)
        patterns = miner.get_all_patterns()
        
        # Analyze
        liq = patterns['liquidity']
        phys = patterns['physics']
        vol = patterns['volatility']
        abs_p = patterns['absorption']
        
        symbol_report = f"\n💎 {symbol} Patterns:"
        found = False
        
        if liq['pattern'] != "NONE":
            symbol_report += f"\n   🌟 {liq['pattern']} (Intensity: {liq['intensity']})"
            found = True
            
        if phys['rejection'] != "NONE":
            symbol_report += f"\n   🚨 {phys['rejection']} (U: {phys['upper_wick_ratio']}, L: {phys['lower_wick_ratio']})"
            found = True

        if abs_p['status'] != "NONE":
            symbol_report += f"\n   📊 ABSORPTION: {abs_p['status']} (Vol Surge: {abs_p['volume_surge']}x)"
            found = True
            
        if vol['status'] != "NORMAL":
            symbol_report += f"\n   🔄 VOLATILITY: {vol['status']} (Comp: {vol['compression']}x)"
            found = True
            
        if not found:
            symbol_report += "\n   ✅ No high-priority institutional patterns detected."
            
        print(symbol_report)
        report.append(symbol_report)

    mt5.shutdown()
    
    # Save to file
    with open("analysis/PATTERN_AUDIT_LATEST.md", "w", encoding="utf-8") as f:
        f.write("# 🔍 Titan Deep Pattern Audit\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("\n".join(report))
        
    print("\n✅ Pattern Audit Complete. Report saved to analysis/PATTERN_AUDIT_LATEST.md")

if __name__ == "__main__":
    run_audit()
