"""
DB SENTINEL
===========
Guardian of the Titan Database layer.
Handles integrity checks, vacuuming, and schema auditing.
"""

import sqlite3
import os
import json
from datetime import datetime

# Paths from project root
DB_PATHS = [
    "data/strategy_factory.db",
    "titan_system/titan.db"
]

def audit_databases():
    summary = {}
    
    for db_path in DB_PATHS:
        abs_path = os.path.abspath(db_path)
        if not os.path.exists(abs_path):
            summary[db_path] = {"status": "MISSING"}
            continue
            
        try:
            conn = sqlite3.connect(abs_path)
            cursor = conn.cursor()
            
            # 1. Integrity Check
            cursor.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchone()[0]
            
            # 2. Schema Audit (List Tables)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            
            # 3. Stats (Size)
            size_kb = os.path.getsize(abs_path) / 1024
            
            # 4. Cleanup (Vacuum)
            cursor.execute("VACUUM;")
            
            summary[db_path] = {
                "status": "HEALTHY" if integrity == "ok" else "CORRUPT",
                "integrity": integrity,
                "size_kb": round(size_kb, 2),
                "tables": tables,
                "timestamp": datetime.now().isoformat()
            }
            
            conn.close()
        except Exception as e:
            summary[db_path] = {"status": "ERROR", "error": str(e)}

    return summary

if __name__ == "__main__":
    report = audit_databases()
    print(json.dumps(report, indent=2))
