"""
Institutional Performance Tracker
Logs and analyzes the win-rate of institutional setups.
Storage: data/performance.db (SQLite)
"""

import os
import sqlite3
import json
import argparse
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/performance.db")

class PerformanceTracker:
    def __init__(self):
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database schema for setups"""
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Create setups table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS setups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                tf TEXT NOT NULL,
                signal TEXT NOT NULL,
                entry_price REAL NOT NULL,
                sl REAL,
                tp REAL,
                score INTEGER NOT NULL,
                patterns TEXT, -- JSON list of patterns
                status TEXT DEFAULT 'PENDING', -- PENDING, WIN, LOSS, CLOSED
                result_pips REAL,
                exit_price REAL,
                exit_time TEXT
            )
        ''')
        
        conn.commit()
        conn.close()

    def log_setup(self, symbol, tf, signal, price, score, patterns=None, sl=None, tp=None):
        """Log a new institutional setup"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        patterns_json = json.dumps(patterns if patterns else [])
        now = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO setups (timestamp, symbol, tf, signal, entry_price, sl, tp, score, patterns)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (now, symbol.upper(), tf, signal.upper(), price, sl, tp, score, patterns_json))
        
        conn.commit()
        setup_id = cursor.lastrowid
        conn.close()
        
        print(f"✅ Setup Logged [ID: {setup_id}]: {symbol} {signal} @ {price} (Score: {score})")
        return setup_id

    def list_setups(self, limit=10):
        """List recent setups"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, timestamp, symbol, signal, score, status FROM setups ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        
        print("\n📊 RECENT INSTITUTIONAL SETUPS")
        print("-" * 60)
        print(f"{'ID':<5} {'Timestamp':<20} {'Symbol':<10} {'Signal':<8} {'Score':<5} {'Status':<10}")
        print("-" * 60)
        
        for row in rows:
            ts = datetime.fromisoformat(row[1]).strftime("%Y-%m-%d %H:%M")
            print(f"{row[0]:<5} {ts:<20} {row[2]:<10} {row[3]:<8} {row[4]:<5} {row[5]:<10}")
        print("-" * 60 + "\n")
        conn.close()

    def update_outcome(self, setup_id, status, exit_price=None, pips=None):
        """Manually or automatically update setup outcome"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE setups 
            SET status = ?, exit_price = ?, result_pips = ?, exit_time = ?
            WHERE id = ?
        ''', (status.upper(), exit_price, pips, now, setup_id))
        
        conn.commit()
        conn.close()
        print(f"✅ Setup {setup_id} updated to {status}")

    def get_stats(self):
        """Calculate and display win-rate analytics"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Overall
        cursor.execute("SELECT COUNT(*), SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END) FROM setups WHERE status IN ('WIN', 'LOSS')")
        total, wins = cursor.fetchone()
        
        if not total:
            print("No completed setups for analysis yet.")
            conn.close()
            return

        win_rate = (wins / total) * 100
        print(f"\n🏆 PERFORMANCE INTELLIGENCE")
        print("-" * 40)
        print(f"Total Completed: {total}")
        print(f"Total Wins:      {wins}")
        print(f"Win Rate:        {win_rate:.1f}%")
        
        # Stats by Score
        print("\n📈 Win Rate by Institutional Score:")
        cursor.execute('''
            SELECT score, COUNT(*), SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END)
            FROM setups 
            WHERE status IN ('WIN', 'LOSS')
            GROUP BY score
            ORDER BY score DESC
        ''')
        for sc, ct, wn in cursor.fetchall():
            wr = (wn / ct) * 100
            print(f"  Score {sc}/10: {wr:.1f}% ({wn}/{ct})")
            
        print("-" * 40 + "\n")
        conn.close()

def main():
    tracker = PerformanceTracker()
    
    parser = argparse.ArgumentParser(description="Titan Performance Tracker")
    subparsers = parser.add_subparsers(dest="command")
    
    # List
    parser_list = subparsers.add_parser("list")
    parser_list.add_argument("--limit", type=int, default=10)
    
    # Stats
    subparsers.add_parser("stats")
    
    # Log (Manual entry)
    parser_log = subparsers.add_parser("log")
    parser_log.add_argument("symbol")
    parser_log.add_argument("tf")
    parser_log.add_argument("signal", choices=["BUY", "SELL"])
    parser_log.add_argument("price", type=float)
    parser_log.add_argument("score", type=int)
    
    # Update
    parser_upd = subparsers.add_parser("update")
    parser_upd.add_argument("id", type=int)
    parser_upd.add_argument("status", choices=["WIN", "LOSS", "CLOSED"])
    parser_upd.add_argument("--pips", type=float)
    
    args = parser.parse_args()
    
    if args.command == "list":
        tracker.list_setups(args.limit)
    elif args.command == "stats":
        tracker.get_stats()
    elif args.command == "log":
        tracker.log_setup(args.symbol, args.tf, args.signal, args.price, args.score)
    elif args.command == "update":
        tracker.update_outcome(args.id, args.status, pips=args.pips)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
