from mt5_service import MT5Service
from finviz_service import FinvizService
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class SymbolResolver:
    """
    Intelligent mapper between MT5 Broker Symbols and Finviz Tickers.
    """
    MAPPING = {
        # Commodities
        "GOLD": {"finviz": "GLD", "name": "Gold (SPDR ETF)", "type": "ETF"},
        "XAUUSD": {"finviz": "GLD", "name": "Gold (SPDR ETF)", "type": "ETF"},
        "SILVER": {"finviz": "SLV", "name": "Silver (iShares ETF)", "type": "ETF"},
        "XAGUSD": {"finviz": "SLV", "name": "Silver (iShares ETF)", "type": "ETF"},
        
        # Indices
        "US100": {"finviz": "QQQ", "name": "Nasdaq 100 (Invesco QQQ)", "type": "ETF"},
        "NAS100": {"finviz": "QQQ", "name": "Nasdaq 100 (Invesco QQQ)", "type": "ETF"},
        "US500": {"finviz": "SPY", "name": "S&P 500 (SPDR)", "type": "ETF"},
        "SPX500": {"finviz": "SPY", "name": "S&P 500 (SPDR)", "type": "ETF"},
        
        # Stocks
        "NVDA": {"finviz": "NVDA", "name": "Nvidia Corp", "type": "Stock"},
        "TSLA": {"finviz": "TSLA", "name": "Tesla Inc", "type": "Stock"},
    }

    def resolve(self, mt5_symbol):
        # 1. Direct Map
        if mt5_symbol in self.MAPPING:
            return self.MAPPING[mt5_symbol]
        
        # 2. Fuzzy Map (Remove suffixes like .pro, c, etc.)
        clean_sym = mt5_symbol.replace("Cash", "").replace(".pro", "").replace("c", "")
        if clean_sym in self.MAPPING:
            return self.MAPPING[clean_sym]
            
        # 3. Fallback (Assume it's a stock)
        return {"finviz": clean_sym, "name": clean_sym, "type": "Stock"}

def deep_dive():
    print("\n🔬 TITAN INTELLIGENCE: DEEP DIVE RAPORT 🔬")
    print("===========================================")
    
    mt5 = MT5Service()
    if not mt5.connect():
        print("MT5 Connection Failed.")
        return

    fv = FinvizService()
    resolver = SymbolResolver()
    
    # Get active Market Watch symbols
    active_symbols = mt5.get_market_watch_symbols()
    
    # Analyze Top 5 interesting ones
    targets = ["GOLD", "US100Cash", "NVDA", "SILVER"]
    
    for t in targets:
        # Find real MT5 symbol
        real_mt5 = None
        for s in active_symbols:
            if t in s or (t == "GOLD" and "XAU" in s):
                real_mt5 = s
                break
        
        if not real_mt5:
            # Try to force it if not in watchlist, just for demo
            real_mt5 = t 
        
        # Resolve to Finviz
        intel = resolver.resolve(real_mt5)
        fv_ticker = intel['finviz']
        
        print(f"\n👉 ASSET: {real_mt5} (Proxy: {fv_ticker})")
        print(f"   Identity: {intel['name']} | Type: {intel['type']}")
        
        # A. MT5 Technicals
        prices = mt5.get_prices([real_mt5])
        if real_mt5 in prices:
            p = prices[real_mt5]
            print(f"   [MT5] Price Action:")
            print(f"     • Current: {p['last']}")
            print(f"     • Spread:  {p['spread']} points")
        
        # B. Finviz Intelligence
        fund = fv.get_ticker_fundamentals(fv_ticker)
        if fund:
            print(f"   [Finviz] Deep Intel:")
            
            # 1. Valuation (Is it cheap?)
            pe = fund.get('P/E', '-')
            print(f"     • Valuation (P/E): {pe} {'(Expensive!)' if pe != '-' and float(pe) > 30 else ''}")
            
            # 2. Institutional Flow (Are big boys buying?)
            rel_vol = fund.get('Rel Volume', '0')
            print(f"     • Rel Volume:      {rel_vol}")
            if float(rel_vol) > 1.5:
                print("       🔥 ALERT: High Institutional Volume Detected!")
            elif float(rel_vol) < 0.7:
                print("       💤 NOTE: Low Volume (Retail only)")
                
            # 3. Sentiment (Are people shorting?)
            short_float = fund.get('Short Float', '0%')
            print(f"     • Short Float:     {short_float}")
            if float(short_float.replace('%','')) > 10:
                print("       ⚠️ WARNING: High Short Interest (Squeeze Risk)")
                
        # C. Narrative (News)
        news = fv.get_ticker_news(fv_ticker)
        if news is not None and len(news) > 0:
            print(f"   [Narrative] Latest Headline:")
            title = news.iloc[0]['Title'] if hasattr(news, 'iloc') else news[0]
            print(f"     • \"{title}\"")
        
        print("   -------------------------------------------")

if __name__ == "__main__":
    deep_dive()
