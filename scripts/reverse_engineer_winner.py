"""
Reverse Engineer the Winning Manual Trades
Analyze what made the profitable GOLD longs successful
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

mt5.initialize()

positions = [p for p in mt5.positions_get() if 'GOLD' in p.symbol and p.profit > 5000]

print("="*70)
print("REVERSE ENGINEERING WINNING TRADES")
print("="*70)

for pos in positions:
    print(f"\n{'BUY' if pos.type == 0 else 'SELL'} {pos.symbol} @ {pos.price_open}")
    print(f"Current: {pos.price_current} | P/L: ${pos.profit:,.2f}")
    print(f"Entry Time: {datetime.fromtimestamp(pos.time)}")
    
    # Get market context AT ENTRY
    entry_time = pos.time
    
    # Fetch data from entry point
    rates_1d = mt5.copy_rates_from(pos.symbol, mt5.TIMEFRAME_D1, entry_time, 50)
    rates_4h = mt5.copy_rates_from(pos.symbol, mt5.TIMEFRAME_H4, entry_time, 100)
    rates_1h = mt5.copy_rates_from(pos.symbol, mt5.TIMEFRAME_H1, entry_time, 100)
    
    if rates_1d is not None:
        df_1d = pd.DataFrame(rates_1d)
        df_1d['sma50'] = df_1d['close'].rolling(50).mean()
        entry_vs_1d_sma = "ABOVE" if pos.price_open > df_1d['sma50'].iloc[-1] else "BELOW"
        
        df_4h = pd.DataFrame(rates_4h)
        df_4h['sma50'] = df_4h['close'].rolling(50).mean()
        entry_vs_4h_sma = "ABOVE" if pos.price_open > df_4h['sma50'].iloc[-1] else "BELOW"
        
        df_1h = pd.DataFrame(rates_1h)
        delta = df_1h['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df_1h['rsi'] = 100 - (100 / (1 + gain/loss))
        entry_rsi = df_1h['rsi'].iloc[-1]
        
        print(f"\nMARKET CONTEXT AT ENTRY:")
        print(f"  1D Trend: Entry was {entry_vs_1d_sma} 1D SMA50")
        print(f"  4H Trend: Entry was {entry_vs_4h_sma} 4H SMA50")
        print(f"  1H RSI: {entry_rsi:.1f}")
        
        # THE WINNING LOGIC
        if pos.type == 0:  # BUY
            print(f"\n✅ WINNING EDGE IDENTIFIED:")
            if entry_vs_1d_sma == "ABOVE" and entry_vs_4h_sma == "ABOVE":
                print(f"  → Bought WITH the 1D/4H trend (Trend Following)")
            if 30 < entry_rsi < 50:
                print(f"  → Bought on a shallow pullback (Smart entry)")
            elif entry_rsi < 30:
                print(f"  → Bought extreme oversold (Contrarian but trend-aligned)")

mt5.shutdown()
