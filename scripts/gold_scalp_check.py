"""
M15 Scalp Analysis
Checks M15 specifically for VWAP distance and RSI extremes for immediate scalping
"""
import MetaTrader5 as mt5
import pandas as pd
from titan_system.smc.vwap_engine import VWAPEngine
from titan_system.smc.momentum_engine import MomentumEngine
from config.settings import settings

def scalp_check():
    if not mt5.initialize(): return
    if settings.mt5_login: mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    df = pd.DataFrame(rates)
    
    # Calculate M15 VWAP
    # Note: For true session VWAP we normally anchor to open, 
    # but for M15 mean reversion, a rolling cumulative or H1 anchor works.
    # Using the Engine logic which averages over the loaded period.
    vwap_eng = VWAPEngine()
    vwap_res = vwap_eng.analyze(df)
    
    mom_eng = MomentumEngine()
    mom_res = mom_eng.analyze(df)
    
    current_price = df['close'].iloc[-1]
    dist = current_price - vwap_res['vwap']
    
    print("\n⚔️ M15 SCALP PRECISION DATA")
    print(f"Current Price: {current_price:.2f}")
    print(f"M15 VWAP:      {vwap_res['vwap']:.2f}")
    print(f"Deviation:     {dist:.2f} points ({'ABOVE' if dist>0 else 'BELOW'})")
    print(f"M15 RSI:       {mom_res['rsi']:.1f}")
    
    if dist > 0 and mom_res['rsi'] > 70:
        print("\n✅ ALERT: EXTENDED LONG")
        print("   Valid Scalp: SHORT back to VWAP")
        print(f"   Target: {vwap_res['vwap']:.2f}")
    elif dist < 0 and mom_res['rsi'] < 30:
        print("\n✅ ALERT: EXTENDED SHORT")
        print("   Valid Scalp: LONG back to VWAP")
        print(f"   Target: {vwap_res['vwap']:.2f}")
    else:
        print("\n⚪ NO EXTREME EXTENSION DETECTED.")
        
    mt5.shutdown()

if __name__ == "__main__":
    scalp_check()
