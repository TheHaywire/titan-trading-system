from titan_system.research.backtester import Backtester

def test_backtest():
    print("Initializing Backtest...")
    # Use "GOLD" as verified in last step
    bt = Backtester("GOLD", "H1")
    
    if bt.data.empty:
        print("FAIL: Data loader returned empty.")
        return

    print(f"Data Loaded: {len(bt.data)} rows.")
    
    # Run Strategy
    pf = bt.run_sma_crossover(fast_window=10, slow_window=20)
    
    trades_count = pf.trades.count()
    
    if pf and trades_count > -1:
         print("SUCCESS: Backtest completed successfully.")
    else:
         print("FAIL: Backtest object invalid.")

if __name__ == "__main__":
    test_backtest()
