"""Quick Trade Audit - Simple ASCII output"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

mt5.initialize()
positions = mt5.positions_get()
acc = mt5.account_info()

lines = []
lines.append('='*60)
lines.append('PROFESSIONAL TRADE AUDIT')
lines.append('='*60)
lines.append('Time: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
lines.append('Account Equity: $' + f'{acc.equity:,.2f}')
lines.append('Open Positions: ' + str(len(positions) if positions else 0))
lines.append('')

current_symbols = []
total_pnl = 0

if positions:
    lines.append('CURRENT POSITIONS:')
    lines.append('-'*60)
    for pos in positions:
        direction = 'BUY' if pos.type == 0 else 'SELL'
        total_pnl += pos.profit
        current_symbols.append(pos.symbol)
        status = 'PROFIT' if pos.profit > 0 else 'LOSS'
        lines.append('[' + status + '] ' + pos.symbol + ' ' + direction + ' ' + str(pos.volume) + ' lots')
        lines.append('   Entry: ' + str(round(pos.price_open, 2)) + ' | Now: ' + str(round(pos.price_current, 2)) + ' | PnL: $' + str(round(pos.profit, 2)))
    lines.append('')
    lines.append('Total Floating P/L: $' + str(round(total_pnl, 2)))
else:
    lines.append('No open positions')

lines.append('')
lines.append('MARKET SCAN (Best Opportunities):')
lines.append('-'*60)

best_setups = []
for sym in ['GOLD', 'BTCUSD', 'US100', 'EURUSD', 'GER40', 'US30', 'GBPUSD', 'XAUUSD']:
    try:
        if not mt5.symbol_select(sym, True): continue
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M5, 0, 100)
        if rates is None or len(rates) < 50: continue
        df = pd.DataFrame(rates)
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        df['MOM'] = df['close'].pct_change(5) * 100
        curr = df.iloc[-1]
        
        score = 50
        signal = 'HOLD'
        reasons = []
        
        if curr['RSI'] < 30: 
            score += 25; signal = 'BUY'; reasons.append('RSI Oversold')
        elif curr['RSI'] > 70: 
            score += 25; signal = 'SELL'; reasons.append('RSI Overbought')
        elif curr['RSI'] < 40:
            score += 10; signal = 'BUY'; reasons.append('RSI Low')
        elif curr['RSI'] > 60:
            score += 10; signal = 'SELL'; reasons.append('RSI High')
            
        if curr['EMA9'] > curr['EMA21']: 
            if signal != 'SELL': score += 15; signal = 'BUY'
            reasons.append('Bullish EMA')
        elif curr['EMA9'] < curr['EMA21']: 
            if signal != 'BUY': score += 15; signal = 'SELL'
            reasons.append('Bearish EMA')
            
        if abs(curr['MOM']) > 0.3: 
            score += 10
            reasons.append('Strong Momentum')
        
        quality = 'HOT!' if score >= 75 else 'OK' if score >= 60 else '--'
        in_trade = '*IN*' if sym in current_symbols else '    '
        rsi_val = round(curr['RSI'], 0)
        mom_val = round(curr['MOM'], 2)
        
        line = '[' + quality + '] ' + in_trade + ' ' + sym.ljust(8) + ': ' + signal.ljust(5) + ' Score=' + str(score) + ' RSI=' + str(int(rsi_val)) + ' Mom=' + str(mom_val) + '%'
        lines.append(line)
        
        if score >= 70:
            best_setups.append((sym, signal, score, reasons))
    except Exception as e:
        pass

lines.append('')
lines.append('='*60)
lines.append('VERDICT')
lines.append('='*60)

# Check position quality
good_trades = 0
if positions:
    lines.append('')
    lines.append('Position Quality Check:')
    for pos in positions:
        pos_dir = 'BUY' if pos.type == 0 else 'SELL'
        found = False
        for sym, sig, sc, r in best_setups:
            if sym == pos.symbol:
                if pos_dir == sig:
                    lines.append('   [GOOD] ' + pos.symbol + ' ' + pos_dir + ' aligns with signal (Score ' + str(sc) + ')')
                    good_trades += 1
                else:
                    lines.append('   [BAD!] ' + pos.symbol + ' ' + pos_dir + ' is AGAINST signal (' + sig + ')')
                found = True
                break
        if not found:
            lines.append('   [HOLD] ' + pos.symbol + ' - No strong signal')

# Missed opportunities
if best_setups:
    missed = [s for s in best_setups if s[0] not in current_symbols]
    if missed:
        lines.append('')
        lines.append('Opportunities NOT in (' + str(len(missed)) + '):')
        for sym, sig, sc, r in sorted(missed, key=lambda x: -x[2]):
            lines.append('   --> ' + sym + ' ' + sig + ' (Score ' + str(sc) + ')')

# Final verdict
if positions:
    total = len(positions)
    pct = int((good_trades / total) * 100) if total > 0 else 0
    lines.append('')
    if pct >= 70:
        lines.append('*** VERDICT: GOOD - ' + str(pct) + '% of trades in optimal setups! ***')
    elif pct >= 40:
        lines.append('*** VERDICT: MODERATE - ' + str(pct) + '% alignment. Review weak positions. ***')
    else:
        lines.append('*** VERDICT: NEEDS REVIEW - Only ' + str(pct) + '% aligned! ***')
        lines.append('    Consider closing misaligned trades.')

# Print all
for line in lines:
    print(line)

mt5.shutdown()
