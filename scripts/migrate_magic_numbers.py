import os
import re
import json
import sqlite3
from pathlib import Path

def migrate_magic_numbers():
    db_path = "data/strategy_factory.db"
    bot_dir = Path("titan_system/strategies/autogen")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Get all paper/live strategies
    cur.execute("SELECT id, genome FROM strategies WHERE status IN ('paper', 'live')")
    rows = cur.fetchall()
    
    print(f"Checking {len(rows)} active strategies...")
    
    for s_id, genome_json in rows:
        genome = json.loads(genome_json)
        # Match filename
        filename = f"autogen_{s_id[:8]}_{genome['name'].replace(' ', '_')}.py"
        filepath = bot_dir / filename
        
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                # Find MAGIC_NUMBER = 12345
                match = re.search(r"MAGIC_NUMBER = (\d+)", content)
                if match:
                    magic = int(match.group(1))
                    cur.execute("UPDATE strategies SET magic_number = ? WHERE id = ?", (magic, s_id))
                    print(f"✅ Updated {genome['name']} ({s_id[:8]}) with Magic: {magic}")
                else:
                    print(f"⚠️ Could not find Magic Number in {filename}")
        else:
            print(f"❌ File not found: {filename}")
            
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_magic_numbers()
