"""
SCAN ALL MT5 SYMBOLS
====================
Scans ALL available symbols for trading opportunities.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

mt5.initialize()

# Get ALL symbols
all_symbols = mt5.symbols_get()
print(f"Total symbols in MT5: {len(all_symbols)}")

# Filter tradeable symbols
tradeable = [s for s in all_symbols if s.visible and s.trade_mode != 0]
print(f"Tradeable symbols: {len(tradeable)}")

# Categorize
categories = {
    "FOREX_MAJOR": [],
    "FOREX_MINOR": [],
    "CRYPTO": [],
    "INDICES": [],
    "COMMODITIES": [],
    "STOCKS": [],
    "OTHER": []
}

for s in tradeable:
    name = s.name
    if any(x in name for x in ["BTC", "ETH", "XRP", "SOL", "DOGE", "LTC", "ADA"]):
        categories["CRYPTO"].append(name)
    elif any(x in name for x in ["US500", "US30", "USTEC", "GER40", "UK100", "JP225", "NAS", "SPX", "DOW"]):
        categories["INDICES"].append(name)
    elif any(x in name for x in ["GOLD", "XAU", "SILVER", "XAG", "OIL", "WTI", "BRENT", "COPPER"]):
        categories["COMMODITIES"].append(name)
    elif len(name) == 6 and all(c.isalpha() for c in name):
        if "USD" in name or "EUR" in name or "GBP" in name or "JPY" in name:
            categories["FOREX_MAJOR"].append(name)
        else:
            categories["FOREX_MINOR"].append(name)
    elif "." in name or any(c.isdigit() for c in name[:3]):
        categories["STOCKS"].append(name)
    else:
        categories["OTHER"].append(name)

print("\nSYMBOLS BY CATEGORY:")
for cat, syms in categories.items():
    if syms:
        print(f"  {cat}: {len(syms)} symbols")

# Scan for opportunities
print("\n" + "="*60)
print("SCANNING FOR OPPORTUNITIES...")
print("="*60)

opportunities = []

# Scan priority categories first
priority = categories["FOREX_MAJOR"] + categories["CRYPTO"] + categories["INDICES"] + categories["COMMODITIES"]

scanned = 0
for sym in priority[:100]:  # Limit to first 100 for speed
    try:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 50)
        if rates is None or len(rates) < 30:
            continue
        
        df = pd.DataFrame(rates)
        
        # Quick indicators
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        df['MOM'] = df['close'].pct_change(5) * 100
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        signal = None
        score = 0
        
        # Check for signals
        if curr['RSI'] < 25:
            signal = "BUY"
            score = 90
            reason = f"RSI Oversold ({curr['RSI']:.0f})"
        elif curr['RSI'] > 75:
            signal = "SELL"
            score = 90
            reason = f"RSI Overbought ({curr['RSI']:.0f})"
        elif prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']:
            signal = "BUY"
            score = 80
            reason = "EMA Bullish Cross"
        elif prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']:
            signal = "SELL"
            score = 80
            reason = "EMA Bearish Cross"
        elif curr['MOM'] > 1.0:
            signal = "BUY"
            score = 70
            reason = f"Strong Momentum +{curr['MOM']:.1f}%"
        elif curr['MOM'] < -1.0:
            signal = "SELL"
            score = 70
            reason = f"Strong Momentum {curr['MOM']:.1f}%"
        
        if signal:
            opportunities.append({
                'symbol': sym,
                'signal': signal,
                'score': score,
                'reason': reason,
                'price': curr['close'],
                'rsi': curr['RSI'],
                'mom': curr['MOM']
            })
        
        scanned += 1
        
    except Exception as e:
        pass

print(f"\nScanned: {scanned} symbols")

# Sort by score
opportunities.sort(key=lambda x: x['score'], reverse=True)

print(f"\nFOUND {len(opportunities)} OPPORTUNITIES:")
print("-"*60)

for opp in opportunities[:20]:  # Top 20
    print(f"{opp['signal']:4} {opp['symbol']:12} | Score: {opp['score']} | {opp['reason']}")
    print(f"     Price: {opp['price']:.5f} | RSI: {opp['rsi']:.0f} | Mom: {opp['mom']:.1f}%")
    print()

mt5.shutdown()
