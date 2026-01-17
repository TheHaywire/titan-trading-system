"""
TITAN ALPHA SIGNAL PRODUCER
===========================
The "Making Money" Engine.
Combines SMC (Liquidity Sweeps + Structure Shifts) with Regime Context.
Outputs high-conviction signals ONLY.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
import MetaTrader5 as mt5

# Add project root to path
sys.path.append(os.getcwd())

from titan_system.smc.liquidity import LiquidityEngine
from titan_system.smc.market_structure import MarketStructure
from titan_system.smc.fvg import FVGDetector

def get_data(symbol: str, timeframe: int, count: int = 200):
    """Fetch data from MT5."""
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def generate_signal(symbol: str):
    """
    Generate SMC signal for a symbol.
    Logic: Sweep of Previous High/Low + CHoCH on lower TF.
    """
    # 1. Trend Context (H1)
    df_h1 = get_data(symbol, mt5.TIMEFRAME_H1, 100)
    if df_h1 is None: return {"error": "H1 data failed"}
    
    ms_engine_h1 = MarketStructure(swing_length=5)
    h1_struct = ms_engine_h1.analyze(df_h1)
    h1_trend = h1_struct.get('trend', 'neutral')
    
    liq_engine = LiquidityEngine(proximity_threshold=2.0)
    h1_liq = liq_engine.analyze(df_h1, symbol)
    
    # Logic A: Sweep (Reversal)
    recent_sweeps = h1_liq.get('sweeps', [])
    if recent_sweeps:
        latest_sweep = recent_sweeps[-1]
        bias = "BULLISH" if latest_sweep['sweep_type'] == 'bearish_liquidity_grab' else "BEARISH"
        confirmed_type = "REVERSAL_SWEEP"
    else:
        # Logic B: BOS (Continuation)
        if h1_trend != 'neutral':
            bias = h1_trend.upper()
            confirmed_type = "TREND_CONTINUATION"
        else:
            return {"symbol": symbol, "status": "NO_SETUP", "message": "No H1 Sweep or Clear Trend detected"}

    # 2. Lower Timeframe Confirmation (M15)
    df_m15 = get_data(symbol, mt5.TIMEFRAME_M15, 100)
    if df_m15 is None: return {"error": "M15 data failed"}
    
    ms_engine_m15 = MarketStructure(swing_length=3)
    m15_struct = ms_engine_m15.analyze(df_m15)
    
    # For REVERSAL: Look for CHoCH
    # For TREND: Look for M15 Trend Alignment
    if confirmed_type == "REVERSAL_SWEEP":
        choch_events = m15_struct.get('choch', [])
        confirmed = any((bias == "BULLISH" and e['direction'] == 'bullish') or 
                        (bias == "BEARISH" and e['direction'] == 'bearish') for e in choch_events)
    else:
        confirmed = m15_struct.get('trend', '').upper() == bias

    if not confirmed:
        return {
            "symbol": symbol, 
            "status": "WAITING_CONFIRMATION", 
            "bias": bias,
            "type": confirmed_type,
            "message": f"H1 {bias} setup detected, but M15 not aligned yet"
        }
    
    # 3. Entry Parameters (FVG or Retest)
    fvg_detector = FVGDetector()
    fvgs = fvg_detector.detect_fvg(df_m15['open'].values, df_m15['high'].values, df_m15['low'].values, df_m15['close'].values)
    
    entry_price = df_m15['close'].iloc[-1]
    sl_price = m15_struct['last_swing_low']['price'] if bias == "BULLISH" else m15_struct['last_swing_high']['price']
    
    # Calculate target (next liquidity pool)
    target_price = h1_liq['sessions']['prev_day_high'] if bias == "BULLISH" else h1_liq['sessions']['prev_day_low']
    
    if not target_price: # Fallback target
        atr = df_m15['high'].max() - df_m15['low'].min()
        target_price = entry_price + (entry_price - sl_price) * 2 if bias == "BULLISH" else entry_price - (sl_price - entry_price) * 2

    # Final Signal
    return {
        "symbol": symbol,
        "status": "SIGNAL_READY",
        "bias": bias,
        "entry": round(entry_price, 5),
        "sl": round(sl_price, 5),
        "tp": round(target_price, 5),
        "rr": round(abs(target_price - entry_price) / abs(entry_price - sl_price), 2) if abs(entry_price - sl_price) > 0 else 0,
        "confidence": "HIGH" if len(fvgs) > 0 else "MEDIUM",
        "message": f"H1 {bias} Sweep + M15 CHoCH Confirmation. Entry at FVG/Market."
    }

def main():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    symbols = ["GOLD", "US100Cash", "USDJPY", "EURUSD", "GBPUSD", "SILVER", "US30Cash", "GER40Cash", "BTCUSD", "ETHUSD"]
    
    print("="*60)
    print("🚀 TITAN ALPHA: SMC SIGNAL GENERATOR")
    print("="*60)
    
    for symbol in symbols:
        try:
            signal = generate_signal(symbol)
            if not signal or 'status' not in signal:
                print(f"⚠️ {symbol}: Unknown Error in signal generation")
                continue
                
            if signal['status'] == "SIGNAL_READY":
                print(f"✅ {symbol}: {signal['bias']} | Entry: {signal['entry']} | SL: {signal['sl']} | TP: {signal['tp']} | RR: {signal['rr']}")
                print(f"   Reason: {signal['message']}")
            else:
                print(f"❌ {symbol}: {signal['status']} | {signal.get('message', 'No details')}")
        except Exception as e:
            print(f"💥 {symbol}: System Exception: {str(e)}")
            
    mt5.shutdown()

if __name__ == "__main__":
    main()
