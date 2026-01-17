import sys
import os
import glob
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.feature_engine import FeatureEngine

def get_latest_file(pattern):
    files = glob.glob(pattern)
    if not files:
        return None
    files.sort(reverse=True)
    return files[0]

def generate_asset_intelligence(symbol):
    """Generates real-time institutional intelligence for a specific asset."""
    print(f"\n🌍 GENERATING INSTITUTIONAL INTELLIGENCE FOR [{symbol}]...")
    
    if not mt5.initialize():
        print("❌ Failed to connect to MT5")
        return

    try:
        # 1. Regime & Data
        detector = RegimeDetector(symbol)
        df_h1 = detector.get_market_data(timeframe=mt5.TIMEFRAME_H1, count=300)
        
        if df_h1 is None or len(df_h1) < 100:
            print("❌ Insufficient data.")
            return

        # 2. Institutional Features
        engine = FeatureEngine(df_h1)
        
        # Macro
        sp500_df = detector.get_market_data(symbol="US500Cash", count=100)
        eurusd_df = detector.get_market_data(symbol="EURUSD", count=100)
        engine.add_macro_correlation(sp500_df, "sp500")
        engine.add_macro_correlation(eurusd_df, "dxy")
        
        # Micro info
        s_info = mt5.symbol_info(symbol)
        spread = s_info.spread if s_info else 0
        
        feats = engine.get_latest_features(symbol=symbol, spread_points=spread)
        
        # 3. Print Brief
        hurst = feats.get('hurst', 0.5)
        regime = "TRENDING 🚀" if hurst > 0.55 else ("MEAN REVERSION ↔️" if hurst < 0.45 else "CHOPPY 🌪️")
        
        imbalance = feats.get('imbalance', 0)
        void_status = "CRITICAL VOID DETECTED 🕳️" if imbalance > 1.5 else "Efficient Market ✅"
        
        ofi = feats.get('ofi_smooth', 0)
        flow = "Accumulation (Buying)" if ofi > 0 else "Distribution (Selling)"
        
        print(f"\n🏛️ **INSTITUTIONAL STATE**: {regime}")
        print(f"- **Hurst Exponent**: {hurst:.2f} (Structure)")
        print(f"- **Order Flow**: {flow} (OFI: {ofi:.2f})")
        print(f"- **Liquidity**: {void_status} (Imbalance: {imbalance:.2f})")
        print(f"- **Macro Alignment**: SP500 Corr: {feats.get('corr_sp500', 0):.2f} | DXY Corr: {feats.get('corr_dxy', 0):.2f}")
        
    except Exception as e:
        print(f"❌ Error analyzing {symbol}: {e}")
    finally:
        mt5.shutdown()

def generate_brief_snapshot(symbol=None):
    print("# 📊 Institutional Daily Brief Snapshot")
    print(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    
    # 0. Asset Specific Intelligence (if requested)
    if symbol:
        generate_asset_intelligence(symbol)
        print("\n" + "-"*40 + "\n")

    # 1. Get Latest Trade Audit
    audit_file = get_latest_file("analysis/TRADE_AUDIT_*.md")
    # 2. Get Latest Weekly Plan
    plan_file = get_latest_file("WEEKLY_TRADING_PLAN_*.csv")
    
    if plan_file:
        df_plan = pd.read_csv(plan_file)
        # Filter for specific symbol if requested, or top focus
        if symbol:
            relevant = df_plan[df_plan['Instrument'].str.contains(symbol, case=False, na=False)]
            if not relevant.empty:
                print(f"## 📜 Matrix Plan for {symbol}")
                for _, row in relevant.iterrows():
                    print(f"- **Score**: {row['Net Score']}")
                    print(f"- **Bias**: {row['Primary Bias']}")
                    print(f"- **Notes**: {row['Notes']}")
            else:
                print(f"## 📜 Matrix Plan for {symbol}")
                print("- Not explicitly covered in the Weekly Plan.")
        else:
            top_focus = df_plan[(df_plan['Focus'] == 'Focus') | (df_plan['Net Score'].astype(float).abs() >= 4)].head(3)
            print("## 🎯 Strategic Focus (Top Matrix Assets)")
            if not top_focus.empty:
                for _, row in top_focus.iterrows():
                    print(f"- **{row['Instrument']}** (Score: {row['Net Score']}): {row['Notes']}")
            else:
                print("- No high-conviction assets today. Stay patient.")
    
    if audit_file:
        print(f"\n## ⚖️ Recent Performance Snapshot")
        print(f"Latest Audit found: {os.path.basename(audit_file)}")
        # We don't print the whole thing, just a link/summary
        print(f"- Discipline Score: [View Full Audit]({audit_file})")
    
    print("\n\n> [!NOTE]")
    print("> Please ask the AI to 'Synthesize today's Macro News' to complete this brief.")

if __name__ == "__main__":
    target_symbol = sys.argv[1].upper() if len(sys.argv) > 1 else None
    generate_brief_snapshot(target_symbol)
