"""
ML TRAINING DATA GENERATOR
==========================
Runs historical analysis to generate features and outcomes for ML training.
Scans history, identifies signals, and tracks their success/failure.

Features Recorded:
- Technicals (RSI, ADX, SMA, ATR)
- Candlestick Patterns
- Market Regime
- Key Levels Context (at support/resistance)
- Market Profile Context (at POC/Value Area)
- Time of Day (Session)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
from datetime import datetime, timedelta
from scripts.autonomous_bot import AutonomousTradingBot
from tqdm import tqdm

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("DataGen")

def generate_data(symbol: str, timeframe: int, days_back: int = 90):
    """
    Scans history and generates a dataset of signals and their outcomes.
    """
    logger.info(f"Generating training data for {symbol} ({days_back} days)...")
    
    if not mt5.initialize():
        logger.error("MT5 failed")
        return None
        
    # Get plenty of data for analysis and outcome tracking
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, days_back * 100) # Approx for H1/M15
    if rates is None or len(rates) < 1000:
        logger.error(f"Not enough data for {symbol}")
        return None
        
    df = pd.DataFrame(rates)
    df['time_dt'] = pd.to_datetime(df['time'], unit='s')
    
    bot = AutonomousTradingBot()
    dataset = []
    
    # We need to loop through the data, but for each bar we need lookback for analysis
    # and lookahead for outcome.
    # Analysis lookback: 300 bars
    # Outcome lookahead: 50 bars
    
    analysis_window = 300
    outcome_window = 100
    
    # Simple outcome labeling:
    # SUCCESS = Price hits Target (2 * ATR) before Stop (1 * ATR)
    
    progress = tqdm(range(analysis_window, len(df) - outcome_window), desc=f"Scanning {symbol}")
    
    for i in progress:
        # Current analysis slice
        slice_df = df.iloc[i-analysis_window:i+1].copy()
        
        # Mock regime (in a real scenario we'd use the detector, here we use bot's logic)
        # Simplified:bot.analyze_symbol needs regime_info
        mock_regime = {
            'regime': 'TRENDING', 
            'preferred_strategies': ['Trend Following'], 
            'avoid_strategies': [], 
            'risk_multiplier': 1.0
        }
        
        # Run bot's analysis
        signal = bot.analyze_symbol(symbol, slice_df, mock_regime)
        
        if signal:
            # We found a potential signal! Now find the outcome
            direction = signal['direction']
            entry_price = df.iloc[i]['close']
            atr = slice_df.tail(20).apply(lambda row: row['high'] - row['low'], axis=1).mean()
            if atr == 0: atr = entry_price * 0.001
            
            sl_dist = atr * 1.5
            tp_dist = atr * 3.0 # 1:2 Risk Reward
            
            sl = entry_price - sl_dist if direction == 'BUY' else entry_price + sl_dist
            tp = entry_price + tp_dist if direction == 'BUY' else entry_price - tp_dist
            
            # Look ahead for outcome
            success = 0
            found_outcome = False
            
            for j in range(i + 1, i + outcome_window):
                high = df.iloc[j]['high']
                low = df.iloc[j]['low']
                
                if direction == 'BUY':
                    if high >= tp:
                        success = 1
                        found_outcome = True
                        break
                    if low <= sl:
                        success = 0
                        found_outcome = True
                        break
                else: # SELL
                    if low <= tp:
                        success = 1
                        found_outcome = True
                        break
                    if high >= sl:
                        success = 0
                        found_outcome = True
                        break
            
            if found_outcome:
                # Extract features to match SignalFilter._get_feature_names()
                # 'rsi_norm', 'adx_norm', 'ema_diff', 'atr_pct', 'range_position',
                # 'regime_trending', 'regime_mean_rev', 'regime_high_vol',
                # 'direction_buy', 'score_norm', 'hour_sin', 'hour_cos',
                # 'session_london', 'session_ny', 'candlestick_score'
                
                features = {
                    'rsi_norm': slice_df['rsi'].iloc[-1] / 100 if 'rsi' in slice_df else 0.5,
                    'adx_norm': slice_df['adx'].iloc[-1] / 50 if 'adx' in slice_df else 0.5,
                    'ema_diff': 0, # Simplified for now
                    'atr_pct': atr / entry_price,
                    'range_position': 0.5, # Simplified
                    'regime_trending': 1,
                    'regime_mean_rev': 0,
                    'regime_high_vol': 0,
                    'direction_buy': 1 if direction == 'BUY' else 0,
                    'score_norm': signal['score'] / 100,
                    'hour_sin': np.sin(2 * np.pi * df.iloc[i]['time_dt'].hour / 24),
                    'hour_cos': np.cos(2 * np.pi * df.iloc[i]['time_dt'].hour / 24),
                    'session_london': 1 if 7 <= df.iloc[i]['time_dt'].hour <= 16 else 0,
                    'session_ny': 1 if 13 <= df.iloc[i]['time_dt'].hour <= 22 else 0,
                    'candlestick_score': 15 if any("[CDL]" in r for r in signal['reasons']) else 0,
                    'outcome': success
                }
                dataset.append(features)
                
    mt5.shutdown()
    
    if dataset:
        result_df = pd.DataFrame(dataset)
        output_path = f"data/training_{symbol.lower()}.csv"
        os.makedirs("data", exist_ok=True)
        result_df.to_csv(output_path, index=False)
        logger.info(f"Generated {len(result_df)} samples for {symbol}. Saved to {output_path}")
        return result_df
    else:
        logger.warning(f"No valid signals found for {symbol}")
        return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GOLD")
    parser.add_argument("--days", type=int, default=90)
    args = parser.parse_args()
    
    generate_data(args.symbol, mt5.TIMEFRAME_M15, args.days)
