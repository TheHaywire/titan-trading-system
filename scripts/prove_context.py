"""
CONTEXT VALIDATOR (The "Forensic" Proof)
========================================
Proves that the system sees the entire chart, from Monthly down to 1-Minute.
Extracts:
- Monthly/Weekly Levels (Big Structure)
- Daily/H4 Trends (Medium Structure)
- H1/M15/M1 Execution (Immediate Structure)
"""

import sys
import os
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

# Import our actual analysis engines to use them
from titan_system.smc.liquidity import LiquidityEngine
from titan_system.smc.market_structure import MarketStructure
from titan_system.smc.fvg import FVGDetector

def get_data(symbol, timeframe, count=500):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def analyze_timeframe(symbol, tf_name, tf_const):
    print(f"🔍 Analyzing {tf_name}...", end="\r")
    df = get_data(symbol, tf_const)
    if df is None: return None
    
    liq = LiquidityEngine().analyze(df, symbol)
    struct = MarketStructure(swing_length=5).analyze(df)
    
    # Calculate simple trend
    sma50 = df['close'].rolling(50).mean().iloc[-1]
    sma200 = df['close'].rolling(200).mean().iloc[-1]
    trend_ema = "BULLISH" if sma50 > sma200 else "BEARISH"
    
    return {
        "trend_ema": trend_ema,
        "structure": struct.get('trend', 'Neutral'),
        "last_swing_high": struct.get('last_swing_high', {}).get('price'),
        "last_swing_low": struct.get('last_swing_low', {}).get('price'),
        "sweeps": [s['sweep_type'] for s in liq.get('sweeps', [])],
        "current_price": df['close'].iloc[-1]
    }

def prove_context(symbol):
    if not mt5.initialize():
        print("MT5 Failed")
        return

    print("="*60)
    print(f"🏛️ INSTITUTIONAL CONTEXT PROOF: {symbol}")
    print(f"   Time: {datetime.now()}")
    print("="*60)

    timeframes = [
        ("MN1 (Monthly)", mt5.TIMEFRAME_MN1),
        ("W1  (Weekly)", mt5.TIMEFRAME_W1),
        ("D1  (Daily)", mt5.TIMEFRAME_D1),
        ("H4  (4-Hour)", mt5.TIMEFRAME_H4),
        ("H1  (1-Hour)", mt5.TIMEFRAME_H1),
        ("M15 (Execution)", mt5.TIMEFRAME_M15),
        ("M1  (Micro)", mt5.TIMEFRAME_M1)
    ]
    
    context = {}
    
    for name, tf in timeframes:
        res = analyze_timeframe(symbol, name, tf)
        if res:
            context[name] = res
            print(f"✅ {name:<15} | Bias: {res['trend_ema']:<8} | Struct: {res['structure']:<8} | High: {res['last_swing_high']} | Low: {res['last_swing_low']}")
            if res['sweeps']:
                print(f"   └── 🧹 SWEEP DETECTED: {res['sweeps']}")
    
    print("-" * 60)
    print("🧠 SYNTHESIS:")
    
    # Check alignment
    mn_bias = context.get("MN1 (Monthly)", {}).get("trend_ema")
    w1_bias = context.get("W1  (Weekly)", {}).get("trend_ema")
    h1_bias = context.get("H1  (1-Hour)", {}).get("trend_ema")
    
    if mn_bias == w1_bias == h1_bias:
        print(f"   🌟 FULL ALIGNMENT ({mn_bias}) from Monthly down to H1")
    else:
        print(f"   ⚠️ CONFLICT: Monthly is {mn_bias} but H1 is {h1_bias}")
        
    print(f"   🎯 FINAL VERDICT: The system sees {len(context)} distinct timeframes.")
    
    mt5.shutdown()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="ETHUSD")
    args = parser.parse_args()
    prove_context(args.symbol)
