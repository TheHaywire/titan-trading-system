"""
Institutional Performance Audit & Blacklist Automator
Analyzes historical trades to identify 'Account Killers' 
and automatically updates the trading universe filters.
"""

import sqlite3
import pandas as pd
import logging
import json
import os

logger = logging.getLogger("Titan.Audit")

class PerformanceOptimizer:
    def __init__(self, db_path="data/trading_system.db", blacklist_path="config/blacklist.json"):
        self.db_path = db_path
        self.blacklist_path = blacklist_path
        os.makedirs(os.path.dirname(blacklist_path), exist_ok=True)

    def run_audit(self, threshold_expectancy=-50.0, min_trades=3):
        """
        threshold_expectancy: Minimum average profit per trade allowed.
        min_trades: Minimum sample size before blacklisting.
        """
        logger.info("🕵️ Starting Performance Forensic Audit...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query("SELECT symbol, profit FROM trades", conn)
            conn.close()
        except Exception as e:
            logger.error(f"Failed to read trade history: {e}")
            return []

        if df.empty:
            logger.info("ℹ️ No trade history available for audit.")
            return []

        # 1. Group by Symbol and Calculate Metrics
        perf = df.groupby('symbol').agg({
            'profit': ['count', 'mean', 'sum']
        })
        perf.columns = ['trade_count', 'expectancy', 'total_pnl']
        
        # 2. Identify Underperformers
        account_killers = perf[
            (perf['trade_count'] >= min_trades) & 
            (perf['expectancy'] < threshold_expectancy)
        ]
        
        blacklist = account_killers.index.tolist()
        
        if blacklist:
            logger.warning(f"🚨 IDENTIFIED ACCOUNT KILLERS: {blacklist}")
            self._update_blacklist(blacklist)
            
        # 3. Detailed Audit Report
        print("\n📈 [PERFORMANCE AUDIT REPORT]")
        print(perf.sort_values('expectancy', ascending=False).to_string())
        
        return blacklist

    def _update_blacklist(self, new_symbols):
        """Persists the blacklist to config/blacklist.json"""
        current_blacklist = []
        if os.path.exists(self.blacklist_path):
            with open(self.blacklist_path, 'r') as f:
                try:
                    current_blacklist = json.load(f)
                except: pass
                
        # Merge and Unique
        updated_blacklist = list(set(current_blacklist + new_symbols))
        
        with open(self.blacklist_path, 'w') as f:
            json.dump(updated_blacklist, f, indent=4)
            
        logger.info(f"💾 Blacklist updated. {len(updated_blacklist)} total symbols paused.")

if __name__ == "__main__":
    optimizer = PerformanceOptimizer()
    optimizer.run_audit()
