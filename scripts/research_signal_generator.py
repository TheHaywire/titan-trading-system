"""
TITAN RESEARCH LAB: HFT MOMENTUM SCALPER (Prototype v1)
=======================================================
 HYPOTHESIS: High-Volatility Breakouts + Momentum allow for
             exponential growth via rapid compounding.
 SOURCE:     Prop Trading Research 2025 (Breakout + RSI/MACD)
 ASSETS:     US100 (Nasdaq), GOLD (XAUUSD), GER40 (DAX)
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# Aggressive Settings
RSI_PERIOD = 7        # Faster than standard 14
RSI_OVERBOUGHT = 75   # Extreme momentum
RSI_OVERSOLD = 25
ADX_THRESHOLD = 30    # Only trade strong trends

def get_data(symbol, timeframe, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None: return None
    df = pd.DataFrame(rates)
    return df

def calculate_indicators(df):
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # ADX (Simplified approximation for speed)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift()), 
                                     abs(df['low'] - df['close'].shift())))
    df['atr'] = df['tr'].rolling(14).mean()
    df['adx_proxy'] = (df['close'] - df['close'].shift(14)).abs() / df['atr'] * 10
    
    return df

def scan_symbol(symbol):
    df = get_data(symbol, mt5.TIMEFRAME_M1, count=100) # M1 Scalping
    if df is None: return None
    
    df = calculate_indicators(df)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    # LOGIC 1: MOMENTUM BREAKOUT (Prop Firm Style)
    # Buy if RSI crosses above 75 (Momentum ignition) + ADX indicates trend
    if last['rsi'] > RSI_OVERBOUGHT and prev['rsi'] <= RSI_OVERBOUGHT:
        if last['adx_proxy'] > 2.0: # Strong move
            return "BUY_MOMENTUM"
            
    # Sell if RSI crosses below 25 (Momentum collapse)
    if last['rsi'] < RSI_OVERSOLD and prev['rsi'] >= RSI_OVERSOLD:
        if last['adx_proxy'] > 2.0:
            return "SELL_MOMENTUM"
            
    # LOGIC 2: MEAN REVERSION (Contrarian)
    # Buy if price < Lower BB and RSI < 20 (Extreme Oversold)
    # Sell if price > Upper BB and RSI > 80 (Extreme Overbought)
    
    # Calculate Bollinger Bands
    df['sma20'] = df['close'].rolling(20).mean()
    df['std20'] = df['close'].rolling(20).std()
    df['upper_bb'] = df['sma20'] + (df['std20'] * 2.5) # 2.5 SD for extreme
    df['lower_bb'] = df['sma20'] - (df['std20'] * 2.5)
    
    last = df.iloc[-1]
    
    if last['close'] < last['lower_bb'] and last['rsi'] < 20:
        return "BUY_REVERSION"
        
    if last['close'] > last['upper_bb'] and last['rsi'] > 80:
        return "SELL_REVERSION"
            
    return None

def run_research_scan():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    symbols = ["US100Cash", "GOLD", "GER40Cash", "BTCUSD"]
    print(f"🔬 RESEARCH LAB: Scanning {len(symbols)} assets for HFT MOMENTUM...")
    
    found_any = False
    for sym in symbols:
        signal = scan_symbol(sym)
        if signal:
            found_any = True
            print(f"🚀 {sym}: {signal} (RSI Breakout confirmed)")
            
    if not found_any:
        print("💤 No HFT anomalies detected. Waiting for volatility.")
        
    mt5.shutdown()

if __name__ == "__main__":
    run_research_scan()
