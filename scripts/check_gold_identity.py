"""
CRITICAL SYMBOL IDENTITY CHECK
==============================
Verify if 'HGCOP' is Copper or Gold.
Find the REAL Gold Future.
"""
import MetaTrader5 as mt5

mt5.initialize()

def check(symbol):
    info = mt5.symbol_info(symbol)
    if info:
        print(f"SYMBOL: {symbol}")
        print(f"  Path: {info.path}")
        print(f"  Description: {info.description}")
        print(f"  Currency: {info.currency_base} / {info.currency_profit}")
        print(f"  Contract Size: {info.trade_contract_size}")
        print("-" * 40)
    else:
        print(f"SYMBOL: {symbol} NOT FOUND")

print("Checking 'HGCOP-MAR26' (The suspect)...")
check("HGCOP-MAR26")

print("\nSEARCHING FOR REAL GOLD FUTURES...")
all_syms = mt5.symbols_get()
for s in all_syms:
    # Look for Gold keywords
    if "GOLD" in s.description.upper() or "XAU" in s.name.upper() or "GC" in s.name.upper():
        # Exclude obvious forex spot if possible, look for futures
        print(f"FOUND: {s.name:<15} | {s.description}")

mt5.shutdown()
