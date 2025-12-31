"""Quick Results Extractor - Get top strategies"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

def calc_indicators(df):
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    df['EMA50'] = df['close'].ewm(span=50).mean()
    df['EMA200'] = df['close'].ewm(span=200).mean()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    tr = pd.concat([df['high']-df['low'], abs(df['high']-df['close'].shift()), abs(df['low']-df['close'].shift())], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    return df

def test_ema_pullback(df, symbol):
    """EMA Pullback - Buy when price pulls back to EMA21 in uptrend"""
    signals = []
    for i in range(100, len(df)-10):
        c = df.iloc[i]
        p = df.iloc[i-1]
        # Uptrend check
        if c['EMA21'] > c['EMA50'] > c['EMA200']:
            if p['low'] <= p['EMA21'] and c['close'] > c['EMA21']:
                if 40 < c['RSI'] < 65:
                    signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
        elif c['EMA21'] < c['EMA50'] < c['EMA200']:
            if p['high'] >= p['EMA21'] and c['close'] < c['EMA21']:
                if 35 < c['RSI'] < 60:
                    signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
    
    if not signals:
        return None
    
    wins, losses, total_r = 0, 0, 0
    for s in signals:
        if s['idx'] + 10 >= len(df):
            continue
        exit_p = df.iloc[s['idx']+10]['close']
        pnl = (exit_p - s['entry']) * s['dir']
        r = pnl / s['risk'] if s['risk'] > 0 else 0
        if pnl > 0:
            wins += 1
        else:
            losses += 1
        total_r += r
    
    total = wins + losses
    if total < 15:
        return None
    
    return {
        'symbol': symbol,
        'strategy': 'EMA_Pullback',
        'signals': total,
        'wins': wins,
        'win_rate': wins/total*100,
        'expectancy': total_r/total,
        'total_r': total_r
    }

# Test key symbols
symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'GOLD', 'BTCUSD', 'US500', 'USTEC']
results = []

print("TESTING EMA PULLBACK STRATEGY")
print("="*50)

for sym in symbols:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 1500)
    if rates is None:
        continue
    df = calc_indicators(pd.DataFrame(rates))
    r = test_ema_pullback(df, sym)
    if r:
        results.append(r)
        status = "PROFITABLE" if r['expectancy'] > 0 else "LOSING"
        print(f"{sym}: {r['signals']} signals, {r['win_rate']:.1f}% win, {r['expectancy']:.2f}R exp - {status}")

print("\n" + "="*50)
print("SUMMARY")
print("="*50)

profitable = [r for r in results if r['expectancy'] > 0]
print(f"Profitable: {len(profitable)}/{len(results)} symbols")

if profitable:
    profitable.sort(key=lambda x: x['expectancy'], reverse=True)
    print("\nBEST PERFORMERS:")
    for r in profitable[:5]:
        print(f"  {r['symbol']}: {r['win_rate']:.1f}% win, {r['expectancy']:.2f}R, {r['signals']} trades")
    
    print(f"\nRECOMMENDATION: Trade EMA Pullback on {profitable[0]['symbol']}")

mt5.shutdown()
