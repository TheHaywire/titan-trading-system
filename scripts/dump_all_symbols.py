"""
DUMP ALL SYMBOLS
================
Brute force search for Gold.
"""
import MetaTrader5 as mt5

mt5.initialize()
symbols = mt5.symbols_get()

with open("all_symbols_dump.txt", "w", encoding="utf-8") as f:
    for s in symbols:
        f.write(f"{s.name} | {s.description} | {s.path}\n")

print(f"Dumped {len(symbols)} symbols.")
mt5.shutdown()
