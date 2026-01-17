"""
System Purge & Sync
===================
Cleaning the registry and filesystem of legacy/invalid data.
"""
import sys, os
sys.path.insert(0, '.')

import sqlite3
import shutil
from titan_system.factory import factory_config as cfg

def purge_db():
    print("🧹 Cleaning Strategy Registry...")
    db_path = cfg.STRATEGY_DB
    if not os.path.exists(db_path):
        print("   Database not found, skipping.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Identify valid symbols
    valid_symbols = cfg.SYMBOL_UNIVERSE
    placeholders = ','.join(['?'] * len(valid_symbols))
    
    # 2. Delete strategies with symbols NOT in universe
    # Note: genome is stored as JSON, so we need to be careful.
    # We'll just fetch all and check manually or use LIKE.
    
    cursor.execute("SELECT id, genome FROM strategies")
    all_strategies = cursor.fetchall()
    
    deleted_count = 0
    import json
    for s_id, genome_json in all_strategies:
        genome = json.loads(genome_json)
        # Check if any symbol in strategy is NOT in universe
        invalid = False
        for sym in genome.get('symbols', []):
            if sym not in valid_symbols:
                invalid = True
                break
        
        if invalid:
            cursor.execute("DELETE FROM strategies WHERE id = ?", (s_id,))
            cursor.execute("DELETE FROM performance_snapshots WHERE strategy_id = ?", (s_id,))
            cursor.execute("DELETE FROM strategy_trades WHERE strategy_id = ?", (s_id,))
            deleted_count += 1
            
    conn.commit()
    conn.close()
    print(f"   Deleted {deleted_count} invalid strategies from database.")

def purge_files():
    print("🧹 Cleaning Autogen Files...")
    autogen_dir = cfg.AUTOGEN_DIR
    if os.path.exists(autogen_dir):
        # Delete everything inside autogen
        for filename in os.listdir(autogen_dir):
            file_path = os.path.join(autogen_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    if filename != "__init__.py":
                        os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'   Failed to delete {file_path}. Reason: {e}')
    print("   Autogen folder cleaned.")

if __name__ == "__main__":
    purge_db()
    purge_files()
    print("✅ SYSTEM PURGE COMPLETE. Ready for fresh autonomous run.")
