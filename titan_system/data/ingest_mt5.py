import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta, timezone
from titan_system.data.database import SessionLocal, init_db
from titan_system.data.models import Ticker, OHLCV
from sqlalchemy.orm import Session
from sqlalchemy import select
import sys

# Constants
TIMEFRAMES = {
    'M1': mt5.TIMEFRAME_M1,
    'M5': mt5.TIMEFRAME_M5,
    'M15': mt5.TIMEFRAME_M15,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
}

def connect_mt5():
    if not mt5.initialize():
        print("initialize() failed, error code =", mt5.last_error())
        return False
    return True

def resolve_symbol(symbol: str) -> str:
    """
    Attempts to find the correct symbol name from MT5.
    Returns the correct symbol name or None.
    """
    # 1. Direct check
    if mt5.symbol_info(symbol):
        return symbol

    print(f"Symbol '{symbol}' not found directly. Searching...")
    
    # 2. Search all symbols
    all_symbols = mt5.symbols_get()
    for s in all_symbols:
        if s.name == symbol: # Exact match match case insensitive?
            return s.name
        if symbol.upper() in s.name.upper():
            # Heuristic: return the shortest match that contains the string
            # e.g. "GOLD" might match "GOLD", "GOLD.m", "XAUUSD"
            pass

    # 3. Smart Mapping
    common_mappings = {
        "GOLD": ["XAUUSD", "GOLD", "XAUUSD.mic"],
        "BTC": ["BTCUSD", "BTCUSD.mic"],
        "EURUSD": ["EURUSD", "EURUSD.mic"]
    }
    
    for k, candidates in common_mappings.items():
        if symbol.upper() in k:
            for cand in candidates:
                if mt5.symbol_info(cand):
                    print(f"Resolved '{symbol}' to '{cand}'")
                    return cand

    # 4. Fuzzy search in list
    matches = [s.name for s in all_symbols if symbol.upper() in s.name.upper()]
    if matches:
        # Prefer exact generic matches (e.g. XAUUSD over XAUUSD.pro)
        best = min(matches, key=len) 
        print(f"Fuzzy resolved '{symbol}' to '{best}' (Candidates: {matches[:3]})")
        return best

    return None

def get_or_create_ticker(session: Session, symbol: str) -> Ticker:
    ticker = session.query(Ticker).filter(Ticker.symbol == symbol).first()
    if not ticker:
        symbol_info = mt5.symbol_info(symbol)
        market_type = "UNKNOWN"
        if symbol_info:
            path = symbol_info.path.upper()
            if "FOREX" in path: market_type = "FOREX"
            elif "CRYPTO" in path: market_type = "CRYPTO"
            elif "INDEX" in path: market_type = "INDEX"
            elif "COMMOD" in path or "SPOT" in path: market_type = "COMMODITY"
            elif "STOCK" in path: market_type = "STOCK"
        
        ticker = Ticker(symbol=symbol, market_type=market_type)
        session.add(ticker)
        session.commit()
        session.refresh(ticker)
    return ticker

