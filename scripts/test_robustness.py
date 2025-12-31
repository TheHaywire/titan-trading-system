from titan_system.research.strategies.trend_surfer import TrendSurferStrategy
from titan_system.research.data_loader import load_data
import pandas as pd

def test_robustness():
    symbols = ["GOLD", "EURUSD", "BTCUSD"]
    print("\n" + "="*60)
    print("   STRATEGY ROBUSTNESS CHECK: TrendSurfer")
    print("="*60)
    print(f"{'SYMBOL':<10} | {'RETURN':<10} | {'TRADES':<8} | {'WIN RATE':<10} | {'RESULT':<10}")
    print("-" * 60)
    
    overall_pnl = 0.0
    
    for symbol in symbols:
        try:
            # 1. Load Data
            df = load_data(symbol, "H1")
            if df.empty:
                print(f"{symbol:<10} | {'NO DATA':<10} | {'-':<8} | {'-':<10} | [SKIP]")
                continue

            # 2. Run Strategy
            strategy = TrendSurferStrategy()
            pf = strategy.run_backtest(df)
            
            if pf is None:
                print(f"{symbol:<10} | {'ERROR':<10} | {'-':<8} | {'-':<10} | [FAIL]")
                continue
                
            # 3. Stats
            ret = pf.total_return()
            try:
                trades = pf.trades.count()
                win_rate = pf.trades.win_rate()
            except:
                trades = 0
                win_rate = 0.0
                
            status = "[PASS]" if ret > 0 else "[FAIL]"
            if trades == 0: status = "[IDLE]"
            
            print(f"{symbol:<10} | {ret:<10.2%} | {trades:<8} | {win_rate:<10.2%} | {status:<10}")
            overall_pnl += ret
            
        except Exception as e:
            print(f"{symbol:<10} | {'ERROR':<10} | {str(e)[:20]}")
            
    print("-" * 60)
    print(f"OVERALL PORTFOLIO RETURN (Equal Weight): {overall_pnl/len(symbols):.2%}")
    print("="*60 + "\n")
    
    print("INTERPRETATION:")
    print("[PASS]: Strategy makes money on this asset.")
    print("[FAIL]: Strategy loses money on this asset (Needs Optimization or Filters).")
    print("[IDLE]: No trades generated (Market conditions didn't match strategy).")

if __name__ == "__main__":
    test_robustness()
