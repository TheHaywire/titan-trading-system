"""
Institutional Trade Plan Generator
Synthesizes data from Institutional Engine into a readable Trade Plan for the user.
"""

import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings
from titan_system.smc.institutional_engine import InstitutionalEngine

def generate_plan():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
    
    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
    df = pd.DataFrame(rates)
    
    engine = InstitutionalEngine()
    data = engine.analyze_symbol(df, symbol)
    
    # Extract Key Metrics
    current_price = df['close'].iloc[-1]
    regime = data['regime']
    
    print("\n" + "="*70)
    print(f"🏛️  INSTITUTIONAL TRADE PLAN: {symbol}  |  {pd.Timestamp.now()}")
    print("="*70)
    
    print(f"\n📊 MARKET REGIME:  >> {regime} <<")
    
    # 1. Narrative Construction
    print("\n📝 NARRATIVE & BIAS")
    trend = data['trend']
    mom = data['momentum']
    vol = data['volatility']
    vwap = data['vwap']
    
    narrative = []
    if trend['bias'] == "BULLISH":
        narrative.append("• Structural Trend is BULLISH (EMA Alignment).")
    elif trend['bias'] == "BEARISH":
        narrative.append("• Structural Trend is BEARISH (EMA Alignment).")
    else:
        narrative.append("• Structural Trend is MIXED/NEUTRAL.")
        
    if mom['rsi'] > 60:
        narrative.append("• Momentum is currently STRONG BULLISH (RSI > 60).")
    elif mom['rsi'] < 40:
        narrative.append("• Momentum is currently STRONG BEARISH (RSI < 40).")
    else:
        narrative.append("• Momentum is NEUTRAL.")
        
    if vol['regime'] == "LOW_VOL_COMPRESSION":
        narrative.append("⚠️ WARNING: VOLATILITY SQUEEZE DETECTED! Expect explosive move soon.")
    elif vol['regime'] == "HIGH_VOL_EXPANSION":
        narrative.append("• Volatility is EXPANDED. Expect wider ranges.")
        
    for line in narrative:
        print(line)
        
    # 2. Key Levels (Liquidity & VWAP)
    print("\n🎯 KEY LEVELS OF INTEREST")
    print(f"• Current Price:   {current_price:.2f}")
    print(f"• Institutional VWAP: {vwap['vwap']:.2f}")
    
    liq = data['liquidity']
    if liq['sessions']['prev_day_high']:
        print(f"• Prev Day High:   {liq['sessions']['prev_day_high']:.2f} (Liquidity Pool)")
    if liq['sessions']['prev_day_low']:
        print(f"• Prev Day Low:    {liq['sessions']['prev_day_low']:.2f} (Liquidity Pool)")
        
    # 3. Actionable Scenarios
    print("\n⚔️  TRADING SCENARIOS FOR NEXT SESSION")
    
    # Scenario A: Trend Continuation
    if trend['tss'] >= 3:
        direction = "LONG" if trend['bias'] == "BULLISH" else "SHORT"
        print(f"[A] TREND CONTINUATION ({direction})")
        print(f"   Wait for pullback to EMAs or VWAP ({vwap['vwap']:.2f}).")
        print(f"   Confirm with RSI {'above 50' if direction=='LONG' else 'below 50'}.")
    else:
        print("[A] NO CLEAR TREND DETECTED - Avoid Trend Strategies.")
        
    # Scenario B: Squeeze Breakout (if applicable)
    if vol['regime'] == "LOW_VOL_COMPRESSION":
        print("[B] SQUEEZE BREAKOUT")
        print("   Volatility is compressed. Watch for impulse candle > ATR.")
        print("   Trade the direction of the first H1 close outside current range.")
        
    # Scenario C: Liquidity Reversal
    print("[C] LIQUIDITY REVERSAL")
    if liq['sessions']['prev_day_high']:
        print(f"   Watch {liq['sessions']['prev_day_high']:.2f} for SWEEP + CLOSE BELOW -> SHORT TARGET VWAP.")
    if liq['sessions']['prev_day_low']:
        print(f"   Watch {liq['sessions']['prev_day_low']:.2f} for SWEEP + CLOSE ABOVE -> LONG TARGET VWAP.")

    # 4. Immediate Setups
    if data['setup']:
        print("\n🔥 ACTIVE ALGORITHMIC SIGNALS")
        for s in data['setup']:
            print(f"   >> {s['name']}: {s.get('trigger')} (Entry: {s.get('entry', 'Market')})")
    else:
        print("\n💤 NO ALGORITHMIC ENTRY SIGNALS PRESENT NOW.")
            
    print("\n" + "="*70)
    mt5.shutdown()

if __name__ == "__main__":
    generate_plan()
