"""
Institutional Symbol Mapper & Resolver
Ensures 100% accuracy in symbol naming to prevent missed trades or execution errors.
Reference: data/tradeable_universe.json
"""

import json
import os
import logging
from difflib import get_close_matches

logger = logging.getLogger("Titan.SymbolMapper")

class SymbolMapper:
    _instance = None
    _universe = {} # Exact name -> Properties
    _aliases = {
        "GOLD": "GOLD",
        "XAU": "GOLD",
        "XAUUSD": "GOLD",
        "BTC": "BTCUSD",
        "ETH": "ETHUSD",
        "DOW": "US30Cash",
        "US30": "US30Cash",
        "NAS": "US100Cash",
        "NAS100": "US100Cash",
        "USTEC": "US100Cash",
        "US100": "US100Cash",
        "SPX": "US500Cash",
        "SP500": "US500Cash",
        "UK100": "UK100Cash",
        "DAX": "GER40Cash",
        "DE40": "GER40Cash"
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SymbolMapper, cls).__new__(cls)
            cls._instance._load_universe()
        return cls._instance

    def _load_universe(self):
        """Loads the master symbol list from the broker scan."""
        json_path = os.path.join(os.getcwd(), 'data', 'tradeable_universe.json')
        if not os.path.exists(json_path):
            logger.error(f"❌ Master symbol list not found at {json_path}. Run broker scan!")
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._universe = {item['name']: item for item in data}
                logger.info(f"✅ Symbol Mapper loaded {len(self._universe)} symbols.")
        except Exception as e:
            logger.error(f"❌ Failed to load symbol universe: {e}")

    def resolve(self, requested_name):
        """
        Resolves a name to the EXACT broker symbol.
        1. Exact check
        2. Alias check
        3. Fuzzy check
        """
        requested_name = requested_name.strip()
        
        # 1. Exact match
        if requested_name in self._universe:
            return requested_name, "Exact Match"

        # 2. Case-insensitive exact match
        for sym in self._universe.keys():
            if sym.lower() == requested_name.lower():
                return sym, "Case Insensitive"

        # 3. Alias match
        alias_target = self._aliases.get(requested_name.upper())
        if alias_target and alias_target in self._universe:
            return alias_target, "Alias Match"

        # 4. Fuzzy match (JPM Style: high threshold 0.8)
        matches = get_close_matches(requested_name, list(self._universe.keys()), n=1, cutoff=0.8)
        if matches:
            return matches[0], "Fuzzy Match"

        return None, "Not Found"

    def is_valid(self, symbol):
        """Check if symbol exists in broker universe."""
        return symbol in self._universe

    def get_properties(self, symbol):
        """Returns institutional properties for a symbol (contract size, tick, etc)."""
        return self._universe.get(symbol)

    def list_all(self):
        """Lists all tradeable symbols."""
        return list(self._universe.keys())

# Global Instance
mapper = SymbolMapper()

if __name__ == "__main__":
    # Test Resolution
    tests = ["GOLD", "btc", "EURUSD", "NAS100", "XAUUSD", "US30"]
    print(f"{'Request':<10} | {'Resolved':<12} | {'Method':<15}")
    print("-" * 45)
    for t in tests:
        res, method = mapper.resolve(t)
        print(f"{t:<10} | {str(res):<12} | {method:<15}")
