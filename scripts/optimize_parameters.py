import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import itertools
from concurrent.futures import ProcessPoolExecutor
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.strategies.scalper import MomentumScalper
from titan_system.strategies.trend_surfer import TrendSurfer
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Optimizer")

def backtest_strategy(strategy_class, params, df):
    """
    Simple vector/loop backtest for a strategy configuration.
    Returns: Net Profit
    """
    strategy = strategy_class(config=params)
    balance = 10000.0
    position = 0 # 0, 1 (Long), -1 (Short)
    entry_price = 0.0
    
    trades = 0
    wins = 0
    
    # Iterate through candles (simplified simulation)
    # A real backtester would be more complex, but this is sufficient for parameter tuning
    for i in range(50, len(df)):
        # Slicing for lookback
        slice_df = df.iloc[:i+1]
        
        # Get signal from strategy
        # Note: Strategy.analyze takes the whole DF window usually
        # To speed up, we might modify strategies to take just the row if they are indicators pre-calculated
        # For now, we trust the logic
        result = strategy.analyze("TEST", slice_df)
        signal = result['signal']
        price = df.iloc[i]['close']
        
        # Close conditions (Basic Take Profit / Stop Loss simulation)
        trade_pnl = 0
        if position != 0:
            pnl_pips = (price - entry_price) * position if position == 1 else (entry_price - price)
            # Assuming EURUSD pip value logic roughly
            pnl_cash = pnl_pips * 100000 * 0.1 # 0.1 lot
            
            # Trailing stop or reversal could go here
            # For this optimizer, we just reverse on opposite signal
            if (position == 1 and signal == 'SELL') or (position == -1 and signal == 'BUY'):
                balance += pnl_cash
                trades += 1
                if pnl_cash > 0: wins += 1
                position = 0
        
        # Open conditions
        if position == 0 and signal in ['BUY', 'SELL']:
            position = 1 if signal == 'BUY' else -1
            entry_price = price

    return balance - 10000.0, trades

def optimize_scalper():
    logger.info("🚀 Starting MomentumScalper Optimization...")
    
    # 1. Get Data
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
        
    symbol = "EURUSD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 1000)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 2. Define Parameter Grid
    grid = {
        'rsi_period': [7, 14, 21],
        'ema_short': [5, 9, 12],
        'adx_threshold': [15, 20, 25]
    }
    
    keys, values = zip(*grid.items())
    combinations = [dict(zip(keys, v)) for v in itertools.product(*values)]
    
    print(f"Testing {len(combinations)} combinations on {symbol}...")
    
    best_pnl = -float('inf')
    best_params = None
    
    for params in combinations:
        pnl, trades = backtest_strategy(MomentumScalper, params, df)
        
        if pnl > best_pnl:
            best_pnl = pnl
            best_params = params
            print(f"  ⭐ New Best: ${pnl:.2f} | Trades: {trades} | Params: {params}")
            
    print("\n🏆 OPTIMIZATION COMPLETE")
    print(f"Best PnL: ${best_pnl:.2f}")
    print(f"Best Params: {best_params}")
    return best_params

if __name__ == "__main__":
    optimize_scalper()
