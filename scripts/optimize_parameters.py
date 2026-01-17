"""
STRATEGY OPTIMIZER (VectorBT)
=============================
Optimizes key strategy parameters for current market conditions.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from titan_system.backtest.fast_backtest import FastBacktester
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Optimizer")

def run_optimization(symbol: str, timeframe: int):
    """
    Runs VectorBT optimization for a symbol.
    """
    logger.info(f"Starting parameter optimization for {symbol}...")
    
    if not mt5.initialize():
        return
        
    backtester = FastBacktester(symbol=symbol, timeframe=timeframe, bars=5000)
    
    # 1. Optimize RSI Strategy
    logger.info("Optimizing RSI Mean Reversion...")
    backtester.test_rsi_strategy()
    best_rsi = backtester.get_best_params('rsi')
    
    # 2. Optimize EMA Crossover
    logger.info("Optimizing EMA Crossover Trend...")
    backtester.test_ema_crossover()
    best_ema = backtester.get_best_params('ema')
    
    # 3. Optimize Bollinger Bands
    logger.info("Optimizing Bollinger Bands...")
    backtester.test_bollinger_bands()
    best_bb = backtester.get_best_params('bollinger')
    
    logger.info("=" * 40)
    logger.info(f"OPTIMIZATION RESULTS FOR {symbol}")
    logger.info("=" * 40)
    logger.info(f"RSI: {best_rsi}")
    logger.info(f"EMA: {best_ema}")
    logger.info(f"BB:  {best_bb}")
    
    mt5.shutdown()
    return {
        'rsi': best_rsi,
        'ema': best_ema,
        'bb': best_bb
    }

if __name__ == "__main__":
    run_optimization("GOLD", "H1")
