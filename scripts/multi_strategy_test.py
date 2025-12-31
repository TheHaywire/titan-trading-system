"""
Multi-Strategy Backtest - Find Best Setup
Tests 5 strategies across multiple symbols and timeframes
"""
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
    df['BB_MID'] = df['close'].rolling(20).mean()
    df['BB_STD'] = df['close'].rolling(20).std()
    df['BB_UPPER'] = df['BB_MID'] + 2*df['BB_STD']
    df['BB_LOWER'] = df['BB_MID'] - 2*df['BB_STD']
    return df

def backtest_strategy(df, strategy_func, name, symbol):
    signals = strategy_func(df)
    if len(signals) < 10:
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
    if total < 10:
        return None
    
    return {
        'symbol': symbol,
        'strategy': name,
        'signals': total,
        'wins': wins,
        'win_rate': wins/total*100,
        'expectancy': total_r/total,
        'total_r': total_r
    }

# Strategy 1: EMA Crossover 9/21
def strat_ema_cross(df):
    signals = []
    for i in range(50, len(df)-10):
        c, p = df.iloc[i], df.iloc[i-1]
        if p['EMA9'] <= p['EMA21'] and c['EMA9'] > c['EMA21'] and c['close'] > c['EMA50']:
            signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
        elif p['EMA9'] >= p['EMA21'] and c['EMA9'] < c['EMA21'] and c['close'] < c['EMA50']:
            signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
    return signals

# Strategy 2: RSI Reversal
def strat_rsi(df):
    signals = []
    for i in range(50, len(df)-10):
        c, p = df.iloc[i], df.iloc[i-1]
        if p['RSI'] < 30 and c['RSI'] > 30 and c['close'] > c['EMA50']:
            signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
        elif p['RSI'] > 70 and c['RSI'] < 70 and c['close'] < c['EMA50']:
            signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
    return signals

# Strategy 3: EMA Pullback
def strat_pullback(df):
    signals = []
    for i in range(100, len(df)-10):
        c, p = df.iloc[i], df.iloc[i-1]
        if c['EMA21'] > c['EMA50'] > c['EMA200']:
            if p['low'] <= p['EMA21'] and c['close'] > c['EMA21'] and 40 < c['RSI'] < 65:
                signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
        elif c['EMA21'] < c['EMA50'] < c['EMA200']:
            if p['high'] >= p['EMA21'] and c['close'] < c['EMA21'] and 35 < c['RSI'] < 60:
                signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
    return signals

# Strategy 4: Momentum Breakout
def strat_breakout(df):
    signals = []
    for i in range(50, len(df)-10):
        c = df.iloc[i]
        high20 = df.iloc[i-20:i]['high'].max()
        low20 = df.iloc[i-20:i]['low'].min()
        if c['close'] > high20 + 0.5*c['ATR'] and c['RSI'] > 50:
            signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']*1.5})
        elif c['close'] < low20 - 0.5*c['ATR'] and c['RSI'] < 50:
            signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']*1.5})
    return signals

# Strategy 5: BB Mean Reversion
def strat_bb(df):
    signals = []
    for i in range(50, len(df)-10):
        c, p = df.iloc[i], df.iloc[i-1]
        if p['close'] < p['BB_LOWER'] and c['close'] > c['BB_LOWER'] and c['RSI'] < 40:
            signals.append({'idx': i, 'dir': 1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
        elif p['close'] > p['BB_UPPER'] and c['close'] < c['BB_UPPER'] and c['RSI'] > 60:
            signals.append({'idx': i, 'dir': -1, 'entry': df.iloc[i+1]['open'], 'risk': c['ATR']})
    return signals

strategies = [
    ('EMA_Cross', strat_ema_cross),
    ('RSI_Bounce', strat_rsi),
    ('EMA_Pullback', strat_pullback),
    ('Breakout', strat_breakout),
    ('BB_Reversion', strat_bb)
]

symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'GOLD', 'BTCUSD', 'US500']
results = []

print("="*60)
print("MULTI-STRATEGY BACKTEST")
print("="*60)

for sym in symbols:
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 2000)
    if rates is None or len(rates) < 500:
        continue
    df = calc_indicators(pd.DataFrame(rates))
    
    for name, func in strategies:
        r = backtest_strategy(df, func, name, sym)
        if r:
            results.append(r)

# Sort by expectancy
results.sort(key=lambda x: x['expectancy'], reverse=True)

print("\nTOP 10 WINNING COMBINATIONS:")
print("-"*60)
print(f"{'Symbol':<10} {'Strategy':<15} {'Signals':<8} {'Win%':<8} {'Expect':<8} {'TotalR':<8}")
print("-"*60)

for r in results[:10]:
    print(f"{r['symbol']:<10} {r['strategy']:<15} {r['signals']:<8} {r['win_rate']:<8.1f} {r['expectancy']:<8.2f} {r['total_r']:<8.1f}")

print("\n" + "="*60)
profitable = [r for r in results if r['expectancy'] > 0]
print(f"Profitable: {len(profitable)}/{len(results)}")

if profitable:
    best = profitable[0]
    print(f"\nBEST: {best['symbol']} + {best['strategy']}")
    print(f"  Win Rate: {best['win_rate']:.1f}%")
    print(f"  Expectancy: {best['expectancy']:.2f}R per trade")
    print(f"  Total Signals: {best['signals']}")
    print(f"  Total R: {best['total_r']:.1f}")
    
    # Group by strategy
    print("\nBY STRATEGY (avg expectancy):")
    by_strat = {}
    for r in results:
        if r['strategy'] not in by_strat:
            by_strat[r['strategy']] = []
        by_strat[r['strategy']].append(r['expectancy'])
    
    for name, exps in sorted(by_strat.items(), key=lambda x: np.mean(x[1]), reverse=True):
        avg = np.mean(exps)
        print(f"  {name}: {avg:.2f}R avg")

mt5.shutdown()
