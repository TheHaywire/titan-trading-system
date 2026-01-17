import requests
import pandas as pd
from io import StringIO

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

url = "https://finviz.com/screener.ashx?v=311&o=-volumereleative"  # Technical view for Relative Volume
# wait, v=311 is technical. Relative volume is Rel Vol in technical view usually.
url = "https://finviz.com/screener.ashx?v=311"
response = requests.get(url, headers=headers, timeout=10)
tables = pd.read_html(StringIO(response.text))
for df in tables:
    if 'Ticker' in df.columns.tolist() or any('Ticker' in str(c) for c in df.columns):
        print("Columns Found:", df.columns.tolist())
        break
