from titan_system.research.strategies.trend_surfer import TrendSurferStrategy
from titan_system.research.data_loader import load_data
import pandas as pd

def test_strategy_backtest():
    print("Testing TrendSurfer Strategy Backtest...")
    
    # 1. Load Data
    symbol = "GOLD"
    df = load_data(symbol, "H1")
    if df.empty:
        print("FAIL: No data loaded.")
        return

    print(f"Data Loaded: {len(df)} rows.")

    # 2. Run Strategy Backtest
    # We use slightly faster params for this small dataset if needed, but defaults are fine
    # Note: 30 days of H1 = 720 bars. 200 SMA needs 200 bars. It should work.
    strategy = TrendSurferStrategy(fast_period=20, slow_period=50) # Tighter periods for demo
    
    pf = strategy.run_backtest(df)
    
    if pf is None:
        print("FAIL: Backtest returned None.")
        return

    # 3. Process Result
    print(f"--- TrendSurfer Results ({symbol}) ---")
    print(f"Total Return: {pf.total_return():.2%}")
    
    try:
        print(f"Total Trades: {pf.trades.count()}")
    except Exception:
        print("Total Trades: N/A")
        
    try:
        # Try finding win rate in trades object
        print(f"Win Rate: {pf.trades.win_rate():.2%}")
    except Exception:
        print("Win Rate: N/A")
        
    # Print full stats for debugging
    # print(pf.stats()) 
    
    if pf.total_return() != 0:  
        print("SUCCESS: Strategy generated non-zero return (positive or negative).")
    else:
        print("WARNING: Strategy generated 0 return (No trades?)")

if __name__ == "__main__":
    test_strategy_backtest()
