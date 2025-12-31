
import MetaTrader5 as mt5
import pandas as pd

if not mt5.initialize():
    print("Init failed")
    quit()

s = "EURDKK"
info = mt5.symbol_info(s)

if info:
    print(f"Symbol: {s}")
    print(f"Volume Min: {info.volume_min}")
    print(f"Volume Step: {info.volume_step}")
    print(f"Filling Mode (Flags): {info.filling_mode}")
    print(f"  Matches IOC? {bool(info.filling_mode & mt5.SYMBOL_FILLING_IOC)}")
    print(f"  Matches FOK? {bool(info.filling_mode & mt5.SYMBOL_FILLING_FOK)}")
else:
    print("Symbol not found")

mt5.shutdown()
