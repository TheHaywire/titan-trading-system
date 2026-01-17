"""
Liquid Watchlist Generator
Scans MT5 for tradeable symbols with tight spreads
"""
import MetaTrader5 as mt5
import json

mt5.initialize()

# Get ALL symbols
all_symbols = mt5.symbols_get()
print(f'Total symbols in MT5: {len(all_symbols)}')

# Filter for liquid symbols
liquid_symbols = []
for sym in all_symbols:
    info = mt5.symbol_info(sym.name)
    if info and info.trade_mode == 4:  # Full trading enabled
        if info.spread < 100:  # Tight spread
            liquid_symbols.append({
                'symbol': sym.name,
                'spread': info.spread,
                'description': sym.description
            })

# Sort by spread
liquid_symbols.sort(key=lambda x: x['spread'])

print(f'\nLiquid symbols (spread < 100): {len(liquid_symbols)}')
print('\nTop 30 most liquid:')
for s in liquid_symbols[:30]:
    print(f"  {s['symbol']}: spread={s['spread']}")

# Save to file
with open('config/liquid_watchlist.json', 'w') as f:
    json.dump(liquid_symbols, f, indent=2)

print(f'\nSaved {len(liquid_symbols)} symbols to config/liquid_watchlist.json')
mt5.shutdown()
