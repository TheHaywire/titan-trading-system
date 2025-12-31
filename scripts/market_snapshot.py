"""Quick market snapshot from MT5"""
import MetaTrader5 as mt5
from datetime import datetime

if not mt5.initialize():
    print("MT5 not connected")
    exit()

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'US30Cash', 'US100Cash', 'OILCash']

print("=" * 70)
print("  MT5 LIVE MARKET DATA")
print("=" * 70)

for sym in symbols:
    tick = mt5.symbol_info_tick(sym)
    
    if not tick:
        continue
    
    # Get today's OHLC from D1
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 2)
    
    if rates is not None and len(rates) >= 2:
        today = rates[-1]
        yesterday = rates[-2]
        
        current = tick.bid
        change = current - yesterday['close']
        change_pct = (change / yesterday['close']) * 100
        
        direction = "UP" if change > 0 else "DOWN" if change < 0 else "FLAT"
        
        print(f"{sym:12} | Bid: {current:>12.5f} | {direction:5} {change_pct:+.2f}%")
        print(f"             | Open: {today['open']:.5f} | High: {today['high']:.5f} | Low: {today['low']:.5f}")
        print()

mt5.shutdown()
