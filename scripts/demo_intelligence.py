from mt5_service import MT5Service
from finviz_service import FinvizService
import json

def demo_value():
    print("Fetching Ultimate Intelligence Report...\n")
    
    mt5 = MT5Service()
    if not mt5.connect():
        print("MT5 Connect Failed")
        return

    fv = FinvizService()

    # Define our "Ultimate" mappings
    # MT5 Symbol (The Asset) -> Finviz Proxy (The Sentiment/Volume Source)
    pairs = [
        {"mt5": "GOLD", "finviz": "GLD", "name": "Gold"},
        {"mt5": "SILVER", "finviz": "SLV", "name": "Silver"},
        {"mt5": "NVDA", "finviz": "NVDA", "name": "Nvidia (Stock)"}
    ]

    available_symbols = mt5.get_market_watch_symbols()

    for item in pairs:
        mt5_sym = item['mt5']
        
        # Handle broker variations (e.g., XAUUSD vs GOLD)
        real_mt5_sym = None
        for s in available_symbols:
            if mt5_sym in s or (mt5_sym == "GOLD" and "XAU" in s) or (mt5_sym == "SILVER" and "XAG" in s):
                real_mt5_sym = s
                break
        
        if not real_mt5_sym:
            print(f"Skipping {item['name']} (Not found in Market Watch)")
            continue

        print(f"==================================================")
        print(f" 🔍 ANALYSIS: {item['name']}")
        print(f"==================================================")

        # 1. THE MUSCLE (MT5)
        prices = mt5.get_prices([real_mt5_sym])
        if real_mt5_sym in prices:
            p = prices[real_mt5_sym]
            print(f"📊 [MT5] RAW DATA ({real_mt5_sym})")
            print(f"   • Price:   {p['last']}")
            print(f"   • Spread:  {p['spread']}")
            print(f"   • Action:  Live Bid/Ask ticking...")
        
        # 2. THE BRAIN (Finviz)
        fv_sym = item['finviz']
        print(f"🧠 [FINVIZ] SMART CONTEXT (Proxy: {fv_sym})")
        
        # Fundamentals
        fund = fv.get_ticker_fundamentals(fv_sym)
        if fund:
            rel_vol = fund.get('Rel Volume', 'N/A')
            print(f"   • Relative Volume: {rel_vol}")
            print(f"     -> Meaning: {'🔥 INSTITUTIONAL ACTIVITY' if rel_vol != 'N/A' and float(rel_vol) > 1.5 else '😴 Retail Noise'}")
            
            inst_own = fund.get('Inst Own', 'N/A')
            print(f"   • Institutional Own: {inst_own}")
            
            change = fund.get('Change', 'N/A')
            print(f"   • Session Change: {change}")

        # News
        print(f"   • Recent Intel:")
        news = fv.get_ticker_news(fv_sym)
        if news is not None and len(news) > 0:
            count = 0
            if hasattr(news, 'iloc'):
                for i in range(len(news)):
                    title = news.iloc[i]['Title']
                    link = news.iloc[i]['Link']
                    print(f"     - {title}")
                    count += 1
                    if count >= 2: break
            else:
                 for item in news[:2]:
                    print(f"     - {item}")
        else:
            print("     - No recent headlines found.")
        
        print("\n")

if __name__ == "__main__":
    demo_value()
