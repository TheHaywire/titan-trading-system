import pandas as pd
import numpy as np
import logging
import MetaTrader5 as mt5
from titan_system.research.auditor import TitanAuditor
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

logging.basicConfig(level=logging.WARNING)

def audit_correlation():
    print("\n" + "="*80)
    print("   TITAN CORRELATION AUDIT: PORTFOLIO OVERLAP CHECK")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ MT5 Initialization failed.")
        return

    universe = ["GOLD", "EURUSD", "BTCUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
    symbol_data = {}
    
    print(f"Fetching 30 days of H1 data for {len(universe)} symbols...")
    
    for symbol in universe:
        auditor = TitanAuditor(symbol)
        resolved = auditor.symbol
        # Small hack for GOLD in ingestion script which we know is XAUUSD or GOLD
        ingest_history(resolved, "H1", days=30)
        df = load_data(resolved, "H1")
        if not df.empty:
            symbol_data[symbol] = df

    if not symbol_data:
        print("❌ No data available for correlation audit.")
        mt5.shutdown()
        return

    # 1. Calculate Correlation
    auditor = TitanAuditor("GOLD") # Generic instance for utility call
    corr_matrix = auditor.calculate_correlation_matrix(symbol_data)
    
    if corr_matrix.empty:
        print("❌ Correlation matrix calculation failed.")
        mt5.shutdown()
        return

    # 2. Display Correlation Table
    print("\nCORRELATION MATRIX (Pearson):")
    print("-" * 80)
    print(corr_matrix.round(2).to_string())
    print("-" * 80)
    
    # 3. Identify Extreme Overlaps
    print("\n⚠️ EXTREME OVERLAPS (> 0.7 or < -0.7):")
    found_overlap = False
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            val = corr_matrix.iloc[i, j]
            if abs(val) > 0.7:
                s1 = corr_matrix.columns[i]
                s2 = corr_matrix.columns[j]
                print(f"  - {s1} & {s2}: {val:.2f}")
                found_overlap = True
    
    if not found_overlap:
        print("  None. Portfolio is well-diversified.")

    # 4. Save to Report
    with open("CORRELATION_REPORT.md", "w") as f:
        f.write("# Titan Portfolio Correlation Audit\n\n")
        f.write("This report identifies overlapping movements between assets to prevent over-exposure.\n\n")
        f.write("## Correlation Matrix\n")
        f.write(corr_matrix.round(2).to_markdown())
        f.write("\n\n## Risk Insights\n")
        if found_overlap:
            f.write("> [!WARNING]\n")
            f.write("> High Correlation detected. Avoid trading these pairs simultaneously as it triples your risk for the same move.\n")
        else:
            f.write("> [!NOTE]\n")
            f.write("> Portfolio is well-diversified. Low correlation between assets allows for more simultaneous trades.\n")
            
        f.write("\n**Quant Tip**: Institutional desks keep correlations below 0.6 to achieve a 'Smoother' equity curve.")

    print("\n✅ REPORT GENERATED: CORRELATION_REPORT.md")
    print("="*80)
    
    mt5.shutdown()

if __name__ == "__main__":
    audit_correlation()
