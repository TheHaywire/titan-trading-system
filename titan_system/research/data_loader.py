import pandas as pd
from sqlalchemy import select
from titan_system.data.database import SessionLocal
from titan_system.data.models import OHLCV, Ticker

def load_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Load data from DB into a Pandas DataFrame compatible with VectorBT.
    Index: Datetime (UTC)
    Columns: Open, High, Low, Close, Volume
    """
    db = SessionLocal()
    try:
        # Find Ticker
        # We handle the 'GOLD' logic by checking substrings if exact match fails
        ticker = db.query(Ticker).filter(Ticker.symbol == symbol).first()
        
        if not ticker:
            # Fallback search
            all_tickers = db.query(Ticker).all()
            for t in all_tickers:
                if symbol in t.symbol or t.symbol in symbol:
                    print(f"Loading data for resolved symbol: {t.symbol}")
                    ticker = t
                    break
        
        if not ticker:
            raise ValueError(f"Symbol {symbol} not found in database.")

        # Query Data
        query = select(OHLCV).filter(
            OHLCV.ticker_id == ticker.id,
            OHLCV.timeframe == timeframe
        ).order_by(OHLCV.timestamp.asc())
        
        # Read with Pandas
        # pd.read_sql is cleaner but requires an engine connection, not session
        # We can extract the engine from the session
        df = pd.read_sql(query, db.bind)
        
        if df.empty:
            print(f"Warning: No data found for {symbol} {timeframe}")
            return pd.DataFrame()

        # formatting
        df.set_index('timestamp', inplace=True)
        df.drop(columns=['id', 'ticker_id', 'timeframe'], inplace=True, errors='ignore')
        
        # Ensure float
        df = df.astype(float)
        
        return df
        
    finally:
        db.close()
