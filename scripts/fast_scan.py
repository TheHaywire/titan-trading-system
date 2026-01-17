import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import numpy as np

# Fast, targeted scan
symbols = [
    # Metals
    "GOLD", "SILVER", "COPPER", "PLATINUM", "PALLADIUM",
    # Major Forex
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
    # Crosses
    "EURJPY", "GBPJPY", "AUDJPY", "EURGBP", "EURAUD", "GBPAUD", "EURCHO", "GBPCAD",
    # Indices  
    "US100", "US100Cash", "US500", "US500Cash", "US30", "US30Cash",
    "GER40", "GER40Cash", "UK100", "UK100Cash", "JPN225", "JPN225Cash",
    "AUS200", "AUS200Cash", "ESP35", "ESP35Cash", "FRA40", "FRA40Cash",
    # Crypto
    "BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD", "BCHUSD", "EOSUSD",
    # Oil & Energy
    "USOIL", "UKOIL", "NGAS",
]

if not mt5.initialize():
    print("MT5 failed")
    exit()

print("="*100)
print(f"⚡ FAST HIGH R:R SCANNER - {datetime.now().strftime('%H:%M:%S')}")
print("="*100)
print(f"\nScanning {len(symbols)} high-quality symbols...\n")

setups = []

for symbol in symbols:
    try:
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
            
        current = tick.bid
        
        h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
        
        if h1 is None or m15 is None or len(h1) < 50:
            continue
        
        df_h1 = pd.DataFrame(h1)
        df_m15 = pd.DataFrame(m15)
        
        # Calculate RSI
        def rsi(prices, period=14):
            deltas = np.diff(prices)
            seed = deltas[:period+1]
            up = seed[seed >= 0].sum()/period
            down = -seed[seed < 0].sum()/period
            rs = up/down if down != 0 else 0
            r = np.zeros_like(prices)
            r[:period] = 100. - 100./(1. + rs)
            for i in range(period, len(prices)):
                delta = deltas[i-1]
                upval = delta if delta > 0 else 0
                downval = -delta if delta < 0 else 0
                up = (up*(period-1) + upval)/period
                down = (down*(period-1) + downval)/period
                rs = up/down if down != 0 else 0
                r[i] = 100. - 100./(1. + rs)
            return r
        
        rsi_val = rsi(df_h1['close'].values)[-1]
        
        # Trends
        h1_ema20 = df_h1['close'].ewm(span=20).mean().iloc[-1]
        h1_ema50 = df_h1['close'].ewm(span=50).mean().iloc[-1]
        m15_ema20 = df_m15['close'].ewm(span=20).mean().iloc[-1]
        
        h1_trend = "UP" if h1_ema20 > h1_ema50 else "DOWN"
        m15_trend = "UP" if current > m15_ema20 else "DOWN"
        aligned = (h1_trend == m15_trend)
        
        # ATR
        df_h1['tr'] = df_h1.apply(lambda r: max(r['high']-r['low'], abs(r['high']-r['close']), abs(r['low']-r['close'])), axis=1)
        atr = df_h1['tr'].tail(14).mean()
        
        # Skip if not aligned
        if not aligned:
            continue
        
        direction = "LONG" if h1_trend == "UP" else "SHORT"
        
        # Calculate levels
        if direction == "LONG":
            sl = current - (atr * 1.5)
            tp1 = current + (atr * 3)
            tp2 = current + (atr * 4)
            tp3 = current + (atr * 5)
        else:
            sl = current + (atr * 1.5)
            tp1 = current - (atr * 3)
            tp2 = current - (atr * 4)
            tp3 = current - (atr * 5)
        
        # R:R
        risk = abs(current - sl)
        rr1 = abs(tp1 - current) / risk if risk > 0 else 0
        rr2 = abs(tp2 - current) / risk if risk > 0 else 0
        rr3 = abs(tp3 - current) / risk if risk > 0 else 0
        
        # Only keep if R:R >= 2.5
        if rr3 < 2.5:
            continue
        
        # Score
        score = 30  # Base for alignment
        
        if direction == "LONG" and 30 < rsi_val < 60:
            score += 25
        elif direction == "SHORT" and 40 < rsi_val < 70:
            score += 25
        
        last_5 = df_m15['close'].tail(5).values
        if (last_5[-1] > last_5[0] and direction == "LONG") or (last_5[-1] < last_5[0] and direction == "SHORT"):
            score += 20
        
        if abs(current - m15_ema20) / current < 0.005:
            score += 15
        
        if rr3 >= 5:
            score += 20
        elif rr3 >= 4:
            score += 15
        elif rr3 >= 3:
            score += 10
        
        setups.append({
            'symbol': symbol,
            'score': score,
            'direction': direction,
            'entry': current,
            'sl': sl,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'rr1': rr1,
            'rr2': rr2,
            'rr3': rr3,
            'rsi': rsi_val,
            'trend': h1_trend,
        })
        
    except:
        pass

# Sort and display
setups.sort(key=lambda x: x['rr3'], reverse=True)

print("\n" + "="*100)
print("💎 TOP HIGH R:R SETUPS (Sorted by Risk:Reward)")
print("="*100 + "\n")

if not setups:
    print("❌ No setups found meeting criteria (aligned trends + R:R >= 2.5:1)\n")
else:
    for i, s in enumerate(setups[:15], 1):
        print(f"{i}. {s['symbol']:<12} {s['direction']:<5} | Score: {s['score']:<3} | R:R: {s['rr3']:.2f}:1 ⭐")
        print(f"   Entry: {s['entry']:<10.5f} | SL: {s['sl']:<10.5f} | TP: {s['tp3']:<10.5f}")
        print(f"   RSI: {s['rsi']:.1f} | Trend: {s['trend']}")
        print()

print("="*100)
print(f"Found {len(setups)} high-quality setups")
print("="*100)

mt5.shutdown()
