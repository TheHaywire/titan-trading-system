import sqlite3
import json

db_path = "titan_system/titan.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("--- TRADES TABLE ---")
    cursor.execute("SELECT DISTINCT symbol FROM trades")
    trade_symbols = cursor.fetchall()
    if trade_symbols:
        for s in trade_symbols:
            print(f"- {s[0]}")
    else:
        print("(No trades recorded yet)")

    print("\n--- LOGS TABLE (Last 50) ---")
    cursor.execute("SELECT message, metadata FROM logs ORDER BY id DESC LIMIT 50")
    logs = cursor.fetchall()
    
    found_symbols = set()
    for msg, meta in logs:
        # Check metadata JSON
        if meta:
            try:
                data = json.loads(meta)
                if isinstance(data, dict) and 'symbol' in data:
                    found_symbols.add(data['symbol'])
            except:
                pass
        
        # Check message text for typical patterns
        # e.g. "Signal for EURUSD", "Executing BUY on EURUSD"
        words = msg.split()
        for w in words:
            if w.isupper() and len(w) == 6 and "USD" in w or "EUR" in w or "JPY" in w: # Heuristic
                found_symbols.add(w.strip(":"))

    if found_symbols:
        print(f"Symbols found in recent logs: {sorted(list(found_symbols))}")
    else:
        print("(No symbols identified in recent logs)")

    conn.close()

except Exception as e:
    print(f"Error: {e}")
