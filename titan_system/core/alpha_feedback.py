"""
Alpha Feedback & Learning Module
================================
Tracks AI decisions and trade outcomes to enable 
automated self-learning and strategy refinement.
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

DB_PATH = "data/alpha_feedback.db"

class AlphaFeedback:
    """Tracks AI decisions and outcomes for institutional auditing."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the feedback database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Table for AI Decisions (Both YES and NO)
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                decision TEXT NOT NULL, -- 'YES' or 'NO'
                model TEXT NOT NULL,
                regime TEXT,
                confidence REAL,
                reasoning TEXT,
                draft_entry REAL,
                draft_sl REAL,
                draft_tp REAL,
                alpha_score REAL,
                market_context TEXT, -- JSON blob of indicators
                outcome_checked INTEGER DEFAULT 0,
                outcome TEXT -- 'WIN', 'LOSS', 'INVALID'
            )
        """)
        
        conn.commit()
        conn.close()
        
    def log_decision(self, data: Dict):
        """Log a new AI decision."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            INSERT INTO ai_decisions 
            (timestamp, symbol, decision, model, regime, confidence, 
             reasoning, draft_entry, draft_sl, draft_tp, alpha_score, market_context)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            data.get('symbol'),
            data.get('decision'),
            data.get('model'),
            data.get('regime'),
            data.get('confidence'),
            data.get('reasoning'),
            data.get('entry'),
            data.get('sl'),
            data.get('tp'),
            data.get('alpha_score'),
            json.dumps(data.get('market_data', {}))
        ))
        
        conn.commit()
        conn.close()
        
    def get_pending_outcomes(self) -> List[Dict]:
        """Get decisions that haven't had their outcome checked yet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM ai_decisions WHERE outcome_checked = 0")
        rows = [dict(row) for row in c.fetchall()]
        
        conn.close()
        return rows
        
    def update_outcome(self, decision_id: int, outcome: str):
        """Update the outcome of a decision."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        c.execute("""
            UPDATE ai_decisions 
            SET outcome = ?, outcome_checked = 1 
            WHERE id = ?
        """, (outcome, decision_id))
        
        conn.commit()
        conn.close()

    def get_performance_stats(self, days: int = 7) -> Dict:
        """Get summary stats for the AI's performance."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        c.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN outcome = 'LOSS' THEN 1 ELSE 0 END) as losses,
                AVG(confidence) as avg_conf
            FROM ai_decisions 
            WHERE timestamp > ? AND outcome IS NOT NULL
        """, (since,))
        
        row = c.fetchone()
        conn.close()
        
        if row and row[0] > 0:
            total, wins, losses, avg_conf = row
            return {
                "total_trades": total,
                "win_rate": round(wins / total * 100, 2) if total > 0 else 0,
                "wins": wins,
                "losses": losses,
                "avg_confidence": round(avg_conf, 2)
            }
        return {"error": "No data found"}

if __name__ == "__main__":
    # Test logging
    feedback = AlphaFeedback()
    feedback.log_decision({
        "symbol": "GOLD",
        "decision": "YES",
        "model": "gemini-2.0-flash",
        "regime": "TRENDING_BEARISH",
        "confidence": 0.85,
        "reasoning": "Strong bearish trend with oversold 1H RSI",
        "entry": 2000.0,
        "sl": 2010.0,
        "tp": 1980.0,
        "alpha_score": 38.5
    })
    print("Logged test decision.")
    print(f"Stats: {feedback.get_performance_stats()}")
