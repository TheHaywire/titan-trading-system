import pandas as pd
import numpy as np
import logging
import MetaTrader5 as mt5
from titan_system.research.auditor import TitanAuditor
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

logging.basicConfig(level=logging.WARNING)

def analyze_extremes(symbol="GOLD"):
    print("\n" + "="*80)
    print(f"   TITAN QUANTILE AUDIT: THE 10% EXTREME MOVE FINDER ({symbol})")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ MT5 Initialization failed.")
        return

    auditor = TitanAuditor(symbol)
    resolved = auditor.symbol
    print(f"Resolved Symbol: {resolved}")
    
    # 1. Gather History (1 Year / 2000 bars)
    print(f"Analyzing 1-Year Return Distribution...")
    ingest_history(resolved, "H1", days=365)
    df = load_data(resolved, "H1")
    
    if df.empty or len(df) < 100:
        print("❌ Insufficient data for distribution analysis.")
        return

    # 2. Calculate Returns
    df['returns'] = np.log(df['close'] / df['close'].shift(1))
    returns = df['returns'].dropna()
    
    # 3. Calculate Quantiles
    quantiles = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
    values = returns.quantile(quantiles)
    
    print("\nRETURN DISTRIBUTION (H1):")
    print("-" * 50)
    print(f"{'PERCENTILE':<15} | {'RETURN %':<15} | {'LABEL'}")
    print("-" * 50)
    
    for q, v in zip(quantiles, values):
        p = q * 100
        label = "NORMAL"
        if p >= 90: label = "🔥 EXTREME (TOP 10%)"
        if p <= 10: label = "❄️ EXTREME (BOTTOM 10%)"
        if p == 50: label = "⚖️ MEDIAN"
        
        print(f"{p:>10.0f}th        | {v*100:>14.3f}% | {label}")
    
    # 4. Current State
    current_q = auditor.get_quantile_rank(df)
    print("\n" + "-" * 50)
    print(f"CURRENT CANDLE: {current_q['percentile']:.1f}th Percentile")
    print(f"CLIMATE       : {current_q['label']}")
    print("-" * 50)
    
    # Save Report
    with open("EXTREME_REPORT.md", "w") as f:
        f.write(f"# Extreme Move Audit: {symbol}\n\n")
        f.write("This report measures 'Rare' vs 'Routine' moves using **Quantile Analysis**.\n\n")
        
        f.write("| Percentile | Return % | Classification |\n")
        f.write("| :--- | :--- | :--- |\n")
        for q, v in zip(quantiles, values):
            f.write(f"| {q*100:.0f}th | {v*100:.3f}% | {'Extreme' if q >= 0.9 or q <= 0.1 else 'Routine'} |\n")
            
        f.write(f"\n**Current Market State**: {current_q['label']} ({current_q['percentile']:.1f}th Percentile)\n")
        f.write("\n> [!TIP]\n> Quants use the 90th percentile to identify high-conviction breakouts and the 99th percentile to spot exhaustion points.")

    print("\n✅ REPORT GENERATED: EXTREME_REPORT.md")
    print("="*80)
    
    mt5.shutdown()

if __name__ == "__main__":
    import sys
    sym = sys.argv[1] if len(sys.argv) > 1 else "GOLD"
    analyze_extremes(sym)