def ingest_history(input_symbol: str, timeframe: str, days: int = 30):
    if not connect_mt5():
        return

    # 1. Resolve Symbol
    symbol = resolve_symbol(input_symbol)
    if not symbol:
        print(f"ERROR: Could not resolve symbol '{input_symbol}' in MT5.")
        return

    # 2. Ensure selected
    if not mt5.symbol_select(symbol, True):
        print(f"ERROR: Failed to select '{symbol}' in Market Watch.")
        return

    db: Session = SessionLocal()
    try:
        current_ticker = get_or_create_ticker(db, symbol)
        
        utc_to = datetime.now(timezone.utc)
        utc_from = utc_to - timedelta(days=days)
        tf_mt5 = TIMEFRAMES.get(timeframe)

        print(f"Fetching {timeframe} data for {symbol} ({utc_from.date()} to {utc_to.date()})...")
        
        rates = mt5.copy_rates_range(symbol, tf_mt5, utc_from, utc_to)
        
        # Fallback
        if rates is None or len(rates) == 0:
            print("Range fetch empty. Trying last 1000 bars...")
            rates = mt5.copy_rates_from_pos(symbol, tf_mt5, 0, 1000)

        if rates is None or len(rates) == 0:
            print(f"No data received for {symbol}.")
            return

        print(f"Received {len(rates)} bars. Saving...")

        # Bulk Process
        # 1. Get existing timestamps to avoid attempting inserts
        # Convert MT5 timestamps to datetime for comparison
        # Note: We must ensure consistency. database stores naive or aware?
        # We will use UTC-aware datetimes in DB for clarity, or Naive representing UTC.
        # SQLite doesn't preserve TZ info well, so usually best to store Naive UTC.
        
        # DataFrame is fast
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s') 
        # df['time'] is now naive (since unit='s' is UTC but pandas makes it naive by default)
        
        # Query existing latest to skip
        last_ts_q = db.query(OHLCV.timestamp)\
            .filter(OHLCV.ticker_id == current_ticker.id, OHLCV.timeframe == timeframe)\
            .order_by(OHLCV.timestamp.desc()).first()
            
        last_ts = last_ts_q[0] if last_ts_q else datetime.min

        # Filter duplicates via Python (simplest for now)
        # We can also query ALL timestamps if dataset is small, but for 30 days it's fine.
        # Better: Filter DF > last_ts (This handles APPEND only)
        # If we are Backfilling gaps, we need check sets.
        
        # Let's use set difference for 100% correctness (slower but safe)
        incoming_timestamps = set(df['time'])
        
        existing_q = db.query(OHLCV.timestamp).filter(
            OHLCV.ticker_id == current_ticker.id, 
            OHLCV.timeframe == timeframe,
            OHLCV.timestamp.in_(incoming_timestamps) # This might be too huge for SQL
        ).all()
        
        existing_timestamps = {r[0] for r in existing_q}
        
        # Actually, `in_` with 50k items is bad. 
        # Strategy: Iterate and check? Too slow.
        # Strategy: Trust Unique Constraint + Ignore?
        # Strategy: Only insert items > last_checked_ts?
        #   - Good for live, bad for random backfill.
        
        # Hybrid:
        # If filling history (days=30), we act as if we are filling gaps?
        # Let's blindly try to add non-existing ones one by one with a quick check? 
        # Or just use the "Upsert" pattern if I had PostgreSQL.
        
        # Let's just do the loop with `exists` check, but optimize variable scope
        
        new_records = []
        for idx, row in df.iterrows():
            ts = row['time'] # is Timestamp object
            
            # Simple check: Is it in our 'existing' set from a recent query?
            # To avoid N+1 queries, we really should fetch the range of existing timestamps
            pass
        
        # Optimized approach:
        # Fetch ALL existing timestamps for this Ticker+TF in the range of min(df) to max(df)
        min_ts, max_ts = df['time'].min(), df['time'].max()
        existing_in_range = db.query(OHLCV.timestamp).filter(
            OHLCV.ticker_id == current_ticker.id,
            OHLCV.timeframe == timeframe,
            OHLCV.timestamp >= min_ts.to_pydatetime(),
            OHLCV.timestamp <= max_ts.to_pydatetime()
        ).all()
        
        existing_set = {r[0] for r in existing_in_range}
        
        to_add = []
        for rate in rates:
            ts_utc = datetime.fromtimestamp(rate['time'], timezone.utc).replace(tzinfo=None)
            
            if ts_utc not in existing_set:
                # Check for NaNs
                o = float(rate['open'])
                h = float(rate['high'])
                l = float(rate['low'])
                c = float(rate['close'])
                v = float(rate['tick_volume'])
                
                # Simple valid check (price > 0)
                if o <= 0 or h <= 0:
                    print(f"Skipping bad data row at {ts_utc}: O={o} H={h}")
                    continue

                to_add.append(OHLCV(
                    ticker_id=current_ticker.id,
                    timeframe=timeframe,
                    timestamp=ts_utc,
                    open=o,
                    high=h,
                    low=l,
                    close=c,
                    volume=v
                ))
                existing_set.add(ts_utc)

        if to_add:
            # Try to bulk save, if fail, fallback to one-by-one to find error
            try:
                db.bulk_save_objects(to_add)
                db.commit()
                print(f"Saved {len(to_add)} new records.")
            except Exception as e:
                db.rollback()
                print(f"Bulk save failed: {e}. Trying iterative save...")
                for item in to_add:
                    try:
                        db.add(item)
                        db.commit()
                    except Exception as inner_e:
                        db.rollback()
                        print(f"Failed to save item {item.timestamp}: {inner_e}")
                        # Break or continue? Continue to save others.
        else:
            print("No new records to save.")

    except Exception as e:
        print(f"Error top level: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        mt5.shutdown()

if __name__ == "__main__":
    init_db()
    if len(sys.argv) > 1:
        ingest_history(sys.argv[1], 'H1', 30)
    else:
        print("Usage: python ingest_mt5.py [SYMBOL]")
