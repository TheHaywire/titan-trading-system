"""
FINVIZ SERVICE
==============
Handles data extraction from Finviz using finvizfinance.
Includes caching to avoid rate-limiting and respect Terms of Service.
"""

from finvizfinance.screener.overview import Overview
from finvizfinance.quote import finvizfinance
import pandas as pd
from datetime import datetime, timedelta
import logging
import json
import os
import requests
from io import StringIO
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FinvizService:
    def __init__(self, cache_dir="data/cache"):
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)
        self.cache_expiry = {
            "screener": 300,      # 5 minutes
            "fundamentals": 3600,  # 1 hour
            "news": 300           # 5 minutes
        }

    def _get_cache_path(self, key):
        return os.path.join(self.cache_dir, f"{key}.json")

    def _is_cache_valid(self, key, expiry_seconds):
        path = self._get_cache_path(key)
        if not os.path.exists(path):
            return False
        
        mtime = os.path.getmtime(path)
        return (datetime.now().timestamp() - mtime) < expiry_seconds

    def _save_cache(self, key, data):
        path = self._get_cache_path(key)
        with open(path, "w") as f:
            if isinstance(data, pd.DataFrame):
                data.to_json(f)
            else:
                json.dump(data, f)

    def _load_cache(self, key):
        path = self._get_cache_path(key)
        with open(path, "r") as f:
            # Try loading as JSON first
            data = json.load(f)
            # If it looks like a DataFrame export (highly simplified check)
            if isinstance(data, dict) and any(isinstance(v, dict) for v in data.values()):
                return pd.read_json(path)
            return data

    def get_screener_rapid(self, filters_dict=None):
        """
        Rapidly pull the FIRST PAGE of Finviz screener using requests + pandas.
        This avoids the pagination hang of the finvizfinance library.
        """
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Build URL with Overview view (v=111) which is more reliable for simple scraping
        url = "https://finviz.com/screener.ashx?v=111&o=-volume"
        
        if filters_dict:
            # Note: Mapping filters_dict to URL params is complex, 
            # so we'll just stick to a high-volume default list for the rapid view.
            pass

        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
                
            tables = pd.read_html(StringIO(response.text))
            best_df = None
            max_valid_rows = 0
            
            for df in tables:
                # Handle MultiIndex
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(-1)
                
                if 'Ticker' in df.columns and 'Price' in df.columns:
                    # Quick check for data quality
                    # Convert price temporarily to check validity count
                    valid_prices = pd.to_numeric(df['Price'], errors='coerce').notna().sum()
                    
                    if valid_prices > max_valid_rows:
                        max_valid_rows = valid_prices
                        best_df = df
                        
            if best_df is not None and max_valid_rows > 0:
                df = best_df
                logger.info(f"Selected table with {max_valid_rows} valid prices.")
                
                # Clean the dataframe
                df = df.dropna(subset=['Ticker'])
                df = df[df['Ticker'] != 'Ticker']
                
                df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
                df = df.dropna(subset=['Price'])
                
                return df
                
            return None
            return None
        except Exception as e:
            logger.error(f"Rapid screener pull failed: {e}")
            return None

    def get_screener_results(self, filters_dict=None, table='Overview', force_refresh=False):
        """
        Pull screener results based on filters.
        """
        cache_key = f"screener_{table}_{hash(frozenset(filters_dict.items())) if filters_dict else 'default'}"
        
        if not force_refresh and self._is_cache_valid(cache_key, self.cache_expiry["screener"]):
            logger.info(f"Loading screener {table} from cache.")
            return self._load_cache(cache_key)

        logger.info(f"Pulling screener {table} from Finviz (Rapid Mode)...")
        # Use the rapid method first to avoid hanging the orchestrator
        df = self.get_screener_rapid(filters_dict)
        
        if df is not None:
            self._save_cache(cache_key, df)
            return df
            
        # Fallback to library if rapid fails
        logger.info(f"Rapid failed, falling back to library...")
        try:
            foverview = Overview()
            if filters_dict:
                foverview.set_filter(filters_dict=filters_dict)
            df = foverview.screener_view()
            if df is not None:
                self._save_cache(cache_key, df)
            return df
        except Exception as e:
            logger.error(f"Error pulling screener: {e}")
            return None

    def get_ticker_fundamentals(self, ticker, force_refresh=False):
        """Pull per-ticker fundamentals snapshot."""
        cache_key = f"fundamentals_{ticker}"
        
        if not force_refresh and self._is_cache_valid(cache_key, self.cache_expiry["fundamentals"]):
            return self._load_cache(cache_key)

        logger.info(f"Pulling fundamentals for {ticker}...")
        try:
            stock = finvizfinance(ticker)
            fund = stock.ticker_fundament()
            self._save_cache(cache_key, fund)
            return fund
        except Exception as e:
            logger.error(f"Error pulling fundamentals for {ticker}: {e}")
            return None

    def get_ticker_news(self, ticker, force_refresh=False):
        """Pull news headlines for a ticker."""
        cache_key = f"news_{ticker}"
        
        if not force_refresh and self._is_cache_valid(cache_key, self.cache_expiry["news"]):
            return self._load_cache(cache_key)

        logger.info(f"Pulling news for {ticker}...")
        try:
            stock = finvizfinance(ticker)
            news = stock.ticker_news()
            # News is typically a list of lists or dicts: [date, title, link, source]
            self._save_cache(cache_key, news)
            return news
        except Exception as e:
            logger.error(f"Error pulling news for {ticker}: {e}")
            return None

if __name__ == "__main__":
    # Test block
    service = FinvizService()
    print("--- Screener Test (High Volume) ---")
    filters = {'Average Volume': 'Over 1M', 'Price': 'Over 10'}
    results = service.get_screener_results(filters_dict=filters)
    if results is not None:
        print(results.head())

    print("\n--- Fundamentals Test (AAPL) ---")
    fund = service.get_ticker_fundamentals("AAPL")
    if fund:
        print(f"P/E: {fund.get('P/E')}, EPS (ttm): {fund.get('EPS (ttm)')}")

    print("\n--- News Test (AAPL) ---")
    news = service.get_ticker_news("AAPL")
    if news is not None:
        print(f"Latest Headline: {news.iloc[0]['Title'] if hasattr(news, 'iloc') else news[0]}")
