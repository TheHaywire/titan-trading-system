import MetaTrader5 as mt5
import pandas as pd

if not mt5.initialize():
    print("MT5 initialization failed")
    quit()

symbols = mt5.symbols_get()
if symbols is None:
    print("No symbols found")
else:
    print(f"Total symbols found: {len(symbols)}")
    # Print a few to see naming convention
    symbol_names = [s.name for s in symbols]
    print("Sample symbols:", symbol_names[:20])
    
    # Check for specific ones we need
    targets = ["US100", "US500", "GOLD", "XAUUSD", "EURUSD", "GER40", "DE40", "ZN", "ZB"]
    print("\nTarget Check:")
    for t in targets:
        matches = [s for s in symbol_names if t in s]
        print(f"{t}: {matches}")

mt5.shutdown()
