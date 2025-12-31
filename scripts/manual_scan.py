"""
Deep Scan Tool
Running a manual multi-timeframe scan to find immediate opportunities.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config.settings import settings

def deep_scan():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    symbol = "GOLD"
    print("\n" + "="*60)
    print(f"🔬 DEEP MARKET SCAN: {symbol} | {datetime.now().strftime('%H:%M')}")
    print("="*60)
    
    # 1. H1 Analysis (Major Structure)
    rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    df_h1 = pd.DataFrame(rates_h1)
    h1_close = df_h1['close'].iloc[-1]
    h1_ema20 = df_h1['close'].ewm(span=20).mean().iloc[-1]
    h1_trend = "BULLISH" if h1_close > h1_ema20 else "BEARISH"
    print(f"1️⃣  H1 Trend: {h1_trend} (Price: {h1_close:.2f} vs EMA20: {h1_ema20:.2f})")
    
    # 2. M15 Analysis (Micro Structure)
    rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
    df_m15 = pd.DataFrame(rates_m15)
    
    # Calculate RSI
    delta = df_m15['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs)).iloc[-1]
    
    print(f"2️⃣  M15 Momentum: RSI is {rsi:.1f}")
    if rsi > 70: print("    ⚠️  OVERBOUGHT (Potential Short)")
    elif rsi < 30: print("    ⚠️  OVERSOLD (Potential Long)")
    
    # 3. Find Minor Zones (Micro-Sweeps)
    last_10_high = df_m15['high'].iloc[-10:].max()
    last_10_low = df_m15['low'].iloc[-10:].min()
    
    current_price = mt5.symbol_info_tick(symbol).bid
    dist_to_high = last_10_high - current_price
    dist_to_low = current_price - last_10_low
    
    print(f"3️⃣  Micro Zones (M15 Last 10 Bars):")
    print(f"    Resistance: {last_10_high:.2f} (Dist: {dist_to_high:.1f} pts)")
    print(f"    Support:    {last_10_low:.2f} (Dist: {dist_to_low:.1f} pts)")
    
    print("-" * 60)
    
    # 4. RECOMMENDATION
    opportunities = []
    
    # Strategy: Minor Sweep
    if dist_to_high < 2.0:
        opportunities.append("SCALP SHORT IF we sweep " + str(last_10_high))
    if dist_to_low < 2.0:
        opportunities.append("SCALP LONG IF we sweep " + str(last_10_low))
        
    # Strategy: Momentum
    if rsi > 70 and h1_trend == "BEARISH":
        opportunities.append("IMMEDIATE SHORT (Trend + RSI Aligned)")
    if rsi < 30 and h1_trend == "BULLISH":
        opportunities.append("IMMEDIATE LONG (Trend + RSI Aligned)")
        
    if not opportunities:
        print("💤 CONFIRMATION: No High-Probability Setup Found.")
        print("   Price is chopping in the middle of M15 range.")
        print("   Wait for {0:.2f} or {1:.2f}".format(last_10_high, last_10_low))
    else:
        print("🚀 OPPORTUNITIES FOUND:")
        for op in opportunities:
            print(f"   >> {op}")
            
    mt5.shutdown()

if __name__ == "__main__":
    deep_scan()
