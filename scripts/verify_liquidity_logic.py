
import sys
import os
sys.path.append(os.getcwd())

import pandas as pd
from titan_system.strategies.liquidity_hunter import LiquidityHunterStrategy

print("🧪 Verifying Liquidity Hunter (Fakeout) Logic...")

# 1. Create Synthetic Data simulating a "Bull Trap"
# Price goes UP, breaks high, then CLOSES back below high.
data = {
    'time': pd.date_range(start='2024-01-01', periods=50, freq='5min'),
    'open': [100.0] * 50,
    'high': [100.5] * 50,
    'low': [99.5] * 50,
    'close': [100.0] * 50,
    'tick_volume': [100] * 50
}
df = pd.DataFrame(data)

# Set a "Resistance" at index 30
df.loc[30, 'high'] = 105.0 # The "High" to beat

# Candle 48: The Breakout Candle (Wick goes above 105, Close below 105)
df.loc[48, 'high'] = 106.0 # Break!
df.loc[48, 'close'] = 104.0 # Close back inside (Fakeout)

print(f"Candle 48 High: {df.loc[48, 'high']}, Close: {df.loc[48, 'close']}")
print(f"Resistance Level (Candle 30): {df.loc[30, 'high']}")

# 2. Run Strategy
strategy = LiquidityHunterStrategy()
try:
    # Need at least 50 candles
    signal = strategy.analyze(df)
    
    if signal:
        print("\n✅ SIGNAL GENERATED:")
        print(signal)
        if signal['setup'] == 'BEARISH_SWEEP':
             print("🎯 Correctly identified Bearish Sweep (Bull Trap)")
        else:
             print("❓ Wrong signal type?")
    else:
        print("\n❌ NO SIGNAL (Method returned None)")

except Exception as e:
    print(f"\n❌ Error during execution: {e}")
