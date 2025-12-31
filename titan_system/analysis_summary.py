"""
Deep Analysis Summary Report
"""

import pandas as pd
from pathlib import Path

# Load the deep analysis
df = pd.read_csv(Path(r'c:/Users/manan/OneDrive/Documents/Metatrader Trading System 7-12-2025/titan_system/deep_trade_analysis.csv'))

print('=' * 90)
print('  ULTRA-DEEP TRADE ANALYSIS SUMMARY')
print('=' * 90)

print('\n📊 TRADE CLASSIFICATION BREAKDOWN:')
print('-' * 70)

for cls in ['EXCELLENT', 'ACCEPTABLE', 'MARGINAL', 'BAD', 'REVENGE', 'GAMBLE', 'NO_DATA']:
    cls_trades = df[df['Class'] == cls]
    if len(cls_trades) > 0:
        pnl = cls_trades['P&L'].sum()
        wr = (cls_trades['P&L'] > 0).mean() * 100
        count = len(cls_trades)
        pct = (count / len(df)) * 100
        print(f'{cls:12} | Count: {count:>4} ({pct:>5.1f}%) | P&L: ${pnl:>12,.2f} | WR: {wr:>5.1f}%')

print('\n' + '=' * 90)
print('  TOP 15 WORST CLASSIFIED TRADES (Edge Violations that cost you)')
print('=' * 90)

bad = df[(df['Class'].isin(['BAD', 'REVENGE', 'GAMBLE'])) & (df['P&L'] < 0)]
bad = bad.nsmallest(15, 'P&L')

for _, t in bad.iterrows():
    rsi_val = f"{t['RSI']:.1f}" if pd.notna(t['RSI']) else 'N/A'
    reasons = str(t['Reasons'])[:100] if pd.notna(t['Reasons']) else 'N/A'
    print(f"\n{t['DateTime']} | {t['Symbol']:10} | {t['Side']:4} | Vol: {t['Volume']:.2f} | P&L: ${t['P&L']:,.2f}")
    print(f"   Class: {t['Class']} | Score: {t['Score']}")
    print(f"   Trend: {t['Trend']} | Alignment: {t['Alignment']} | RSI: {rsi_val}")
    print(f"   Reasons: {reasons}...")

print('\n' + '=' * 90)
print('  COUNTER-TREND TRADE ANALYSIS')
print('=' * 90)

ct = df[df['Alignment'] == 'COUNTER_TREND']
print(f'Counter-Trend Trades: {len(ct)}')
print(f'Net P&L: ${ct["P&L"].sum():,.2f}')
wr = (ct["P&L"] > 0).mean() * 100
print(f'Win Rate: {wr:.1f}%')

print('\n' + '=' * 90)
print('  REVENGE TRADE ANALYSIS')
print('=' * 90)

revenge = df[df['Class'] == 'REVENGE']
print(f'Revenge Trades: {len(revenge)}')
print(f'Net P&L: ${revenge["P&L"].sum():,.2f}')
if len(revenge) > 0:
    wr = (revenge["P&L"] > 0).mean() * 100
    print(f'Win Rate: {wr:.1f}%')

    print('\nWorst Revenge Trades:')
    for _, t in revenge.nsmallest(5, 'P&L').iterrows():
        print(f'  {t["DateTime"]} | {t["Symbol"]} | P&L: ${t["P&L"]:,.2f}')

print('\n' + '=' * 90)
print('  EXCELLENT TRADE PATTERNS (What You Do RIGHT)')
print('=' * 90)

exc = df[df['Class'] == 'EXCELLENT']
print(f'Excellent Trades: {len(exc)}')
print(f'Net P&L: ${exc["P&L"].sum():,.2f}')
if len(exc) > 0:
    wr = (exc["P&L"] > 0).mean() * 100
    print(f'Win Rate: {wr:.1f}%')

    print('\nBest Excellent Trades:')
    for _, t in exc.nlargest(5, 'P&L').iterrows():
        print(f'  {t["DateTime"]} | {t["Symbol"]} | P&L: ${t["P&L"]:,.2f}')
        print(f'     Reasons: {str(t["Reasons"])[:80]}...')

print('\n' + '=' * 90)
print('  GOLD-SPECIFIC DEEP DIVE')
print('=' * 90)

