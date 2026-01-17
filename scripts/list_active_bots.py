import sqlite3, json
conn = sqlite3.connect('data/strategy_factory.db')
cur = conn.cursor()
cur.execute('SELECT id, genome, status FROM strategies WHERE status IN ("paper", "live")')
rows = cur.fetchall()
print("-" * 80)
print(f"{'ID':<15} | {'NAME':<40} | {'STATUS':<10}")
print("-" * 80)
for r in rows:
    genome = json.loads(r[1])
    print(f"{r[0][:15]:<15} | {genome.get('name', 'N/A'):<40} | {r[2]:<10}")
conn.close()
