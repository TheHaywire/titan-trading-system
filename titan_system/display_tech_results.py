"""
Display Technical Analysis Results
"""
import pandas as pd
from pathlib import Path

# Load the results
df = pd.read_csv(Path(r'c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025/titan_system/technical_analysis_results.csv'))

winners = df[df['IsWin'] == True]
losers = df[df['IsWin'] == False]

print('='*80)
print('  TECHNICAL IMPROVEMENT ANALYSIS RESULTS')
print('='*80)

print(f'\nTotal trades analyzed: {len(df)}')
print(f'Winners: {len(winners)} | Losers: {len(losers)}')

print('\n' + '='*80)
print('  RSI ANALYSIS')
print('='*80)

if 'rsi_at_entry' in df.columns:
    print(f'\nAverage RSI at Entry:')
    print(f'  WINNERS: {winners["rsi_at_entry"].mean():.1f}')
    print(f'  LOSERS:  {losers["rsi_at_entry"].mean():.1f}')
    
    print('\nWin rate by RSI range:')
    for rsi_min, rsi_max, label in [(0, 30, 'Oversold (0-30)'), (30, 50, 'Low (30-50)'), 
                                    (50, 70, 'High (50-70)'), (70, 100, 'Overbought (70+)')]:
        subset = df[(df['rsi_at_entry'] >= rsi_min) & (df['rsi_at_entry'] < rsi_max)]
        if len(subset) > 0:
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f'  {label}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

print('\n' + '='*80)
print('  MACD CONFIRMATION')
print('='*80)

if 'macd_issue' in df.columns:
    for macd_type in df['macd_issue'].dropna().unique():
        subset = df[df['macd_issue'] == macd_type]
        wr = (subset['PnL'] > 0).mean() * 100
        pnl = subset['PnL'].sum()
        print(f'  {macd_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

print('\n' + '='*80)
print('  STOCHASTIC')
print('='*80)

if 'stoch_issue' in df.columns:
    for stoch_type in df['stoch_issue'].dropna().unique():
        subset = df[df['stoch_issue'] == stoch_type]
        wr = (subset['PnL'] > 0).mean() * 100
        pnl = subset['PnL'].sum()
        print(f'  {stoch_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

print('\n' + '='*80)
print('  BOLLINGER BANDS')
print('='*80)

if 'bb_issue' in df.columns:
    for bb_type in df['bb_issue'].dropna().unique():
        subset = df[df['bb_issue'] == bb_type]
        wr = (subset['PnL'] > 0).mean() * 100
        pnl = subset['PnL'].sum()
        print(f'  {bb_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

print('\n' + '='*80)
print('  EMA ALIGNMENT')
print('='*80)

if 'ema_issue' in df.columns:
    for ema_type in df['ema_issue'].dropna().unique():
        subset = df[df['ema_issue'] == ema_type]
        wr = (subset['PnL'] > 0).mean() * 100
        pnl = subset['PnL'].sum()
        print(f'  {ema_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

print('\n' + '='*80)
print('  ENTRY TIMING (MFE/MAE)')
print('='*80)

if 'entry_timing' in df.columns:
    for timing in df['entry_timing'].dropna().unique():
        subset = df[df['entry_timing'] == timing]
        wr = (subset['PnL'] > 0).mean() * 100
        pnl = subset['PnL'].sum()
        print(f'  {timing}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}')

if 'mfe_atr' in df.columns and 'mae_atr' in df.columns:
    winners_clean = winners.dropna(subset=['mfe_atr', 'mae_atr'])
    losers_clean = losers.dropna(subset=['mfe_atr', 'mae_atr'])
    
    if len(winners_clean) > 0:
        print(f'\nMFE (how far trade went in your favor):')
        print(f'  WINNERS: {winners_clean["mfe_atr"].mean():.2f} ATR')
        print(f'  LOSERS:  {losers_clean["mfe_atr"].mean():.2f} ATR')
        
        print(f'\nMAE (how far trade went against you):')
        print(f'  WINNERS: {winners_clean["mae_atr"].mean():.2f} ATR')
        print(f'  LOSERS:  {losers_clean["mae_atr"].mean():.2f} ATR')

print('\n' + '='*80)
print('  SYMBOL-SPECIFIC TECHNICAL PATTERNS')
print('='*80)

for symbol in df['Symbol'].unique():
    sym = df[df['Symbol'] == symbol]
    if len(sym) > 5:
        print(f'\n{symbol}:')
        sym_winners = sym[sym['IsWin'] == True]
        sym_losers = sym[sym['IsWin'] == False]
        
        if len(sym_winners) > 0 and 'rsi_at_entry' in sym.columns:
            print(f'  Winner avg RSI: {sym_winners["rsi_at_entry"].mean():.1f}')
        if len(sym_losers) > 0 and 'rsi_at_entry' in sym.columns:
            print(f'  Loser avg RSI:  {sym_losers["rsi_at_entry"].mean():.1f}')
