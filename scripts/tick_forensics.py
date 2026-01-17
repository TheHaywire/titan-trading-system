"""
DEEP TICK FORENSICS & ALPHA RECON
=================================
Analyzes REAL TICK DATA and REAL DEAL HISTORY from the MT5 terminal
to identify high-probability edges that actually work on this broker (XMGlobal).
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [FORENSICS] %(message)s')
logger = logging.getLogger("TickForensics")

def analyze_tick_microstructure(symbol="GOLD"):
    """Analyze real tick volatility and spread dynamics."""
    logger.info(f"Analyzing micro-structure for {symbol}...")
    
    if not mt5.initialize():
        logger.error("MT5 Init Failed")
        return None
    
    # 1. Fetch Ticks (Last 50,000 ticks)
    ticks = mt5.copy_ticks_from(symbol, datetime.now() - timedelta(hours=24), 50000, mt5.COPY_TICKS_ALL)
    if ticks is None:
        logger.error(f"Could not fetch ticks for {symbol}")
        return None
    
    df = pd.DataFrame(ticks)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['spread'] = (df['ask'] - df['bid'])
    
    # Analysis
    avg_spread = df['spread'].mean()
    volatility = df['bid'].pct_change().std() * np.sqrt(1000) # Micro-vol
    
    # Identify tick streaks (institutional momentum)
    df['price_change'] = df['bid'].diff()
    df['streak'] = (df['price_change'] > 0).astype(int).groupby((df['price_change'] <= 0).cumsum()).cumsum()
    max_streak = df['streak'].max()
    
    logger.info(f"--- {symbol} MICRO-STATS ---")
    logger.info(f"  Avg Spread:  {avg_spread:.5f}")
    logger.info(f"  Micro-Vol:   {volatility:.5f}")
    logger.info(f"  Max Tick Streak: {max_streak} consecutive bids")
    
    # 2. Analyze Deal History (Real Edge Verification)
    deals = mt5.history_deals_get(datetime.now() - timedelta(days=30), datetime.now())
    if deals:
        df_deals = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        df_deals = df_deals[df_deals['profit'] != 0] # Filter for closed trades
        
        if not df_deals.empty:
            best_hour = pd.to_datetime(df_deals['time'], unit='s').dt.hour.value_counts().idxmax()
            avg_profit = df_deals['profit'].mean()
            logger.info(f"--- HISTORICAL DEAL STATS ---")
            logger.info(f"  Avg Real PnL: ${avg_profit:.2f}")
            logger.info(f"  Most Active Hour: {best_hour}:00")
            
    mt5.shutdown()

if __name__ == "__main__":
    analyze_tick_microstructure("GOLD")
    analyze_tick_microstructure("EURUSD")
