from storage_service import init_db, get_session, Symbol, FinvizData
from finviz_service import FinvizService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sync():
    logger.info("Initializing DB...")
    init_db()
    
    svc = FinvizService()
    logger.info("Calling get_screener_results...")
    df = svc.get_screener_results(force_refresh=True)
    
    if df is not None:
        logger.info(f"Got results: {len(df)} rows")
        session = get_session()
        tickers = df['Ticker'].tolist()
        
        for ticker in tickers[:5]: # Just 5 for test
            logger.info(f"Processing {ticker}...")
            s = session.query(Symbol).filter(Symbol.ticker == ticker).first()
            if not s:
                s = Symbol(ticker=ticker, source="Finviz", is_active=1)
                session.add(s)
            
            row = df[df['Ticker'] == ticker].iloc[0]
            f_data = s.finviz_data
            if not f_data:
                f_data = FinvizData(symbol=s)
                session.add(f_data)
                
            f_data.price = float(row['Price'])
            logger.info(f"Updated {ticker} price to {f_data.price}")
            
        session.commit()
        logger.info("Commit successful!")
        session.close()
    else:
        logger.error("Failed to get screener results.")

if __name__ == "__main__":
    test_sync()
