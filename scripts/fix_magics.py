import sqlite3
import json

def fix_magics():
    conn = sqlite3.connect('data/strategy_factory.db')
    cursor = conn.cursor()
    
    # Start magic number range for factory
    MAGIC_START = 999000
    
    # Get all paper trading strategies
    cursor.execute("SELECT id FROM strategies WHERE status IN ('paper', 'live')")
    rows = cursor.fetchall()
    
    print(f"Assigning unique magic numbers to {len(rows)} active strategies...")
    
    for i, (strategy_id,) in enumerate(rows):
        new_magic = MAGIC_START + i
        print(f"  {strategy_id[:8]} -> {new_magic}")
        
        # Check if another strategy already has this magic and set it to NULL first to avoid unique constraint issues
        cursor.execute("UPDATE strategies SET magic_number = NULL WHERE magic_number = ?", (new_magic,))
        
        # Update current strategy
        cursor.execute("UPDATE strategies SET magic_number = ? WHERE id = ?", (new_magic, strategy_id))
    
    conn.commit()
    conn.close()
    print("Done! Magics updated in database.")

if __name__ == "__main__":
    fix_magics()
