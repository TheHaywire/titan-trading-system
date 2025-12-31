"""
Multi-Timeframe Institutional Scanner for GOLD
Analyzes H4 (Strategic), H1 (Tactical), and M15 (Execution) layers.
"""

import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings
from titan_system.smc.institutional_engine import InstitutionalEngine

def run_mtf_scan():
    if not mt5.initialize():
        print("MT5 Failed")
        return
    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
        
    symbol = "GOLD"
    engine = InstitutionalEngine()
    
    # 1. STRATEGIC LAYER (H4) - The Bias
    rates_h4 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 200)
    df_h4 = pd.DataFrame(rates_h4)
    res_h4 = engine.analyze_symbol(df_h4, symbol)
    
    # 2. TACTICAL LAYER (H1) - The Zones
    rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    df_h1 = pd.DataFrame(rates_h1)
    res_h1 = engine.analyze_symbol(df_h1, symbol)
    
    # 3. EXECUTION LAYER (M15) - The Setup
    rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 200)
    df_m15 = pd.DataFrame(rates_m15)
    res_m15 = engine.analyze_symbol(df_m15, symbol)
    
    current_price = df_m15['close'].iloc[-1]
    
    print("="*60)
    print(f"🥇 GOLD MULTI-TIMEFRAME DEEP DIVE | {pd.Timestamp.now()}")
    print("="*60)
    
    # --- H4 ANALYSIS ---
    bias = res_h4['trend']['bias']
    tss = res_h4['trend']['tss']
    h4_regime = res_h4['regime']
    
    print(f"\n1️⃣ STRATEGIC LAYER (H4) -> BIAS: {bias}")
    print(f"   • Trend Strength: {tss}/5 ({h4_regime})")
    print(f"   • EMA Alignment: {res_h4['trend']['ema_alignment'].upper()}")
    print(f"   • Verdict: {'LOOK FOR LONGS ONLY' if bias == 'BULLISH' else 'LOOK FOR SHORTS ONLY' if bias == 'BEARISH' else 'CAUTION - MIXED BIAS'}")

    # --- H1 ANALYSIS ---
    print(f"\n2️⃣ TACTICAL LAYER (H1) -> ZONES")
    print(f"   • Market Structure: {res_h1['trend']['bias']}") # Using bias as proxy for structure direction
    
    # Identify nearest liquidity pools
    pools = []
    if res_h1['liquidity']['sessions']['prev_day_high']:
        pools.append((res_h1['liquidity']['sessions']['prev_day_high'], "PDH"))
    if res_h1['liquidity']['sessions']['prev_day_low']:
        pools.append((res_h1['liquidity']['sessions']['prev_day_low'], "PDL"))
        
    # Sort pools by distance to price
    pools.sort(key=lambda x: abs(x[0] - current_price))
    
    print(f"   • Nearest Liquidity Magnets:")
    for p in pools[:2]:
        dist = p[0] - current_price
        direction = "ABOVE" if dist > 0 else "BELOW"
        print(f"     -> {p[1]} at {p[0]:.2f} is {abs(dist):.2f} pts {direction}")

    # --- M15 ANALYSIS ---
    print(f"\n3️⃣ EXECUTION LAYER (M15) -> ACTION")
    print(f"   • Volatility: {res_m15['volatility']['regime']}")
    if res_m15['volatility']['regime'] == "LOW_VOL_COMPRESSION":
        print("     ⚠️  SQUEEZE ACTIVE - DO NOT CHASE.")
        
    print(f"   • Momentum (RSI): {res_m15['momentum']['rsi']:.1f}")
    
    # Check alignment
    aligned = (bias == res_m15['trend']['bias'])
    print(f"   • H4/M15 Alignment: {'✅ ALIGNED' if aligned else '❌ CONFLICT'}")
    
    # Final Plan
    print("\n📝 THE EXECUTABLE PLAN")
    if aligned and bias == "BULLISH":
        print("   ✅ BUY SCENARIO: Wait for M15 pullback to VWAP. Target H1 PDH.")
    elif aligned and bias == "BEARISH":
        print("   ✅ SELL SCENARIO: Wait for M15 rally to VWAP. Target H1 PDL.")
    else:
        print("   ⚠️  CONFLICT: H4 and M15 disagree. Wait for M15 to align with H4.")
        print("      (Or trade the H1 Liquidity Sweep Reversal setup if price hits PDH/PDL)")
        
    mt5.shutdown()

if __name__ == "__main__":
    run_mtf_scan()
