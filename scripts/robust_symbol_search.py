import MetaTrader5 as mt5

def find_best_symbols():
    if not mt5.initialize():
        print("MetaTrader5 initialization failed")
        return

    symbols = mt5.symbols_get()
    names = [s.name for s in symbols]
    
    targets = {
        "S&P 500": ["US500", "SP500", "SPX"],
        "Nasdaq 100": ["US100", "NAS100", "USTEC"],
        "Dow Jones": ["US30", "DJI", "DOW"],
        "DAX": ["GER40", "DE40", "DAX"],
        "Gold": ["GOLD", "XAUUSD"],
        "Crude Oil": ["WTI", "OIL", "CL"],
        "Natural Gas": ["NATGAS", "NG"],
        "10Y Bond": ["UST10Y", "ZN", "10Y"],
        "30Y Bond": ["UST30Y", "ZB", "30Y"],
        "Euro": ["EURUSD"],
        "Bitcoin": ["BTCUSD", "BITCOIN"],
    }
    
    results = {}
    for label, keywords in targets.items():
        matches = []
        for kw in keywords:
            for n in names:
                if kw.upper() in n.upper():
                    matches.append(n)
        results[label] = list(set(matches))
        
    for label, matches in results.items():
        print(f"{label}: {matches[:5]}") # Show top 5 matches

    mt5.shutdown()

if __name__ == "__main__":
    find_best_symbols()
