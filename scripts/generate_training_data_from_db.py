import sqlite3
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import ta
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DataGen")

DB_PATH = "data/titan.db"
TIMEFRAME = mt5.TIMEFRAME_M15 # We train on M15 context

def get_market_context(symbol, timestamp_str):
    """Fetches OHLCV leading up to the trade and calculates features."""
    # Convert timestamp string to datetime
    try:
        ts = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    except:
        return None
        
    # Fetch 200 bars before the trade
    rates = mt5.copy_rates_from(symbol, TIMEFRAME, ts, 200)
    if rates is None or len(rates) < 50:
        return None
        
    df = pd.DataFrame(rates)
    
    # Features
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
    df['sma50'] = ta.trend.sma_indicator(df['close'], window=50)
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    # State AT the trade time (last row of rates which is closest to ts)
    curr = df.iloc[-1]
    
    features = {
        'rsi': curr['rsi'],
        'adx': curr['adx'],
        'ema_diff': (curr['close'] - curr['ema20']) / curr['ema20'],
        'trend_alignment': 1 if curr['close'] > curr['sma50'] else 0,
        'volatility': curr['atr'] / curr['close'],
        'hour': ts.hour
    }
    return features

def extract_and_label():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    conn = sqlite3.connect(DB_PATH)
    trades_df = pd.read_sql_query("SELECT symbol, type, open_time, profit FROM trades WHERE profit IS NOT NULL", conn)
    
    dataset = []
    print(f"Propelling Machine Learning: Reconstructing context for {len(trades_df)} historical trades...")
    
    for _, row in trades_df.iterrows():
        context = get_market_context(row['symbol'], row['open_time'])
        if context:
            # Outcome: 1 for profit > 0, else 0
            context['outcome'] = 1 if row['profit'] > 0 else 0
            context['symbol'] = row['symbol']
            context['direction'] = 1 if row['type'] == 'BUY' else 0
            dataset.append(context)
            if len(dataset) % 10 == 0:
                print(f"Processed {len(dataset)} trades...")

    if dataset:
        final_df = pd.DataFrame(dataset)
        output_path = "data/training_live_reconstructed.csv"
        final_df.to_csv(output_path, index=False)
        print(f"✅ Success! Generated training data with {len(final_df)} samples at {output_path}")
    else:
        print("❌ Failed to generate any valid samples.")

    conn.close()
    mt5.shutdown()

if __name__ == "__main__":
    extract_and_label()
