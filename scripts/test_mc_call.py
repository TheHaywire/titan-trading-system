import MetaTrader5 as mt5
import sys
import os

sys.path.append(os.getcwd())
from scripts.risk_monte_carlo import get_monte_carlo_results

def test_call():
    if not mt5.initialize():
        print("Init failed")
        return
    
    print("Testing get_monte_carlo_results(standalone=False)...")
    res = get_monte_carlo_results(standalone=False)
    print(f"Result type: {type(res)}")
    print(f"Results: {res}")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_call()
