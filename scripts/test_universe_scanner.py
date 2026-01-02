
import sys
import os
import logging

# Add project root to path
sys.path.append(os.getcwd())

from scripts.launch import UniverseScanner
import MetaTrader5 as mt5

# Setup basic logging to console
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_scanner():
    print("Initializing Universe Scanner Test...")
    scanner = UniverseScanner()
    
    print("Running Full Universe Scan (This may take a moment)...")
    candidates = scanner.scan_full_universe()
    
    print("-" * 50)
    print(f"SCAN COMPLETE.")
    print(f"Total Active Candidates Found: {len(candidates)}")
    print("-" * 50)
    
    if candidates:
        print("Top 10 Candidates:")
        for sym in candidates[:10]:
            print(f"- {sym}")
    else:
        print("No candidates found (check market hours or filters).")

if __name__ == "__main__":
    test_scanner()
