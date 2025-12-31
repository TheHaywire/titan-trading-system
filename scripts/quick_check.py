"""Quick analysis check - no emojis for Windows compatibility"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd

def main():
    print("=" * 50)
    print("MARKET ANALYSIS CHECK")
    print("=" * 50)
    
    mt5.initialize()
    
    from titan_system.smc.institutional_engine import InstitutionalEngine
    inst = InstitutionalEngine()
    
    symbols = ["EURUSD", "GBPUSD", "GOLD", "USDJPY"]
    
    for sym in symbols:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 200)
        if rates is None:
            print(f"{sym}: No data")
            continue
        
        df = pd.DataFrame(rates)
        
        try:
            result = inst.analyze_symbol(df, sym)
            regime = result.get("regime", "N/A")
            setups = result.get("setup", [])
            
            print(f"\n{sym}:")
            print(f"  Regime: {regime}")
            print(f"  Setups: {len(setups)}")
            
            if setups:
                for s in setups:
                    name = s.get("name", "unknown")
                    print(f"    -> {name}")
            else:
                print("    -> No valid setups right now")
                
        except Exception as e:
            print(f"{sym}: Error - {e}")
    
    print("\n" + "=" * 50)
    print("WHAT THIS MEANS:")
    print("=" * 50)
    print("The QuantAI engine waits for SPECIFIC conditions:")
    print("  1. Strong trend regime (TSS >= 4)")
    print("  2. FVG retest or Liquidity sweep")
    print("  3. RSI alignment with trend")
    print("  4. Session quality (London/NY overlap)")
    print("\nIf no setups found = market is ranging/choppy")
    print("System is WORKING - just waiting for good spots!")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
