import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import ta
from datetime import datetime
import os
import tqdm

# Constants
BARS_TO_FETCH = 50000
SYMBOLS = ["GOLD", "EURUSD", "GBPUSD", "BTCUSD", "ETHUSD"]
TIMEFRAME = mt5.TIMEFRAME_M15
OUTPUT_FILE = "data/general_market_scenarios_v2.csv"
LOOKAHEAD_BARS = 96  # 24 hours of M15 bars
RISK_REWARD = 2.0    # 2:1 RR
ATR_PERIOD = 14
ATR_MULTIPLIER = 1.5

def calculate_features(df):
    """Calculates technical features for ML."""
    # Trend
    df['ema9'] = ta.trend.ema_indicator(df['close'], window=9)
    df['ema21'] = ta.trend.ema_indicator(df['close'], window=21)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['ema_diff'] = (df['ema9'] - df['ema21']) / df['ema21']
    
    # Momentum
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
    
    # Volatility
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    df['atr_pct'] = df['atr'] / df['close']
    
    # Range Position
    df['low20'] = df['low'].rolling(window=20).min()
    df['high20'] = df['high'].rolling(window=20).max()
    df['range_pos'] = (df['close'] - df['low20']) / (df['high20'] - df['low20'])
    
    return df

def simulate_outcome(row, future_df, direction):
    """Simulates trade outcome by looking forward in time."""
    entry_price = row['close']
    atr = row['atr']
    sl_dist = atr * ATR_MULTIPLIER
    
    if direction == 1: # BUY
        tp = entry_price + (sl_dist * RISK_REWARD)
        sl = entry_price - sl_dist
    else: # SELL
        tp = entry_price - (sl_dist * RISK_REWARD)
        sl = entry_price + sl_dist
        
    for i in range(len(future_df)):
        bar = future_df.iloc[i]
        
        if direction == 1:
            if bar['low'] <= sl: return 0 # Loss
            if bar['high'] >= tp: return 1 # Win
        else:
            if bar['high'] >= sl: return 0 # Loss
            if bar['low'] <= tp: return 1 # Win
            
    return 0 # Timed out (Loss)

def main():
    if not mt5.initialize():
        print(f"MT5 Init Failed: {mt5.last_error()}")
        return
        
    all_data = []
    
    print(f"🚀 GENERATING SYNTHETIC INTELLIGENCE DATA ({BARS_TO_FETCH} bars/symbol)")
    
    for symbol in SYMBOLS:
        print(f"  > Processing {symbol}...", end="", flush=True)
        rates = mt5.copy_rates_from_pos(symbol, TIMEFRAME, 0, BARS_TO_FETCH)
        
        if rates is None or len(rates) < 1000:
            print(" [FAILED: No Data]")
            continue
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Add Features
        df = calculate_features(df)
        df.dropna(inplace=True)
        
        # Simulate Trades
        # We sample every 5th bar to avoid extreme correlation
        for i in range(len(df) - LOOKAHEAD_BARS):
            if i % 3 != 0: continue
            
            curr = df.iloc[i]
            future = df.iloc[i+1 : i+1+LOOKAHEAD_BARS]
            
            # --- LOGIC SELECTION ---
            # Simulate both BUY and SELL on every bar to learn what works and what fails
            # This teaches "General Physics" not just "Strategy Wins"
            
            # Scenario 1: BUY
            outcome_buy = simulate_outcome(curr, future, 1)
            all_data.append({
                'rsi_norm': curr['rsi'] / 100,
                'adx_norm': curr['adx'] / 50,
                'ema_diff': curr['ema_diff'],
                'atr_pct': curr['atr_pct'],
                'range_position': curr['range_pos'],
                'direction_buy': 1,
                'hour_sin': np.sin(2 * np.pi * curr['time'].hour / 24),
                'hour_cos': np.cos(2 * np.pi * curr['time'].hour / 24),
                'session_london': 1 if 7 <= curr['time'].hour <= 16 else 0,
                'session_ny': 1 if 13 <= curr['time'].hour <= 22 else 0,
                'candlestick_score': 0, 
                'outcome': outcome_buy
            })
            
            # Scenario 2: SELL
            outcome_sell = simulate_outcome(curr, future, -1)
            all_data.append({
                'rsi_norm': curr['rsi'] / 100,
                'adx_norm': curr['adx'] / 50,
                'ema_diff': curr['ema_diff'],
                'atr_pct': curr['atr_pct'],
                'range_position': curr['range_pos'],
                'direction_buy': 0,
                'hour_sin': np.sin(2 * np.pi * curr['time'].hour / 24),
                'hour_cos': np.cos(2 * np.pi * curr['time'].hour / 24),
                'session_london': 1 if 7 <= curr['time'].hour <= 16 else 0,
                'session_ny': 1 if 13 <= curr['time'].hour <= 22 else 0,
                'candlestick_score': 0, 
                'outcome': outcome_sell
            })
            
        print(f" [OK: {len(df)} bars]")
        
    mt5.shutdown()
    
    # Save
    master_df = pd.DataFrame(all_data)
    os.makedirs("data", exist_ok=True)
    master_df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n✅ GENERATION COMPLETE")
    print(f"   Total Samples: {len(master_df)}")
    print(f"   Win Rate (Base): {master_df['outcome'].mean():.2%}")
    print(f"   Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
