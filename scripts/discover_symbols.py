"""
Symbol Discovery Tool
Finds the correct symbol names for major assets on this broker.
"""
import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings

def find_symbols():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    print("SEARCHING FOR TRADABLE SYMBOLS...")
    all_symbols = mt5.symbols_get()
    names = [s.name for s in all_symbols]
    
    # Keyword search
    targets = {
        "GOLD": ["GOLD", "XAUUSD", "XAU_USD"],
        "SILVER": ["SILVER", "XAGUSD", "XAG_USD"],
        "NASDAQ": ["US100", "NAS100", "USTEC"],
        "S&P": ["US500", "SPX500", "SP500"],
        "DOW": ["US30", "DJ30", "WALLST"],
        "DAX": ["DE40", "DAX40", "GER40"],
        "BTC": ["BTCUSD", "BITCOIN", "BTC_USD"],
        "ETH": ["ETHUSD", "ETHEREUM"],
        "EURUSD": ["EURUSD", "EUR_USD"],
        "GBPUSD": ["GBPUSD"],
        "USDJPY": ["USDJPY"],
    }
    
    found_map = {}
    
    for category, potential_names in targets.items():
        found = None
        for p in potential_names:
            # Check exact match or partial match
            matches = [n for n in names if p in n]
            if matches:
                 # Prefer exact match
                 if p in matches: found = p
                 else: found = matches[0]
                 break
        
        if found:
            print(f"✅ {category}: Found '{found}'")
            found_map[category] = found
        else:
            print(f"❌ {category}: Not Found")
            
    mt5.shutdown()
    return found_map

if __name__ == "__main__":
    find_symbols()
