"""
MAIN LOOP / ORCHESTRATOR
========================
Coordinates background data pulls and symbol synchronization.
"""

import sys, os
from datetime import datetime
import time
import logging
from apscheduler.schedulers.background import BackgroundScheduler

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_service import init_db, get_session, Symbol, FinvizData, News, Alert
from mt5_service import MT5Service
from finviz_service import FinvizService
from symbol_resolver import SymbolResolver

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize services
mt5_svc = MT5Service()
finviz_svc = FinvizService()

def sync_symbols():
    """Ensure symbols from MT5 Market Watch are in our DB."""
    logger.info("Syncing symbols from MT5 Market Watch...")
    mt5_symbols = mt5_svc.get_market_watch_symbols()
    
    session = get_session()
    for ticker in mt5_symbols:
        s = session.query(Symbol).filter(Symbol.ticker == ticker).first()
        if not s:
            s = Symbol(ticker=ticker, source="MT5", is_active=1)
            session.add(s)
            logger.info(f"Added new MT5 symbol: {ticker}")
        else:
            s.is_active = 1
            if "MT5" not in s.source:
                s.source = "Both" if "Finviz" in s.source else "MT5"
    
    session.commit()
    session.close()

def refresh_finviz_screener():
    """Pull Finviz screener and update symbol universe."""
    logger.info("Refreshing Finviz screener data...")
    # Example: Top Momentum/Volume filter
    filters = {'Average Volume': 'Over 1M', 'Relative Volume': 'Over 1.5', 'Price': 'Over 5'}
    df = finviz_svc.get_screener_results(filters_dict=filters)
    
    if df is not None:
        session = get_session()
        tickers = df['Ticker'].tolist()
        for ticker in tickers:
            s = session.query(Symbol).filter(Symbol.ticker == ticker).first()
            if not s:
                s = Symbol(ticker=ticker, source="Finviz", is_active=1)
                session.add(s)
                logger.info(f"Added new Finviz symbol: {ticker}")
            else:
                if "Finviz" not in s.source:
                    s.source = "Both" if "MT5" in s.source else "Finviz"
            
            # Update Finviz data snapshot
            matched_rows = df[df['Ticker'] == ticker]
            if matched_rows.empty:
                logger.warning(f"Ticker {ticker} found in index but not in subset. Skipping.")
                continue
                
            row = matched_rows.iloc[0]
            f_data = s.finviz_data
            if not f_data:
                f_data = FinvizData(symbol=s)
                session.add(f_data)
            
            f_data.price = float(row['Price']) if 'Price' in row else None
            # Handle percentage string
            change_str = row['Change'].replace('%', '') if 'Change' in row else '0'
            f_data.change_pct = float(change_str)
            f_data.rel_vol = float(row['Relative Volume']) if 'Relative Volume' in row else None
            f_data.avg_vol = row['Average Volume'] if 'Average Volume' in row else None
            
        session.commit()
        session.close()

def refresh_fundamentals():
    """Periodic deep refresh of fundamentals for active symbols."""
    session = get_session()
    active_symbols = session.query(Symbol).filter(Symbol.is_active == 1).all()
    
    for s in active_symbols[:20]:  # Limit per run to avoid hammering
        logger.info(f"Refreshing fundamentals for {s.ticker}...")
        fund = finviz_svc.get_ticker_fundamentals(s.ticker)
        if fund:
            f_data = s.finviz_data
            if not f_data:
                f_data = FinvizData(symbol=s)
                session.add(f_data)
            
            f_data.pe = float(fund.get('P/E', 0)) if fund.get('P/E', '-') != '-' else None
            f_data.eps_growth = float(fund.get('EPS next 5Y', '0').replace('%', '')) if fund.get('EPS next 5Y', '-') != '-' else None
            f_data.insider_own = float(fund.get('Insider Own', '0').replace('%', '')) if fund.get('Insider Own', '-') != '-' else None
            f_data.short_interest = float(fund.get('Short Float', '0').replace('%', '')) if fund.get('Short Float', '-') != '-' else None
        
        time.sleep(1) # Small delay
    
    session.commit()
    session.close()

def refresh_news():
    """Update news feed."""
    session = get_session()
    # Pull news for symbols we have positions in
    pos = mt5_svc.get_positions()
    pos_tickers = list(set([p['symbol'] for p in pos]))
    
    for ticker in pos_tickers:
        logger.info(f"Checking news for position: {ticker}")
        news_list = finviz_svc.get_ticker_news(ticker)
        # In a real app, we'd compare headlines to avoid duplicates
        # For now, just logging activity
        
    session.close()

