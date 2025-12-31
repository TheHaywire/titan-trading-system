import pandas as pd
import logging
import MetaTrader5 as mt5
from titan_system.research.auditor import TitanAuditor
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

logging.basicConfig(level=logging.WARNING)

def audit_full_universe():
    print("\n" + "="*80)
    print("   TITAN UNIVERSE AUDIT: INSTITUTIONAL HEALTH REPORT")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ MT5 Initialization failed.")
        return

    universe = ["GOLD", "EURUSD", "BTCUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF"]
    results = []

    print(f"\nScanning {len(universe)} symbols for Trend Quality and Liquidity...\n")
    
    for symbol in universe:
        auditor = TitanAuditor(symbol)
        resolved = auditor.symbol
        
        # 1. Liquidity Audit (Real-time)
        liq = auditor.audit_liquidity(resolved)
        
        # 2. Trend Quality Audit (Historical)
        ingest_history(resolved, "H1", days=10)
        df = load_data(resolved, "H1")
        trend_quality = auditor.audit_trend_quality(df)
        
        # 3. Categorization
        relevance = "EXCELLENT" if trend_quality > 0.4 else "CHOPPY"
        if trend_quality > 0.6: relevance = "LEGENDARY"
        if trend_quality < 0.2: relevance = "DEATH ZONE (NO TREND)"

        results.append({
            "SYMBOL": resolved,
            "SPREAD (PTS)": liq['spread_points'],
            "COST (USD)": f"${liq['cost_usd_est']:.2f}",
            "TREND QUALITY": f"{trend_quality:.2f}",
            "STATUS": relevance
        })

    # Display as Table
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    
    # Save to file
    with open("UNIVERSE_AUDIT.md", "w") as f:
        f.write("# Titan Universe Health Audit\n\n")
        f.write("This report ranks our universe by **Trend Quality** (Efficiency Ratio) and **Liquidity Cost**.\n\n")
        f.write(df_results.to_markdown(index=False))
        f.write("\n\n**Legend**: Trend Quality 1.0 = Straight Line. 0.0 = Random Noise.\n")

    print("\n" + "="*80)
    print("✅ MASTER REPORT GENERATED: UNIVERSE_AUDIT.md")
    print("="*80)
    
    mt5.shutdown()

if __name__ == "__main__":
    audit_full_universe()
