from titan_system.data.ingest_mt5 import ingest_history
from titan_system.data.database import SessionLocal, init_db
from titan_system.data.models import OHLCV, Ticker

def test_ingestion():
    print("Initializing Database...")
    init_db()
    
    # Test with "GOLD" which might be "XAUUSD" on some brokers
    symbol = "GOLD"
    print(f"Testing ingestion for {symbol} (expecting auto-resolution)...")
    
    # Ingest 30 days of H1 data
    ingest_history(symbol, "H1", days=30)
    
    # Verify
    db = SessionLocal()
    try:
        # We don't know the resolved symbol name easily without querying, 
        # but ingest should have printed it.
        # Let's search for any ticker with GOLD or XAU
        tickers = db.query(Ticker).all()
        target_ticker = None
        for t in tickers:
            if "GOLD" in t.symbol.upper() or "XAU" in t.symbol.upper():
                target_ticker = t
                break
        
        if not target_ticker:
            print(f"FAILED: No related ticker found in DB.")
            return
            
        count = db.query(OHLCV).filter(OHLCV.ticker_id == target_ticker.id).count()
        print(f"Found {count} H1 records for resolved symbol '{target_ticker.symbol}' in DB.")
        
        if count > 0:
            last_record = db.query(OHLCV).filter(OHLCV.ticker_id == target_ticker.id).order_by(OHLCV.timestamp.desc()).first()
            first_record = db.query(OHLCV).filter(OHLCV.ticker_id == target_ticker.id).order_by(OHLCV.timestamp.asc()).first()
            print(f"First record: {first_record.timestamp}")
            print(f"Last record: {last_record.timestamp}")
            print("SUCCESS: Data ingestion verification passed.")
        else:
            print("WARNING: No records found.")
            
    finally:
        db.close()

if __name__ == "__main__":
    test_ingestion()