def check_alerts():
    """Rule engine for alerts."""
    # Example: "Show alert if a symbol from Screener X has > 2% move in MT5"
    # This would join MT5 live prices with Finviz data
    pass

def check_trading_rules():
    """
    TITAN ALPHA: The Trading Brain.
    Evaluates symbols for high-conviction setups using MT5 + Finviz intelligence.
    """
    logger.info("🧠 Running Trading Rule Engine...")
    
    # Safety: Check if auto-trade is enabled (we'll add this flag later)
    # For now, this runs in "DRY RUN" mode (logs only, no actual trades)
    
    session = get_session()
    resolver = SymbolResolver()
    
    # Get active symbols from Market Watch
    mt5_symbols = mt5_svc.get_market_watch_symbols()
    
    # Limit to top symbols to avoid overload
    target_symbols = [s for s in mt5_symbols if any(
        keyword in s for keyword in ["GOLD", "XAU", "SILVER", "XAG", "US100", "NAS", "NVDA", "TSLA"]
    )][:5]
    
    for mt5_symbol in target_symbols:
        try:
            # 1. RESOLVE: MT5 -> Finviz
            intel = resolver.resolve(mt5_symbol)
            fv_ticker = intel['finviz']
            
            # 2. FETCH: Finviz Intelligence
            fund = finviz_svc.get_ticker_fundamentals(fv_ticker)
            if not fund:
                logger.warning(f"No Finviz data for {fv_ticker}")
                continue
            
            # 3. EXTRACT: Key Metrics
            rel_vol = float(fund.get('Rel Volume', '0'))
            short_float = fund.get('Short Float', '0%').replace('%', '')
            short_float = float(short_float) if short_float != '-' else 0
            pe = fund.get('P/E', '-')
            pe = float(pe) if pe != '-' else 999
            
            # 4. APPLY FILTERS (The "Titan" Rules)
            
            # Filter A: Adrenaline (Volume Validation)
            if rel_vol < 1.0:
                logger.info(f"❌ {mt5_symbol}: SKIP (Rel Vol {rel_vol} < 1.0 - Retail Noise)")
                continue
            
            # Filter B: Value Guard (Don't buy expensive tops)
            if pe > 50:
                logger.info(f"⚠️ {mt5_symbol}: CAUTION (P/E {pe} > 50 - Expensive, pullback only)")
                # In a real system, we'd only take pullback entries here
            
            # Filter C: Squeeze Detector
            if short_float > 15:
                logger.info(f"🚀 {mt5_symbol}: ROCKET FUEL (Short Float {short_float}% - Squeeze Potential)")
                # In a real system, we'd increase target and size
            
            # 5. SIGNAL QUALIFIED
            logger.info(f"✅ {mt5_symbol} ({fv_ticker}): QUALIFIED | Rel Vol: {rel_vol} | Short Float: {short_float}% | P/E: {pe}")
            
            # 6. [DRY RUN] Simulate Trade Decision
            # In production, this would integrate with alpha_signal_producer.py
            # For now, just log that this symbol passed all filters
            
        except Exception as e:
            logger.error(f"Error evaluating {mt5_symbol}: {e}")
    
    session.close()
    logger.info("🧠 Trading Rule Engine Complete.")


def start_orchestrator():
    logger.info("🚀 Starting MT5 Command Center Orchestrator...")
    init_db()
    
    scheduler = BackgroundScheduler()
    
    # 1. Symbol Sync (Every 5 mins)
    scheduler.add_job(sync_symbols, 'interval', minutes=5)
    
    # 2. Screener Refresh (Every 5 mins)
    scheduler.add_job(refresh_finviz_screener, 'interval', minutes=5)
    
    # 3. Fundamentals Refresh (Every 1 hour)
    scheduler.add_job(refresh_fundamentals, 'interval', hours=1)
    
    # 4. News Refresh (Every 10 mins)
    scheduler.add_job(refresh_news, 'interval', minutes=10)
    
    # 5. Trading Rule Engine (Every 60 seconds) - THE BRAIN
    scheduler.add_job(check_trading_rules, 'interval', seconds=60)
    
    # Initial run
    sync_symbols()
    refresh_finviz_screener()
    
    scheduler.start()
    
    try:
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        mt5_svc.disconnect()

if __name__ == "__main__":
    start_orchestrator()
