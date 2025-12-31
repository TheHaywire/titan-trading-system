"""Simple trade reasoning report"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd

mt5.initialize()

positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    exit()

print("TRADE REASONING REPORT")
print("="*50)

for pos in positions:
    print(f"\n{pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots")
    print(f"Entry: {pos.price_open} | Current: {pos.price_current}")
    print(f"P/L: ${pos.profit:.2f}")
    
    # Get data
    rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_M15, 0, 50)
    if rates is None:
        continue
    df = pd.DataFrame(rates)
    
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    df['MOM'] = df['close'].pct_change(5) * 100
    
    c = df.iloc[-1]
    direction = 'BUY' if pos.type == 0 else 'SELL'
    
    # Why
    reasons = []
    if c['EMA9'] > c['EMA21']:
        reasons.append("EMA9 > EMA21 (Bullish)")
    else:
        reasons.append("EMA9 < EMA21 (Bearish)")
    
    if c['RSI'] < 30:
        reasons.append(f"RSI oversold ({c['RSI']:.0f})")
    elif c['RSI'] > 70:
        reasons.append(f"RSI overbought ({c['RSI']:.0f})")
    else:
        reasons.append(f"RSI neutral ({c['RSI']:.0f})")
    
    if c['MOM'] > 0.3:
        reasons.append(f"Bullish momentum +{c['MOM']:.1f}%")
    elif c['MOM'] < -0.3:
        reasons.append(f"Bearish momentum {c['MOM']:.1f}%")
    
    print("WHY: " + " | ".join(reasons))
    
    # SL/TP
    info = mt5.symbol_info(pos.symbol)
    point = info.point
    sl_pts = abs(pos.price_open - pos.sl) / point if pos.sl else 0
    tp_pts = abs(pos.tp - pos.price_open) / point if pos.tp else 0
    rr = tp_pts / sl_pts if sl_pts > 0 else 0
    
    print(f"SL: {sl_pts:.0f} pts | TP: {tp_pts:.0f} pts | R:R = 1:{rr:.1f}")
    
    # Confidence
    aligned = (direction == 'BUY' and c['EMA9'] > c['EMA21']) or \
              (direction == 'SELL' and c['EMA9'] < c['EMA21'])
    conf = "HIGH" if aligned else "LOW (against trend)"
    print(f"Confidence: {conf}")

mt5.shutdown()
