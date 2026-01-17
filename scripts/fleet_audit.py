import sqlite3
import json
from collections import Counter

def audit_alpha_fleet():
    conn = sqlite3.connect('data/strategy_factory.db')
    c = conn.cursor()
    
    print("=" * 60)
    print("TITAN OS :: ALPHA FLEET AUDIT")
    print("=" * 60)
    
    # 1. Overall Status Count
    c.execute('SELECT status, COUNT(*) FROM strategies GROUP BY status')
    status_counts = dict(c.fetchall())
    print("\n[📊] STATUS SUMMARY:")
    for status, count in status_counts.items():
        print(f"  - {status.upper():12}: {count}")
        
    # 2. Symbol Distribution (All)
    c.execute('SELECT genome FROM strategies')
    symbols = [json.loads(r[0]).get('symbols', ['UNKNOWN'])[0] for r in c.fetchall()]
    symbol_counts = Counter(symbols)
    print("\n[🌎] SYMBOL DISTRIBUTION (ALL):")
    for sym, count in symbol_counts.most_common(10):
        print(f"  - {sym:8}: {count}")
        
    # 3. Paper Trading Fleet Details
    c.execute('SELECT id, bt_sharpe, genome FROM strategies WHERE status = "paper"')
    paper_rows = c.fetchall()
    print("\n[🛰️] PAPER FLEET DETAILS:")
    if not paper_rows:
        print("  (Empty)")
    for r in paper_rows:
        g = json.loads(r[2])
        print(f"  - {r[0][:8]} | {g.get('symbols')[0]:8} | SR: {r[1]:.2f} | {g.get('type')}")
        
    # 4. Top Validated Candidates (Pending Deployment)
    c.execute('SELECT id, bt_sharpe, genome FROM strategies WHERE status = "validated" ORDER BY bt_sharpe DESC LIMIT 5')
    val_rows = c.fetchall()
    print("\n[🏆] TOP VALIDATED (PENDING):")
    for r in val_rows:
        g = json.loads(r[2])
        print(f"  - {r[0][:8]} | {g.get('symbols')[0]:8} | SR: {r[1]:.2f} | {g.get('type')}")
        
    conn.close()

if __name__ == "__main__":
    audit_alpha_fleet()
