"""
TEST GOLD vs COPPER MOMENTUM
============================
We found:
1. HGCOP-MAR26 (Copper Future) -> Sharpe 2.16 (We know this works)
2. XAUUSD (Spot Gold)
3. GOLD (Barrick Gold Corp - Stock) -> NOT the commodity!

We need to test XAUUSD (Spot) to see if Chan's strategy works there too.
If XAUUSD fails (due to costs/swaps), we stick with Copper.
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

def test_momentum(symbol, name):
    print(f"\n📊 TESTING: {name} ({symbol})")
    
    # Check if symbol exists
    if not mt5.symbol_info(symbol):
        print("❌ Symbol not found")
        return

    # Get Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 500)
    if rates is None:
        print("❌ No Data")
        return
    df = pd.DataFrame(rates)
    
    # Strategy: Buy High (>250d), Sell Low
    LOOKBACK = 250
    HOLD = 25
    
    trades = []
    
    for i in range(LOOKBACK, len(df)-HOLD, HOLD):
        curr = df.iloc[i]['close']
        past = df.iloc[i-LOOKBACK]['close']
        
        direction = 1 if curr > past else -1
        
        entry = df.iloc[i]['close']
        exit_p = df.iloc[i+HOLD]['close']
        
        # Gross Return
        if direction == 1: ret = (exit_p - entry)
        else: ret = (entry - exit_p)
        
        trades.append(ret)
        
    # Analysis
    if not trades: return
    
    total = sum(trades)
    avg = np.mean(trades)
    
    # Simple Sharpe Proxy (Mean / Std)
    sharpe = (avg / np.std(trades)) * np.sqrt(10) # Annualized
    
    print(f"   Total Return: {total:.2f}")
    print(f"   Sharpe Ratio: {sharpe:.2f}")
    print(f"   Verdict: {'✅ WORKS' if sharpe > 1.0 else '❌ FAILS'}")

print("COMPARING GOLD INSTRUMENTS:")
test_momentum("HGCOP-MAR26", "Copper Future")
test_momentum("XAUUSD", "Spot Gold")
test_momentum("GOLD", "Barrick Gold (Stock)")

mt5.shutdown()
