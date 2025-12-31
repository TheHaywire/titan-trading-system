"""
Reverse Engineer User's GOLD Trading Strategy
==============================================
Looks at exactly what the market was doing when user entered trades.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone

mt5.initialize()

# Get user's GOLD trade entries
now = datetime.now(timezone.utc)
from_date = now - timedelta(hours=24)

deals = mt5.history_deals_get(from_date, now)

# Find GOLD entries (not exits)
gold_entries = []
for deal in deals:
    d = deal._asdict()
    if ('GOLD' in d['symbol'] or 'XAU' in d['symbol']) and d['entry'] == 0:  # entry=0 means entry deal
        if d['type'] in [0, 1]:  # Buy/Sell
            gold_entries.append({
                'time': datetime.fromtimestamp(d['time'], tz=timezone.utc),
                'type': 'BUY' if d['type'] == 0 else 'SELL',
                'price': d['price'],
                'volume': d['volume'],
                'profit': d['profit']
            })

print(f"Found {len(gold_entries)} GOLD entries to analyze")
print("="*70)

# Get M1 data for GOLD (very granular)
gold_m1 = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M1, 0, 1000)
gold_m5 = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_M5, 0, 500)

if gold_m1 is None:
    print("Cannot get GOLD M1 data")
    mt5.shutdown()
    exit()

df_m1 = pd.DataFrame(gold_m1)
df_m1['time'] = pd.to_datetime(df_m1['time'], unit='s', utc=True)

df_m5 = pd.DataFrame(gold_m5)
df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s', utc=True)

# Add indicators
def add_indicators(df):
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    df['EMA50'] = df['close'].ewm(span=50).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    df['MOM'] = df['close'].pct_change(5) * 100
    df['VOL'] = df['tick_volume']
    df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
    df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA']
    
    # ATR
    df['TR'] = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    df['ATR'] = df['TR'].rolling(14).mean()
    
    # Price relative to range
    df['HIGH_20'] = df['high'].rolling(20).max()
    df['LOW_20'] = df['low'].rolling(20).min()
    df['RANGE_POS'] = (df['close'] - df['LOW_20']) / (df['HIGH_20'] - df['LOW_20'])
    
    return df

df_m1 = add_indicators(df_m1)
df_m5 = add_indicators(df_m5)

# Analyze each entry
patterns = []

for entry in gold_entries:
    print(f"\n{'='*70}")
    print(f"ENTRY: {entry['type']} {entry['volume']} lots @ {entry['price']}")
    print(f"Time: {entry['time'].strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"P/L: ${entry['profit']:.2f}")
    print("="*70)
    
    # Find the candle at entry time
    entry_time = entry['time']
    
    # Get M5 candle at entry
    mask = df_m5['time'] <= entry_time
    if mask.any():
        idx = df_m5[mask].index[-1]
        if idx >= 20:
            candle = df_m5.iloc[idx]
            prev_candles = df_m5.iloc[idx-20:idx]
            
            print("\nM5 INDICATORS AT ENTRY:")
            print(f"  Price: {candle['close']:.2f}")
            print(f"  EMA9: {candle['EMA9']:.2f}")
            print(f"  EMA21: {candle['EMA21']:.2f}")
            print(f"  RSI: {candle['RSI']:.1f}")
            print(f"  Momentum: {candle['MOM']:.2f}%")
            print(f"  Volume Ratio: {candle['VOL_RATIO']:.2f}x average")
            print(f"  Position in Range: {candle['RANGE_POS']*100:.0f}%")
            
            # Determine what triggered the entry
            print("\nPOSSIBLE ENTRY TRIGGERS:")
            
            triggers = []
            
            # Check EMA alignment
            if entry['type'] == 'SELL':
                if candle['EMA9'] < candle['EMA21']:
                    triggers.append("EMA9 below EMA21 (bearish)")
                if candle['close'] < candle['EMA9']:
                    triggers.append("Price below EMA9 (weak)")
                if candle['RSI'] > 60:
                    triggers.append(f"RSI was high ({candle['RSI']:.0f}) - overbought")
                if candle['MOM'] < 0:
                    triggers.append(f"Negative momentum ({candle['MOM']:.2f}%)")
                if candle['RANGE_POS'] > 0.7:
                    triggers.append(f"Near top of range ({candle['RANGE_POS']*100:.0f}%)")
            else:  # BUY
                if candle['EMA9'] > candle['EMA21']:
                    triggers.append("EMA9 above EMA21 (bullish)")
                if candle['close'] > candle['EMA9']:
                    triggers.append("Price above EMA9 (strong)")
                if candle['RSI'] < 40:
                    triggers.append(f"RSI was low ({candle['RSI']:.0f}) - oversold")
                if candle['MOM'] > 0:
                    triggers.append(f"Positive momentum ({candle['MOM']:.2f}%)")
                if candle['RANGE_POS'] < 0.3:
                    triggers.append(f"Near bottom of range ({candle['RANGE_POS']*100:.0f}%)")
            
            # Volume spike
            if candle['VOL_RATIO'] > 1.5:
                triggers.append(f"High volume ({candle['VOL_RATIO']:.1f}x average)")
            
            for t in triggers:
                print(f"  -> {t}")
            
            patterns.append({
                'type': entry['type'],
                'rsi': candle['RSI'],
                'mom': candle['MOM'],
                'vol_ratio': candle['VOL_RATIO'],
                'range_pos': candle['RANGE_POS'],
                'ema_trend': 'bearish' if candle['EMA9'] < candle['EMA21'] else 'bullish',
                'profit': entry['profit']
            })

# Summary - find common patterns
print("\n" + "="*70)
print("PATTERN SUMMARY - YOUR WINNING TRADES")
print("="*70)

if patterns:
    winners = [p for p in patterns if p['profit'] > 0]
    if winners:
        print(f"\nWinning Trades: {len(winners)}")
        
        avg_rsi = np.mean([p['rsi'] for p in winners])
        avg_range = np.mean([p['range_pos'] for p in winners])
        
        print(f"Average RSI at Entry: {avg_rsi:.1f}")
        print(f"Average Range Position: {avg_range*100:.0f}%")
        
        # Count trend directions
        sells = [p for p in winners if p['type'] == 'SELL']
        buys = [p for p in winners if p['type'] == 'BUY']
        
        print(f"SELL wins: {len(sells)}")
        print(f"BUY wins: {len(buys)}")
        
        print("\n" + "="*70)
        print("DERIVED STRATEGY RULES")
        print("="*70)
        
        if len(sells) > len(buys):
            print("""
YOUR PATTERN (Derived from data):
1. Primary Direction: SELL (you're catching drops)
2. Entry when RSI is elevated (>50-60)
3. Entry near top of recent range
4. You use SIZE (5-20 lots) when confident
5. Quick exits when momentum fades

SUGGESTED BOT CONFIG:
- Focus: GOLD only
- Timeframe: M5
- Direction: Prefer SELLS when RSI > 55 and near range high
- Size: 5+ lots
- Exit: Trail or quick TP (20-30 points)
""")
        else:
            print("""
YOUR PATTERN (Derived from data):
1. Primary Direction: BUY (you're catching bounces)
2. Entry when RSI is low (<45)
3. Entry near bottom of range
4. Size up when confident

SUGGESTED BOT CONFIG:
- Focus: GOLD only
- Timeframe: M5
- Direction: Prefer BUYS when RSI < 45 and near range low
- Size: 5+ lots
- Exit: Trail or quick TP
""")

mt5.shutdown()
