"""
SIMPLE VPA SCANNER
==================
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()
SYMBOLS = ['HGCOP-MAR26', 'MTU', 'SES', 'BTCUSD', 'ETHUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']

for s in SYMBOLS:
    # Resolve
    sym = None
    if mt5.symbol_info(s): sym = s
    else:
        found = [x.name for x in mt5.symbols_get() if s.split('-')[0] in x.name]
        if found: sym = found[0]
    
    if not sym:
        print(f"{s}: Not Found")
        continue
        
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 50)
    if rates is None: continue
    df = pd.DataFrame(rates)
    
    # Volume
    vol = df['real_volume'] if df['real_volume'].sum() > 0 else df['tick_volume']
    
    # Last completed
    last = df.iloc[-2]
    
    avg_vol = vol.iloc[-22:-2].mean()
    curr_vol = vol.iloc[-2]
    rel_vol = curr_vol / avg_vol
    
    spread = (df['high'] - df['low'])
    avg_spread = spread.iloc[-22:-2].mean()
    curr_spread = spread.iloc[-2]
    rel_spread = curr_spread / avg_spread
    
    is_up = last['close'] > last['open']
    
    status = "NORMAL"
    if rel_spread > 1.2 and rel_vol > 1.2: status = "VALID MOVE"
    if rel_spread > 1.2 and rel_vol < 0.8: status = "TRAP (Fakeout)"
    if rel_spread < 0.8 and rel_vol > 1.5: status = "BLOCKING (Reversal)"
    if is_up and rel_spread < 0.8 and rel_vol < 0.7: status = "NO DEMAND"
    
    print(f"{sym} | Vol: {rel_vol:.2f}x | Spread: {rel_spread:.2f}x | {status}")

mt5.shutdown()
