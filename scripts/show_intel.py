"""Quick query to show current market intelligence data"""
import sqlite3

conn = sqlite3.connect('data/market_intelligence.db')
c = conn.cursor()

# Count samples
c.execute('SELECT COUNT(*) FROM spread_samples')
print(f'Total samples in DB: {c.fetchone()[0]}')

# Top 20 tightest spreads
c.execute('SELECT symbol, spread, hour, session FROM spread_samples ORDER BY spread LIMIT 25')
print('\nTop 25 Tightest Spreads Right Now:')
print(f'{"Symbol":<20} {"Spread":<10} {"Hour":<6} {"Session"}')
print('-'*50)
for r in c.fetchall():
    print(f'{r[0]:<20} {r[1]:<10} {r[2]:<6} {r[3]}')

# Widest spreads (illiquid)
c.execute('SELECT symbol, spread, hour, session FROM spread_samples ORDER BY spread DESC LIMIT 10')
print('\n\nTop 10 WIDEST Spreads (Illiquid):')
print(f'{"Symbol":<20} {"Spread":<10} {"Hour":<6} {"Session"}')
print('-'*50)
for r in c.fetchall():
    print(f'{r[0]:<20} {r[1]:<10} {r[2]:<6} {r[3]}')

conn.close()
