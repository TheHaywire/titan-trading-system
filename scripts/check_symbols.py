import MetaTrader5 as mt5
import pandas as pd

def check_symbols():
    if not mt5.initialize():
        print("MT5 Initialize failed")
        return

    print("Searching for Gold-related symbols...")
    symbols = mt5.symbols_get()
    
    found = []
    for s in symbols:
        if "GOLD" in s.name.upper() or "XAU" in s.name.upper():
            found.append(s.name)
            print(f"Found: {s.name} (Path: {s.path})")
            
    if not found:
        print("No symbols matching GOLD or XAU found. Listing first 10 symbols:")
        for s in symbols[:10]:
            print(s.name)
            
    mt5.shutdown()

if __name__ == "__main__":
    check_symbols()
