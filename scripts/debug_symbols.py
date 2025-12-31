"""
DEBUG SYMBOL MAPPING
====================
Compare simple mapping (Previous Success) vs Complex mapping (Failed Walk-Forward)
"""
import MetaTrader5 as mt5

mt5.initialize()
symbols = mt5.symbols_get()

targets = ['GC', 'TU', 'ES']

print(f"{'Target':<10} | {'Simple Match (Success)':<30} | {'Complex Match (Fail)':<30}")
print("-" * 80)

for t in targets:
    # Logic from test_chan_futures.py (Success)
    simple = [s.name for s in symbols if t in s.name]
    simple_match = simple[0] if simple else "NONE"
    
    # Logic from walk_forward_futures.py (Fail)
    complex_list = [s.name for s in symbols if t in s.name and ('FUT' in s.name or '.' in s.name)]
    complex_match = complex_list[0] if complex_list else (simple[0] if simple else "NONE")
    
    # Logic to find "Best" match (e.g. avoiding Copper for GC)
    # GC often matches HGCOP (Copper). We want Gold.
    # Look for "Gold" in description
    gold_candidates = [s.name for s in symbols if 'GOLD' in s.path.upper() or 'GOLD' in s.description.upper()]
    
    print(f"{t:<10} | {simple_match:<30} | {complex_match:<30}")
    
print("\nSpecific Checks:")
# Check what 'GC' actually maps to in Simple mode
gc_simple = [s for s in symbols if 'GC' in s.name]
for s in gc_simple[:5]:
    print(f"  {s.name} ({s.description})")

mt5.shutdown()
