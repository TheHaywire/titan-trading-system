import pandas as pd
import numpy as np
from titan_system.portfolio.optimizer import PortfolioOptimizer
from titan_system.portfolio.risk_engine import RiskEngine

def test_portfolio():
    print("Testing Portfolio Layer...")
    
    # 1. Generate Dummy Data
    dates = pd.date_range("2023-01-01", periods=100)
    df = pd.DataFrame(index=dates)
    df['GOLD'] = 100 + np.random.randn(100).cumsum()
    df['EURUSD'] = 1.0 + np.random.randn(100).cumsum() * 0.01
    df['BTC'] = 20000 + np.random.randn(100).cumsum() * 100
    
    print("Dummy Prices Generated:")
    print(df.tail())
    
    # 2. Test Optimizer
    try:
        opt = PortfolioOptimizer(df)
        print("\nRunning Max Sharpe Optimization...")
        weights, perf = opt.optimize_mean_variance()
        print("Optimal Weights:", weights)
        print("Performance:", perf)
        
        if sum(weights.values()) > 0.99:
             print("SUCCESS: Weights sum to approx 1.0")
        else:
             print("FAIL: Weights do not sum to 1.0")
             
    except Exception as e:
        print(f"Optimizer Failed: {e}")
        
    # 3. Test Risk Engine
    print("\nTesting Risk Engine...")
    risk = RiskEngine(max_daily_drawdown=0.05)
    
    # Allowed Trade
    if risk.check_trade("GOLD", 1000, 10000):
        print("Test 1 Passed: Allowed safe trade.")
    else:
        print("Test 1 Failed: Rejected safe trade.")
        
    # Trigger Drawdown
    risk.update_drawdown(9400, 10000) # 6% DD
    
    # Rejected Trade
    if not risk.check_trade("GOLD", 1000, 10000):
        print("Test 2 Passed: Rejected trade during drawdown.")
    else:
        print("Test 2 Failed: Allowed trade despite max drawdown.")

if __name__ == "__main__":
    test_portfolio()
