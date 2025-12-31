"""
FIND CORRECT SYMBOLS
====================
Search by description to find the REAL Gold, Treasury, and S&P symbols.
"""
import MetaTrader5 as mt5

mt5.initialize()
symbols = mt5.symbols_get()

print("SEARCHING FOR GOLD:")
for s in symbols:
    if "GOLD" in s.description.upper() or "XAU" in s.name.upper():
        print(f"  {s.name} : {s.description}")

print("\nSEARCHING FOR S&P 500:")
for s in symbols:
    if "S&P" in s.description.upper() or "US500" in s.name.upper() or "ES" in s.name:
        print(f"  {s.name} : {s.description}")

print("\nSEARCHING FOR TREASURY:")
for s in symbols:
    if "TREASURY" in s.description.upper() or "NOTE" in s.description.upper() or "TU" in s.name:
        print(f"  {s.name} : {s.description}")

mt5.shutdown()
