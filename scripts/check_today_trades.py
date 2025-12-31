"""
Daily Opportunity Review
Checks if the Institutional Logic would have triggered trades today.
"""
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta
from titan_system.smc.momentum_engine import MomentumEngine
from config.settings import settings

def check_today_opportunities():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    symbol = "GOLD"
    # Get today's M15 data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 96) # Last 24 hours
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Calculate RSI
    mom = MomentumEngine()
    df['rsi'] = mom.calculate_rsi(df['close'], 14)
    
    # Get Yesterday's High/Low (Using H1 data approx)
    rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 24, 24) # Previous day approx
    pdh = max([x['high'] for x in rates_h1])
    pdl = min([x['low'] for x in rates_h1])
    
    print("\n" + "="*60)
    print(f"🕵️ DID WE MISS TRADES TODAY? ({datetime.now().date()})")
    print("="*60)
    print(f"PDH (Resistance): {pdh:.2f}")
    print(f"PDL (Support):    {pdl:.2f}")
    
    opportunities = 0
    
    for i in range(14, len(df)):
        row = df.iloc[i]
        
        # 1. LIQUIDITY SWEEP CHECK
        if row['high'] >= pdh:
            print(f"⏰ {row['time'].time()} | 🔴 SWEEP: Hit PDH ({row['high']:.2f}) -> POTENTIAL SHORT")
            opportunities += 1
        elif row['low'] <= pdl:
            print(f"⏰ {row['time'].time()} | 🟢 SWEEP: Hit PDL ({row['low']:.2f}) -> POTENTIAL LONG")
            opportunities += 1
            
        # 2. RSI EXTREME CHECK
        elif row['rsi'] > 75:
             print(f"⏰ {row['time'].time()} | 🔴 RSI EXTREME ({row['rsi']:.1f}) @ {row['close']:.2f} -> SCALP SHORT")
             opportunities += 1
        elif row['rsi'] < 25:
             print(f"⏰ {row['time'].time()} | 🟢 RSI EXTREME ({row['rsi']:.1f}) @ {row['close']:.2f} -> SCALP LONG")
             opportunities += 1
             
    if opportunities == 0:
        print("\n💤 Result: NO High-Quality Setups today (System kept you safe).")
    else:
        print(f"\n✅ Result: {opportunities} potential setups identified.")
        
    mt5.shutdown()

if __name__ == "__main__":
    check_today_opportunities()
