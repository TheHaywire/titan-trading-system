"""
SYMBOL RESOLVER
===============
Maps MT5 broker symbols to their Finviz proxy tickers.
"""

class SymbolResolver:
    """
    Intelligent mapper between MT5 Broker Symbols and Finviz Tickers.
    """
    MAPPING = {
        # Commodities -> ETF Proxies
        "GOLD": {"finviz": "GLD", "name": "Gold (SPDR ETF)", "type": "ETF"},
        "XAUUSD": {"finviz": "GLD", "name": "Gold (SPDR ETF)", "type": "ETF"},
        "SILVER": {"finviz": "SLV", "name": "Silver (iShares ETF)", "type": "ETF"},
        "XAGUSD": {"finviz": "SLV", "name": "Silver (iShares ETF)", "type": "ETF"},
        
        # Indices -> ETF Proxies
        "US100": {"finviz": "QQQ", "name": "Nasdaq 100 (Invesco QQQ)", "type": "ETF"},
        "US100Cash": {"finviz": "QQQ", "name": "Nasdaq 100 (Invesco QQQ)", "type": "ETF"},
        "NAS100": {"finviz": "QQQ", "name": "Nasdaq 100 (Invesco QQQ)", "type": "ETF"},
        "US500": {"finviz": "SPY", "name": "S&P 500 (SPDR)", "type": "ETF"},
        "SPX500": {"finviz": "SPY", "name": "S&P 500 (SPDR)", "type": "ETF"},
        "US30": {"finviz": "DIA", "name": "Dow Jones (SPDR)", "type": "ETF"},
        "US30Cash": {"finviz": "DIA", "name": "Dow Jones (SPDR)", "type": "ETF"},
        
        # Direct Stocks
        "NVDA": {"finviz": "NVDA", "name": "Nvidia Corp", "type": "Stock"},
        "TSLA": {"finviz": "TSLA", "name": "Tesla Inc", "type": "Stock"},
        "AAPL": {"finviz": "AAPL", "name": "Apple Inc", "type": "Stock"},
        "MSFT": {"finviz": "MSFT", "name": "Microsoft Corp", "type": "Stock"},
    }

    def resolve(self, mt5_symbol):
        """
        Resolve MT5 symbol to Finviz ticker.
        Returns dict with finviz ticker, name, and type.
        """
        # 1. Direct Map
        if mt5_symbol in self.MAPPING:
            return self.MAPPING[mt5_symbol]
        
        # 2. Fuzzy Map (Remove broker suffixes)
        clean_sym = mt5_symbol.replace("Cash", "").replace(".pro", "").replace("c", "").replace("_", "")
        if clean_sym in self.MAPPING:
            return self.MAPPING[clean_sym]
        
        # 3. Check for Gold/Silver variations
        if "XAU" in mt5_symbol.upper():
            return self.MAPPING["GOLD"]
        if "XAG" in mt5_symbol.upper():
            return self.MAPPING["SILVER"]
            
        # 4. Fallback (Assume it's a stock ticker)
        return {"finviz": mt5_symbol, "name": mt5_symbol, "type": "Stock"}
