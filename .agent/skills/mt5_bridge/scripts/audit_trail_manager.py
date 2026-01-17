"""
AUDIT TRAIL MANAGER
===================
Institutional ledger for system actions.
Records every decision, execution attempt, and infrastructure event.
"""

import sqlite3
import json
import os
from datetime import datetime

AUDIT_DB = "data/audit_trail.db"

def init_audit_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(AUDIT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            component TEXT,
            action TEXT,
            status TEXT,
            details TEXT,
            magic INTEGER
        )
    """)
    conn.commit()
    conn.close()

def log_event(component, action, status, details=None, magic=0):
    try:
        if not os.path.exists(AUDIT_DB):
            init_audit_db()
            
        conn = sqlite3.connect(AUDIT_DB)
        cursor = conn.cursor()
        
        details_json = json.dumps(details) if details else None
        
        cursor.execute("""
            INSERT INTO system_logs (component, action, status, details, magic)
            VALUES (?, ?, ?, ?, ?)
        """, (component, action, status, details_json, magic))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"FAILED TO WRITE TO AUDIT TRAIL: {e}")

def get_recent_trail(limit=50):
    if not os.path.exists(AUDIT_DB):
        return []
    
    conn = sqlite3.connect(AUDIT_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    # Test logging
    log_event("AUDIT_DESK", "Audit System Started", "SUCCESS", {"version": "1.0"})
    print("Logged test event. Recent trail entries:")
    for row in get_recent_trail(5):
        print(row)
