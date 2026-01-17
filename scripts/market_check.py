import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import ta

def analyze_setup(symbol):
    print(f"\n--- {symbol} Real-Time Setup Scan ---")
    if not mt5.initialize(): return
    
    # Fetch H1 for Bias
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    if h1_rates is None: return
    df_h1 = pd.DataFrame(h1_rates)
    df_h1['sma200'] = ta.trend.sma_indicator(df_h1['close'], window=50) # Using 50 for faster bias on intraday
    
    curr_h1 = df_h1.iloc[-1]
    bias = "BULLISH" if curr_h1['close'] > curr_h1['sma200'] else "BEARISH"
    
    # Fetch M15 for Trigger
    m15_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if m15_rates is None: return
    df_m15 = pd.DataFrame(m15_rates)
    df_m15['rsi'] = ta.momentum.rsi(df_m15['close'], window=14)
    
    curr_m15 = df_m15.iloc[-1]
    
    print(f"H1 Bias: {bias} (Price: {curr_h1['close']:.2f} vs SMA50: {curr_h1['sma200']:.2f})")
    print(f"M15 RSI: {curr_m15['rsi']:.2f}")
    
    # Check for Setup
    if bias == "BULLISH" and curr_m15['rsi'] < 40:
        print("🟢 SETUP: Bullish Pullback. Looking for LONG entry.")
    elif bias == "BEARISH" and curr_m15['rsi'] > 60:
        print("🔴 SETUP: Bearish Retracement. Looking for SHORT entry.")
    else:
        print("⚪ NO SETUP: Waiting for alignment.")

if __name__ == "__main__":
    analyze_setup("GOLD")
    analyze_setup("BTCUSD")
    mt5.shutdown()
