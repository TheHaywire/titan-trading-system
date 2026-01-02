
import MetaTrader5 as mt5
import pandas as pd
import ta
import numpy as np

TARGETS = ["XAUUSD", "BTCUSD", "ETHUSD", "US500"]

def analyze_vpa(df):
    """
    Volume Price Analysis (Advanced)
    Detects: Effort vs Result, Stopping Volume, Climaxes.
    """
    # Defensive Copy
    df = df.copy()
    
    # Calculate Spread and Volume averages
    df['spread'] = df['high'] - df['low']
    df['vol_ma'] = df['tick_volume'].rolling(20).mean()
    df['spread_ma'] = df['spread'].rolling(20).mean()
    
    # Fill NAs
    df.fillna(0, inplace=True)
    
    if len(df) < 2:
        return "NEUTRAL (No Data)", "Insufficient Data", 0, 0
    
    last = df.iloc[-1]
    
    signal = "NEUTRAL"
    desc = "Normal activity"
    
    vol = last['tick_volume']
    vol_ma = last['vol_ma']
    spread = last['spread']
    spread_ma = last['spread_ma']
    
    # Avoid zero division
    if vol_ma == 0: vol_ma = 1
    if spread_ma == 0: spread_ma = 1
    
    # 1. High Volume, Small Spread (Effort > Result) -> Reversal Warning
    if vol > 1.5 * vol_ma and spread < 0.8 * spread_ma:
        signal = "WARNING"
        desc = "Effort vs Result divergence (Potential Reversal)"
        
    # 2. High Volume, High Spread (Validation)
    elif vol > 1.5 * vol_ma and spread > 1.5 * spread_ma:
        if last['close'] > last['open']:
            signal = "STRONG BULL"
            desc = "Validated Bullish Momentum (Smart Money Buying)"
        else:
            signal = "STRONG BEAR"
            desc = "Validated Bearish Momentum (Smart Money Selling)"
            
    # 3. Low Volume, Small Spread (No Supply/Demand) -> Drift
    elif vol < 0.5 * vol_ma:
        signal = "WEAK"
        desc = "No Demand/Supply (Drifting)"
        
    return signal, desc, vol, vol_ma

def deep_dive(symbol):
    rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 500)
    
    if rates_h1 is None or len(rates_h1) < 200:
        print(f"Skipping {symbol}: Insufficient Data")
        return
    
    df_h1 = pd.DataFrame(rates_h1)
    if 'tick_volume' not in df_h1.columns: df_h1['tick_volume'] = 0
    
    # Indicators
    df_h1['ema200'] = ta.trend.EMAIndicator(df_h1['close'], window=200).ema_indicator()
    df_h1['rsi'] = ta.momentum.RSIIndicator(df_h1['close'], window=14).rsi()
    
    # Fill NAs
    df_h1.fillna(method='bfill', inplace=True)
    df_h1.fillna(0, inplace=True)

    # VPA
    vpa_sig, vpa_desc, vol, vol_ma = analyze_vpa(df_h1.iloc[50:]) 
    
    last = df_h1.iloc[-1]
    price = last['close']
    ema200 = last['ema200']
    rsi_val = last['rsi']
    trend = "BULLISH" if price > ema200 else "BEARISH"
    
    # Suggestion Logic
    suggestion = "WAIT"
    
    if trend == "BULLISH":
        if rsi_val < 40: suggestion = "BUY DIP (Oversold in Uptrend)"
        elif vpa_sig == "STRONG BULL": suggestion = "BUY BREAKOUT (Volume Backed)"
        elif rsi_val > 70: suggestion = "TAKE PROFIT / WAIT (Overbought)"
        else: suggestion = "HOLD / ADD"
        
    elif trend == "BEARISH":
        if rsi_val > 60: suggestion = "SELL RALLY (Overbought in Downtrend)"
        elif vpa_sig == "STRONG BEAR": suggestion = "SELL BREAKDOWN (Volume Backed)"
        elif rsi_val < 30: suggestion = "TAKE PROFIT / WAIT (Oversold)"
        else: suggestion = "HOLD / ADD SHORT"
        
    if "WARNING" in vpa_sig:
        suggestion = "CAUTION: VOLUME ANOMALY DETECTED"

    # Print Report
    print(f"\n{'='*40}")
    print(f"DEEP ANALYSIS: {symbol}")
    print(f"{'='*40}")
    print(f"Price:          {price:.5f}")
    print(f"Trend (H1):     {trend}")
    print(f"RSI (14):       {rsi_val:.1f} ({'Overbought' if rsi_val>70 else ('Oversold' if rsi_val<30 else 'Neutral')})")
    print(f"Vol Signal:     {vpa_sig} ({vpa_desc})")
    print(f"Vol Raw:        {vol:.0f} (Avg: {vol_ma:.0f})")
    print("-" * 40)
    print(f"AI SUGGESTION:  {suggestion.upper()}")
    print("=" * 40 + "\n")

if __name__ == "__main__":
    if mt5.initialize():
        print("Connected to MT5. Analyzing Markets (Advanced TA + VPA)...")
        for sym in TARGETS:
            try:
                deep_dive(sym)
            except Exception as e:
                print(f"Skipped {sym}: {e}")
        mt5.shutdown()
    else:
        print("Failed to connect to MT5.")
