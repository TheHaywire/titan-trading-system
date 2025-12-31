import pandas as pd
import numpy as np
import logging
import MetaTrader5 as mt5
from titan_system.research.auditor import TitanAuditor
from titan_system.research.data_loader import load_data
from titan_system.data.ingest_mt5 import ingest_history

logging.basicConfig(level=logging.WARNING)

def audit_var(account_value=10000):
    print("\n" + "="*80)
    print(f"   TITAN VaR AUDIT: VALUE AT RISK MODEL ({account_value} USD)")
    print("="*80)
    
    if not mt5.initialize():
        print("❌ MT5 Initialization failed.")
        return

    universe = ["GOLD", "EURUSD", "BTCUSD", "GBPUSD", "USDJPY"]
    symbol_data = {}
    
    print(f"Fetching 180 days of H1 data for {len(universe)} symbols...")
    
    for symbol in universe:
        auditor = TitanAuditor(symbol)
        resolved = auditor.symbol
        ingest_history(resolved, "H1", days=180)
        df = load_data(resolved, "H1")
        if not df.empty:
            symbol_data[symbol] = df

    if not symbol_data:
        print("❌ No data available for VaR calculation.")
        mt5.shutdown()
        return

    # 1. Prepare Returns DataFrame
    returns_dict = {}
    for symbol, df in symbol_data.items():
        # Use simple returns for VaR percentile calculation
        returns_dict[symbol] = df['close'].pct_change()
    
    returns_df = pd.DataFrame(returns_dict).dropna()
    
    if returns_df.empty:
        print("❌ Returns calculation returned empty dataset.")
        mt5.shutdown()
        return

    # 2. Calculate VaR (Assuming 1-hour horizon)
    auditor = TitanAuditor("GOLD")
    var_95 = auditor.calculate_var(returns_df, initial_value=account_value, confidence=0.95)
    var_99 = auditor.calculate_var(returns_df, initial_value=account_value, confidence=0.99)
    
    print("\nVALUE AT RISK (Historical Simulation | 1-Hour Horizon):")
    print("-" * 50)
    print(f"95% Confidence VaR: ${var_95:.2f}")
    print(f"99% Confidence VaR: ${var_99:.2f}")
    print("-" * 50)
    
    # 3. Insights
    max_drawdown_limit = account_value * 0.05 # 5% institutional standard for single horizon
    
    print(f"\nRISK ASSESSMENT:")
    if var_99 > max_drawdown_limit:
        print(f"🔴 HIGH RISK: 99% VaR (${var_99:.2f}) exceeds your 5% safety buffer (${max_drawdown_limit:.2f}).")
        print("   Recommendation: Reduce position sizing or diversify further.")
    else:
        print(f"🟢 SAFE: 99% VaR (${var_99:.2f}) is within institutional safety limits.")

    # 4. Save Report
    with open("VAR_REPORT.md", "w") as f:
        f.write(f"# Titan Value at Risk (VaR) Report\n\n")
        f.write(f"Account Basis: ${account_value:,.2f} USD\n\n")
        f.write("## Performance Metrics (1-Hour Horizon)\n")
        f.write(f"| Metric | Value | Interpretation |\n")
        f.write(f"| :--- | :--- | :--- |\n")
        f.write(f"| 95% VaR | ${var_95:.2f} | 5% chance of losing more than this in 1 hour. |\n")
        f.write(f"| 99% VaR | ${var_99:.2f} | 1% chance of losing more than this in 1 hour. |\n")
        
        f.write("\n\n## Quantitative Verdict\n")
        if var_99 > max_drawdown_limit:
            f.write("> [!CAUTION]\n")
            f.write(f"> **PORTFOLIO OVER-EXPOSURE**. Redline risk detected. Statistical modeling suggests the current asset mix is too volatile for your account size.")
        else:
            f.write("> [!IMPORTANT]\n")
            f.write(f"> **RISK WITHIN LIMITS**. The current asset mix is balanced for institutional-grade safety.")
            
        f.write("\n\n**Note**: This calculation assumes equal weighting across the universe. Real-time lot sizing will further adjust these figures.")

    print("\n✅ REPORT GENERATED: VAR_REPORT.md")
    print("="*80)
    
    mt5.shutdown()

if __name__ == "__main__":
    import sys
    try:
        acc = float(sys.argv[1]) if len(sys.argv) > 1 else 10000
    except ValueError:
        acc = 10000
    audit_var(acc)
