import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import ta
from datetime import datetime, timedelta
import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())
from titan_system.ml.signal_filter import SignalFilter

def get_history_features():
    """
    Pulls real historical deals from MT5 and calculates technical context.
    This is the 'True Ground Truth' training set.
    """
    print("🚀 Initializing MT5 True-History Intelligence Pipeline...")
    if not mt5.initialize():
        print("❌ MT5 Initialization Failed")
        return None

    # 1. Fetch Deals from the last 90 days
    from_date = datetime.now() - timedelta(days=90)
    to_date = datetime.now()
    
    deals = mt5.history_deals_get(from_date, to_date)
    if deals is None or len(deals) == 0:
        print("❌ No historical deals found.")
        return None

    print(f"📊 Analyzing {len(deals)} historical events...")
    
    dataset = []
    
    # We want to find CLOSING deals to get the profit/loss, then look at the ENTRY context.
    print(f"Total deals found: {len(deals)}")
    
    for deal in deals:
        # entry=0 (In), entry=1 (Out)
        if deal.entry != 1: # Only look at closing deals
            continue
            
        symbol = deal.symbol
        profit = deal.profit + deal.swap + deal.commission
        
        position_id = deal.position_id
        pos_deals = mt5.history_deals_get(position=position_id)
        
        if pos_deals is None or len(pos_deals) == 0:
            # print(f"DEBUG: No deals found for PositionID {position_id}")
            continue

        try:
            entry_deal = [d for d in pos_deals if d.entry == 0][0]
            entry_time = datetime.fromtimestamp(entry_deal.time)
            direction = 1 if entry_deal.type == mt5.ORDER_TYPE_BUY else 0
        except Exception as e:
            # print(f"DEBUG: Could not find entry deal for {symbol} (PID {position_id}): {e}")
            continue

        # 2. Fetch context at ENTRY time
        rates = mt5.copy_rates_from(symbol, mt5.TIMEFRAME_M15, entry_time, 100)
        if rates is None or len(rates) < 50:
            # print(f"DEBUG: No M15 rates for {symbol} at {entry_time}")
            continue
            
        df = pd.DataFrame(rates)
        
        # Calculate Features
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
        df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
        df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=9)
        df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=21)
        df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
        
        curr = df.iloc[-1]
        
        # Skip if features are NaN
        if pd.isna(curr['rsi']) or pd.isna(curr['adx']):
            continue
            
        # Standardized Features for SignalFilter
        features = {
            'rsi_norm': curr['rsi'] / 100,
            'adx_norm': curr['adx'] / 50,
            'ema_diff': (curr['ema_fast'] - curr['ema_slow']) / curr['ema_slow'],
            'atr_pct': curr['atr'] / curr['close'],
            'range_position': (curr['close'] - df['low'].tail(20).min()) / (df['high'].tail(20).max() - df['low'].tail(20).min()) if (df['high'].tail(20).max() - df['low'].tail(20).min()) != 0 else 0.5,
            'regime_trending': 1, # Defaulting to trending for history
            'regime_mean_rev': 0,
            'regime_high_vol': 0,
            'direction_buy': 1 if direction == 1 else 0,
            'score_norm': 0.7, # Mocked base score for history
            'hour_sin': np.sin(2 * np.pi * entry_time.hour / 24),
            'hour_cos': np.cos(2 * np.pi * entry_time.hour / 24),
            'session_london': 1 if 7 <= entry_time.hour <= 16 else 0,
            'session_ny': 1 if 13 <= entry_time.hour <= 22 else 0,
            'candlestick_score': 0.0,
            'outcome': 1 if profit > 0 else 0
        }
        dataset.append(features)
        
        if len(dataset) % 50 == 0:
            print(f"✅ Processed {len(dataset)} verified samples...")

    mt5.shutdown()
    
    if dataset:
        result_df = pd.DataFrame(dataset)
        print(f"💎 Extraction Complete: {len(result_df)} samples ready.")
        return result_df
    return None

def train_true_model():
    df = get_history_features()
    if df is None or df.empty:
        print("❌ Dataset generation failed.")
        return
        
    # Save for auditing
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/true_pnl_training_data.csv", index=False)
    
    sf = SignalFilter()
    print("🧠 Training Strategic Model on Real Equity history...")
    success = sf.train(df)
    
    if success:
        print("✨ MODEL CERTIFIED: Grounded in real-world MT5 execution.")
    else:
        print("❌ Training encountered numerical instability.")

if __name__ == "__main__":
    train_true_model()
