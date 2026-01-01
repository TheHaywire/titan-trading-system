"""
TEST GOLD PROXY (GAUUSD)
========================
Standard XAUUSD is missing. We found GAUUSD (Gold Grams).
Hypothesis: Trends in Gold/Oz (XAU) should match Gold/Gram (GAU).
Tests Momentum Strategy on GAUUSD.
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

def test_proxy(symbol, name):
    print(f"\n📊 TESTING PROXY: {name} ({symbol})")
    
    if not mt5.symbol_info(symbol):
        print("❌ Symbol not found")
        return

    # Get Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 700) # 2+ Years
    if rates is None:
        print("❌ No Data")
        return
    df = pd.DataFrame(rates)
    
    print(f"   Data: {len(df)} days. Price: {df.iloc[-1]['close']}")
    
    # Strategy
    LOOKBACK = 250
    HOLD = 25
    trades = []
    
    for i in range(LOOKBACK, len(df)-HOLD, HOLD):
        curr = df.iloc[i]['close']
        past = df.iloc[i-LOOKBACK]['close']
        
        direction = 1 if curr > past else -1
        
        entry = df.iloc[i]['close']
        exit_p = df.iloc[i+HOLD]['close']
        
        if direction == 1: ret = (exit_p - entry)
        else: ret = (entry - exit_p)
        
        trades.append(ret)

    if not trades: return
    
    total = sum(trades)
    avg = np.mean(trades)
    std = np.std(trades)
    sharpe = (avg / std * np.sqrt(10)) if std > 0 else 0
    
    print(f"   Total Return (Points): {total:.2f}")
    print(f"   Sharpe Ratio: {sharpe:.2f}")
    print(f"   Win Rate: {len([t for t in trades if t>0])/len(trades)*100:.1f}%")
    print(f"   Verdict: {'✅ VIABLE GOLD PROXY' if sharpe > 1.0 else '❌ FAILED'}")

test_proxy("GAUUSD", "Gold Grams")
test_proxy("XAUJPY", "Gold Yen")

mt5.shutdown()
