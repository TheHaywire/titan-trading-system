import requests
import pandas as pd
from io import StringIO

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

url = "https://finviz.com/screener.ashx?v=111"
print(f"Requesting {url}...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 200:
        # Find the table in the HTML. Finviz screener table is usually the one with class 'screener-table' (which is actually a table with multiple internal tables sometimes)
        # But pandas.read_html can find all tables.
        tables = pd.read_html(StringIO(response.text))
        print(f"Found {len(tables)} tables.")
        # Usually the largest table or one with a specific number of columns
        # Ticker table usually has columns like No., Ticker, Company, Sector, etc.
        for i, df in enumerate(tables):
            if 'Ticker' in df.columns:
                print(f"Table {i} looks like the ticker table!")
                print(df.head())
                break
    else:
        print(f"Failed with status {response.status_code}")
except Exception as e:
    print(f"Error: {e}")
