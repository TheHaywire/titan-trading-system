"""Quick Market Scan - Find Best Setup Right Now"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

if not mt5.initialize():
    print("MT5 connection failed")
    exit()

# Your broker's actual symbols
symbols = ['GOLD', 'US100Cash', 'US30Cash', 'GER40Cash', 'EURUSD', 'GBPUSD', 'USDJPY', 'BTCUSD', 'ETHUSD']

print("=" * 60)
print("🔍 LIVE MARKET SCAN - Finding Best Setup")
print("=" * 60)

best_setup = None
best_score = 0

for sym in symbols:
    try:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None or len(rates) < 50:
            continue
        
        df = pd.DataFrame(rates)
        tick = mt5.symbol_info_tick(sym)
        if tick is None:
            continue
        price = tick.bid
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # ATR
        tr = (df['high'] - df['low']).rolling(14).mean().iloc[-1]
        atr_pct = (tr / price) * 100
        
        # Trend
        sma20 = df['close'].rolling(20).mean().iloc[-1]
        sma50 = df['close'].rolling(50).mean().iloc[-1]
        trend = 'BULLISH' if price > sma20 > sma50 else 'BEARISH' if price < sma20 < sma50 else 'RANGING'
        
        # Score
        score = 0
        signal = None
        reason = ""
        
        if current_rsi < 30:
            score = 85
            signal = 'BUY'
            reason = f'RSI Oversold ({current_rsi:.1f})'
        elif current_rsi > 70:
            score = 85
            signal = 'SELL'
            reason = f'RSI Overbought ({current_rsi:.1f})'
        elif trend == 'BULLISH' and 40 < current_rsi < 55:
            score = 70
            signal = 'BUY'
            reason = 'Bullish Trend Pullback'
        elif trend == 'BEARISH' and 45 < current_rsi < 60:
            score = 70
            signal = 'SELL'
            reason = 'Bearish Trend Pullback'
        elif trend == 'BULLISH':
            score = 55
            signal = 'BUY'
            reason = 'With Trend'
        elif trend == 'BEARISH':
            score = 55
            signal = 'SELL'
            reason = 'With Trend'
        
        if atr_pct > 0.3:
            score += 10
        
        if score > 0:
            status = "⭐⭐⭐" if score >= 75 else "⭐⭐" if score >= 60 else "⭐"
            print(f"{status} {sym}: {signal} | Score: {score} | RSI: {current_rsi:.1f} | {trend}")
            
            if score > best_score:
                best_score = score
                best_setup = {'sym': sym, 'sig': signal, 'price': price, 'rsi': current_rsi, 
                             'trend': trend, 'atr': tr, 'reason': reason, 'score': score}
    except Exception as e:
        print(f"Error {sym}: {e}")

print()
print("=" * 60)
if best_setup:
    s = best_setup
    sl_dist = s['atr'] * 1.5
    tp_dist = s['atr'] * 2.5
    
    if s['sig'] == 'BUY':
        sl = s['price'] - sl_dist
        tp = s['price'] + tp_dist
    else:
        sl = s['price'] + sl_dist
        tp = s['price'] - tp_dist
    
    print(f"🎯 BEST SETUP: {s['sym']}")
    print(f"   Direction:   {s['sig']}")
    print(f"   Entry:       {s['price']:.5f}")
    print(f"   Stop Loss:   {sl:.5f}")
    print(f"   Take Profit: {tp:.5f}")
    print(f"   R:R Ratio:   1:{tp_dist/sl_dist:.1f}")
    print(f"   Confidence:  {s['score']}/100")
    print(f"   Reason:      {s['reason']}")
    print()
    print("   Reply 'EXECUTE' to place this trade!")
else:
    print("No clear setups. Markets may be ranging.")
print("=" * 60)

mt5.shutdown()
