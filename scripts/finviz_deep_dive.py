from finvizfinance.quote import finvizfinance
import pandas as pd

def audit_finviz_data():
    print("🔬 FINVIZ ULTIMATE DATA AUDIT 🔬")
    print("================================")
    
    # Use a data-rich ticker
    ticker = "NVDA"
    stock = finvizfinance(ticker)
    
    # 1. FUNDAMENTAL & TECHNICAL (The Screener Data)
    print("\n[Layer 1] Fundamentals & Technicals:")
    try:
        fund = stock.ticker_fundament()
        keys = list(fund.keys())
        # Print in columns
        for i in range(0, len(keys), 3):
            print(f"  {keys[i]:<20} {keys[i+1] if i+1<len(keys) else '':<20} {keys[i+2] if i+2<len(keys) else ''}")
    except Exception as e:
        print(f"Error fetching fundamentals: {e}")

    # 2. INSIDER TRADING
    print("\n[Layer 2] Insider Trading:")
    try:
        insider = stock.ticker_inside_trader()
        if insider is not None:
             print(f"  Columns: {insider.columns.tolist()}")
             print(f"  Sample:\n{insider.head(2).to_string(index=False)}")
    except Exception as e:
        print(f"Error fetching insider: {e}")

    # 3. NEWS & SENTIMENT
    print("\n[Layer 3] News & Sentiment:")
    try:
        news = stock.ticker_news()
        if news is not None:
             print(f"  Type: {type(news)}")
             if hasattr(news, 'columns'):
                 print(f"  Columns: {news.columns.tolist()}")
                 print(f"  Sample:\n{news.head(2).to_string(index=False)}")
             else:
                 print("  Returns list/dict structure.")
    except Exception as e:
        print(f"Error fetching news: {e}")
        
    # 4. ANALYST TARGETS
    print("\n[Layer 4] Analyst Targets:")
    try:
        # Note: finvizfinance might change naming, checking common methods
        description = stock.ticker_description()
        print(f"  Description Length: {len(description)} chars")
        
        # Check output of 'signal' if available (often requires different class)
    except Exception as e:
        print(f"Error fetching miscellaneous: {e}")

if __name__ == "__main__":
    audit_finviz_data()
