"""Check all available MT5 symbols and categorize them"""
import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

print("🔍 CHECKING ALL AVAILABLE MT5 SYMBOLS\n")
print("="*70)

# Get all symbols
symbols = mt5.symbols_get()

if symbols is None:
    print("❌ Failed to get symbols")
    mt5.shutdown()
    exit()

print(f"Total symbols available: {len(symbols)}\n")

# Categorize
categories = {
    'Forex': [],
    'Indices': [],
    'Commodities': [],
    'Crypto': [],
    'Stocks': [],
    'Futures': [],
    'Other': []
}

for symbol in symbols:
    name = symbol.name
    desc = symbol.description if symbol.description else ""
    
    # Categorize
    if any(x in name for x in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'NZD', 'CAD', 'CHF']):
        if len(name) == 6:  # Standard forex pair
            categories['Forex'].append((name, desc, symbol.trade_tick_size))
    elif any(x in name for x in ['US30', 'US500', 'NAS100', 'GER', 'UK100', 'JPN225', 'AUS200']):
        categories['Indices'].append((name, desc, symbol.trade_tick_size))
    elif any(x in name.upper() for x in ['GOLD', 'SILVER', 'XAU', 'XAG', 'OIL', 'BRENT']):
        categories['Commodities'].append((name, desc, symbol.trade_tick_size))
    elif any(x in name.upper() for x in ['BTC', 'ETH', 'LTC', 'XRP', 'CRYPTO']):
        categories['Crypto'].append((name, desc, symbol.trade_tick_size))
    elif 'STOCK' in desc.upper() or 'SHARE' in desc.upper():
        categories['Stocks'].append((name, desc, symbol.trade_tick_size))
    elif 'FUTURE' in desc.upper() or any(x in name for x in ['.f', '_f', 'FUT']):
        categories['Futures'].append((name, desc, symbol.trade_tick_size))
    else:
        categories['Other'].append((name, desc, symbol.trade_tick_size))

# Print categorized
for category, items in categories.items():
    if items:
        print(f"\n{'='*70}")
        print(f"{category.upper()} ({len(items)} symbols)")
        print(f"{'='*70}")
        
        for name, desc, tick in items[:20]:  # Show first 20
            print(f"  {name:15s} | {desc[:40]:40s} | Tick: {tick}")
        
        if len(items) > 20:
            print(f"  ... and {len(items)-20} more")

# Check for specific futures Chan uses
print(f"\n\n{'='*70}")
print("CHECKING FOR ERNEST CHAN'S FUTURES:")
print(f"{'='*70}")

chan_futures = ['TU', 'ES', 'GC', 'VX', 'CL', 'NG', 'ZN']
for fut in chan_futures:
    found = [s.name for s in symbols if fut in s.name]
    if found:
        print(f"✅ {fut}: {', '.join(found)}")
    else:
        print(f"❌ {fut}: Not available")

# Check for real volume
print(f"\n\n{'='*70}")
print("VOLUME DATA CHECK:")
print(f"{'='*70}")

print("\nChecking if symbols have REAL volume or just tick volume...")

# Test a few symbols
test_symbols = ['EURUSD', 'US500', 'GOLD', 'BTCUSD']
for sym_name in test_symbols:
    sym_info = mt5.symbol_info(sym_name)
    if sym_info:
        # Get some data
        rates = mt5.copy_rates_from_pos(sym_name, mt5.TIMEFRAME_H1, 0, 10)
        if rates is not None and len(rates) > 0:
            df = pd.DataFrame(rates)
            print(f"\n{sym_name}:")
            print(f"  Has volume data: {'tick_volume' in df.columns}")
            print(f"  Has real volume: {'real_volume' in df.columns}")
            if 'tick_volume' in df.columns:
                print(f"  Sample tick_volume: {df['tick_volume'].iloc[-1]}")
            if 'real_volume' in df.columns:
                print(f"  Sample real_volume: {df['real_volume'].iloc[-1]}")

print(f"\n{'='*70}")
print("✅ ANALYSIS COMPLETE")
print(f"{'='*70}\n")

mt5.shutdown()
