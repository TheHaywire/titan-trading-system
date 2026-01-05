"""
PROFESSIONAL TRADE AUDIT
Are we in the best setups?
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

mt5.initialize()

print('=' * 60)
print('PROFESSIONAL TRADE AUDIT - Are We In The Best Setups?')
print('=' * 60)
print(f'Timestamp: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

# Get current positions
positions = mt5.positions_get()
print(f'\n[POSITIONS] CURRENT OPEN POSITIONS ({len(positions) if positions else 0})')
print('-' * 60)

current_symbols = []
total_pnl = 0
if positions:
    for pos in positions:
        profit = pos.profit
        total_pnl += profit
        status = '[PROFIT]' if profit > 0 else '[LOSS]'
        direction = 'BUY' if pos.type == 0 else 'SELL'
        pips = (pos.price_current - pos.price_open) if pos.type == 0 else (pos.price_open - pos.price_current)
        current_symbols.append(pos.symbol)
        
        print(f'{status} {pos.symbol}: {direction} {pos.volume} lots @ {pos.price_open:.2f}')
        print(f'   Current: {pos.price_current:.2f} | P/L: ${profit:+.2f}')
        print(f'   SL: {pos.sl:.2f} | TP: {pos.tp:.2f}')
        print()
else:
    print('No open positions')

# Analyze quality of current setups
print('\n[SCANNER] MARKET CONDITION ANALYSIS')
print('-' * 60)

symbols_to_scan = ['GOLD', 'BTCUSD', 'US100', 'EURUSD', 'GBPUSD', 'XAUUSD', 'GER40', 'US30', 'ETHUSD']
best_setups = []

for symbol in symbols_to_scan:
    try:
        if not mt5.symbol_select(symbol, True):
            continue
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
        if rates is None or len(rates) < 50:
            continue
        
        df = pd.DataFrame(rates)
        
        # Calculate indicators
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        df['MOM'] = df['close'].pct_change(5) * 100
        df['HIGH_20'] = df['high'].rolling(20).max()
        df['LOW_20'] = df['low'].rolling(20).min()
        df['RANGE_POS'] = (df['close'] - df['LOW_20']) / (df['HIGH_20'] - df['LOW_20'])
        
        curr = df.iloc[-1]
        
        # Score the setup
        score = 50  # Base score
        signal = 'NEUTRAL'
        reasons = []
        
        # RSI extremes
        if curr['RSI'] < 30:
            score += 20
            signal = 'BUY'
            reasons.append(f"RSI oversold ({curr['RSI']:.0f})")
        elif curr['RSI'] > 70:
            score += 20
            signal = 'SELL'
            reasons.append(f"RSI overbought ({curr['RSI']:.0f})")
        elif curr['RSI'] < 40:
            score += 10
            signal = 'BUY'
            reasons.append(f"RSI low ({curr['RSI']:.0f})")
        elif curr['RSI'] > 60:
            score += 10
            signal = 'SELL'
            reasons.append(f"RSI high ({curr['RSI']:.0f})")
        
        # EMA trend
        if curr['EMA9'] > curr['EMA21']:
            if signal in ['NEUTRAL', 'BUY']: 
                signal = 'BUY'
                score += 15
            reasons.append('Bullish EMA')
        elif curr['EMA9'] < curr['EMA21']:
            if signal in ['NEUTRAL', 'SELL']: 
                signal = 'SELL'
                score += 15
            reasons.append('Bearish EMA')
        
        # Strong momentum
        if abs(curr['MOM']) > 0.3:
            score += 10
            mom_dir = 'up' if curr['MOM'] > 0 else 'down'
            reasons.append(f"Strong {mom_dir} mom ({curr['MOM']:+.2f}%)")
        
        # Range extremes
        if curr['RANGE_POS'] < 0.2:
            if signal == 'BUY': score += 10
            reasons.append('At range low')
        elif curr['RANGE_POS'] > 0.8:
            if signal == 'SELL': score += 10
            reasons.append('At range high')
        
        in_trade = '[IN]' if symbol in current_symbols else '    '
        quality = '[HOT]' if score >= 80 else '[OK]' if score >= 65 else '[--]'
        print(f"{quality} {in_trade} {symbol:8s}: {signal:7s} | Score: {score:3d}/100 | RSI: {curr['RSI']:.0f} | Range: {curr['RANGE_POS']*100:.0f}%")
        if reasons and score >= 65:
            print(f"         Reasons: {', '.join(reasons)}")
        
        if score >= 70:
            best_setups.append((symbol, signal, score, reasons))
    except Exception as e:
        pass

print('\n' + '=' * 60)
print('VERDICT')
print('=' * 60)

# Check if current positions are in best setups
good_trades = 0
if positions:
    print('\n[QUALITY CHECK] Your Positions:')
    for pos in positions:
        setup_found = False
        for sym, sig, sc, r in best_setups:
            if sym == pos.symbol:
                pos_dir = 'BUY' if pos.type == 0 else 'SELL'
                if pos_dir == sig:
                    print(f'   [GOOD] {pos.symbol} {pos_dir} - ALIGNED with signal (Score: {sc})')
                    good_trades += 1
                else:
                    print(f'   [BAD!] {pos.symbol} {pos_dir} - AGAINST signal (Signal is {sig})')
                setup_found = True
                break
        if not setup_found:
            print(f'   [HOLD] {pos.symbol} - No strong signal either way')

if best_setups:
    not_in_yet = [s for s in best_setups if s[0] not in current_symbols]
    if not_in_yet:
        print(f'\n[OPPORTUNITIES] High-Score Setups You Are NOT In ({len(not_in_yet)}):')
        for sym, sig, sc, r in sorted(not_in_yet, key=lambda x: -x[2]):
            print(f'   --> {sym} {sig} (Score: {sc})')
else:
    print('\n[WAIT] No high-conviction setups right now. Patience is key.')

# Account status
acc = mt5.account_info()
print(f'\n[ACCOUNT]')
print(f'   Equity: ${acc.equity:,.2f}')
print(f'   Floating P/L: ${total_pnl:+,.2f}')
print(f'   Open Positions: {len(positions) if positions else 0}')

# Final verdict
if positions:
    total = len(positions)
    pct = (good_trades / total) * 100 if total > 0 else 0
    if pct >= 80:
        print(f'\n>>> VERDICT: EXCELLENT - {pct:.0f}% of trades in optimal setups!')
    elif pct >= 50:
        print(f'\n>>> VERDICT: MODERATE - {pct:.0f}% alignment. Consider reviewing weak positions.')
    else:
        print(f'\n>>> VERDICT: NEEDS REVIEW - Only {pct:.0f}% aligned with high-conviction signals.')
        print('    Consider: Closing misaligned trades OR waiting for setup to develop.')

mt5.shutdown()