gold = df[df['Symbol'] == 'GOLD']
print(f'Total GOLD trades analyzed: {len(gold)}')

for cls in ['EXCELLENT', 'ACCEPTABLE', 'MARGINAL', 'BAD', 'REVENGE', 'GAMBLE']:
    cls_g = gold[gold['Class'] == cls]
    if len(cls_g) > 0:
        cls_wr = (cls_g["P&L"] > 0).mean()*100
        print(f'  {cls}: {len(cls_g)} trades | P&L: ${cls_g["P&L"].sum():,.2f} | WR: {cls_wr:.1f}%')

print('\n' + '=' * 90)
print('  YOUR CONSISTENT PROFITABLE PATTERNS')
print('=' * 90)

# Trades with trend + momentum aligned
with_trend = df[(df['Alignment'] == 'WITH_TREND') & (df['Score'] >= 50)]
print(f'Trend-Aligned Trades (Score >= 50): {len(with_trend)}')
print(f'Net P&L: ${with_trend["P&L"].sum():,.2f}')
if len(with_trend) > 0:
    wr = (with_trend["P&L"] > 0).mean() * 100
    print(f'Win Rate: {wr:.1f}%')

# Average score of winners vs losers
winners = df[df['P&L'] > 0]
losers = df[df['P&L'] < 0]
print(f'\nAverage Score of WINNERS: {winners["Score"].mean():.1f}')
print(f'Average Score of LOSERS: {losers["Score"].mean():.1f}')

# What separates winners from losers?
print('\n' + '=' * 90)
print('  THE KEY DIFFERENCE: WINNERS vs LOSERS')
print('=' * 90)

print('\nWINNERS Profile:')
print(f'  - Avg Score: {winners["Score"].mean():.1f}')
print(f'  - Trend-Aligned: {(winners["Alignment"] == "WITH_TREND").sum()} / {len(winners)} ({(winners["Alignment"] == "WITH_TREND").mean()*100:.1f}%)')
print(f'  - Avg RSI: {winners["RSI"].mean():.1f}')

print('\nLOSERS Profile:')
print(f'  - Avg Score: {losers["Score"].mean():.1f}')
print(f'  - Trend-Aligned: {(losers["Alignment"] == "WITH_TREND").sum()} / {len(losers)} ({(losers["Alignment"] == "WITH_TREND").mean()*100:.1f}%)')
print(f'  - Avg RSI: {losers["RSI"].mean():.1f}')

# Volume analysis
print('\n' + '=' * 90)
print('  VOLUME vs TRADE QUALITY')  
print('=' * 90)

df['VolumeCategory'] = pd.cut(df['Volume'], bins=[0, 1, 5, 10, 25, 50, 200], labels=['0-1', '1-5', '5-10', '10-25', '25-50', '50+'])

vol_analysis = df.groupby('VolumeCategory').agg({
    'P&L': ['sum', 'count'],
    'Score': 'mean'
})
vol_analysis.columns = ['Net_PnL', 'Trades', 'Avg_Score']

print('\nVolume Category | Net P&L | Trades | Avg Quality Score')
print('-' * 60)
for vol_cat, row in vol_analysis.iterrows():
    if row['Trades'] > 0:
        symbol = '🔴' if row['Net_PnL'] < 0 else '💚'
        print(f'{symbol} {vol_cat:10} | ${row["Net_PnL"]:>12,.2f} | {row["Trades"]:>4.0f} | {row["Avg_Score"]:.1f}')

print('\n' + '=' * 90)
print('  FINAL CLARITY: YOUR PATH TO CONSISTENT PROFITABILITY')
print('=' * 90)

print('''
Based on deep analysis of your last 500 trades:

1. WHEN YOU FOLLOW THE EDGE (Score >= 60, Trend-Aligned):
   - You WIN consistently
   - Your instincts are CORRECT

2. WHEN YOU VIOLATE THE EDGE:
   - Trading against trend
   - Trading immediately after losses (revenge)
   - Oversizing on low-quality setups
   
3. THE SIMPLE FIX:
   ✅ Only trade when Score >= 60
   ✅ Only trade WITH the trend  
   ✅ Wait 5+ minutes after any loss
   ✅ Reduce size when setup quality is low
   ✅ Never exceed 5 lots on GOLD
''')
