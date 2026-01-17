"""
Market Intelligence Tracker
============================
Tracks real-time market data that isn't available historically:
- Spreads (varies by hour/session)
- Spread ratio (spread / ATR)
- Tick volume profiles
- Slippage estimates
- Session characteristics

Run this continuously to build a comprehensive market database.
"""
import MetaTrader5 as mt5
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import threading
import time

DB_PATH = "data/market_intelligence.db"


class MarketIntelligence:
    """Collects and stores real-time market intelligence."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize the SQLite database."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Spread samples table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS spread_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                spread INTEGER,
                bid REAL,
                ask REAL,
                tick_volume INTEGER,
                hour INTEGER,
                weekday INTEGER,
                session TEXT
            )
        """)
        
        # Daily summary table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                min_spread INTEGER,
                max_spread INTEGER,
                avg_spread REAL,
                spread_std REAL,
                avg_atr REAL,
                spread_ratio REAL,
                total_volume INTEGER,
                best_hour INTEGER,
                worst_hour INTEGER,
                samples INTEGER,
                UNIQUE(date, symbol)
            )
        """)
        
        # Symbol profiles (aggregated over time)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS symbol_profiles (
                symbol TEXT PRIMARY KEY,
                last_updated TEXT,
                avg_spread REAL,
                max_spread INTEGER,
                spread_variability REAL,
                avg_atr REAL,
                spread_ratio REAL,
                best_session TEXT,
                worst_session TEXT,
                adrenaline_score REAL,
                is_tradeable INTEGER,
                total_samples INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_session(self, hour: int) -> str:
        """Determine trading session based on hour (UTC)."""
        if 0 <= hour < 7:
            return "ASIAN"
        elif 7 <= hour < 12:
            return "LONDON"
        elif 12 <= hour < 17:
            return "OVERLAP"  # Best liquidity
        elif 17 <= hour < 21:
            return "NEW_YORK"
        else:
            return "AFTER_HOURS"
    
    def sample_all_symbols(self, symbols: List[str] = None) -> int:
        """
        Sample spread/tick data for all or specified symbols.
        Returns count of symbols sampled.
        """
        if not mt5.initialize():
            print("MT5 initialization failed")
            return 0
        
        if symbols is None:
            all_syms = mt5.symbols_get()
            symbols = [s.name for s in all_syms 
                      if mt5.symbol_info(s.name) and 
                      mt5.symbol_info(s.name).trade_mode == 4]
        
        now = datetime.utcnow()
        hour = now.hour
        weekday = now.weekday()
        session = self._get_session(hour)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        count = 0
        for sym in symbols:
            try:
                info = mt5.symbol_info(sym)
                tick = mt5.symbol_info_tick(sym)
                
                if info and tick:
                    cursor.execute("""
                        INSERT INTO spread_samples 
                        (timestamp, symbol, spread, bid, ask, tick_volume, hour, weekday, session)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        now.isoformat(),
                        sym,
                        info.spread,
                        tick.bid,
                        tick.ask,
                        tick.volume,
                        hour,
                        weekday,
                        session
                    ))
                    count += 1
            except Exception as e:
                pass  # Skip problematic symbols
        
        conn.commit()
        conn.close()
        return count
    
    def calculate_daily_summary(self, date: str = None):
        """Calculate daily summary for all symbols."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all symbols sampled today
        cursor.execute("""
            SELECT DISTINCT symbol FROM spread_samples
            WHERE timestamp LIKE ?
        """, (f"{date}%",))
        
        symbols = [row[0] for row in cursor.fetchall()]
        
        for sym in symbols:
            # Get spread stats
            cursor.execute("""
                SELECT 
                    MIN(spread), MAX(spread), AVG(spread),
                    COUNT(*),
                    (SELECT hour FROM spread_samples 
                     WHERE symbol = ? AND timestamp LIKE ?
                     GROUP BY hour ORDER BY AVG(spread) LIMIT 1),
                    (SELECT hour FROM spread_samples 
                     WHERE symbol = ? AND timestamp LIKE ?
                     GROUP BY hour ORDER BY AVG(spread) DESC LIMIT 1)
                FROM spread_samples
                WHERE symbol = ? AND timestamp LIKE ?
            """, (sym, f"{date}%", sym, f"{date}%", sym, f"{date}%"))
            
            row = cursor.fetchone()
            if row and row[3] > 0:
                min_spread, max_spread, avg_spread, samples, best_hour, worst_hour = row
                
                # Calculate ATR from MT5
                rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 24)
                if rates is not None and len(rates) > 0:
                    atr = sum(r['high'] - r['low'] for r in rates) / len(rates)
                    # Convert to points
                    info = mt5.symbol_info(sym)
                    if info and info.point > 0:
                        atr_points = atr / info.point
                        spread_ratio = (avg_spread / atr_points * 100) if atr_points > 0 else 100
                    else:
                        atr_points = 0
                        spread_ratio = 100
                else:
                    atr_points = 0
                    spread_ratio = 100
                
                # Upsert daily summary
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_summary
                    (date, symbol, min_spread, max_spread, avg_spread, avg_atr, 
                     spread_ratio, best_hour, worst_hour, samples)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date, sym, min_spread, max_spread, avg_spread,
                    atr_points, spread_ratio, best_hour, worst_hour, samples
                ))
        
        conn.commit()
        conn.close()
        print(f"Daily summary calculated for {len(symbols)} symbols")
    
    def update_symbol_profiles(self):
        """Update symbol profiles from all collected data."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all symbols with data
        cursor.execute("SELECT DISTINCT symbol FROM daily_summary")
        symbols = [row[0] for row in cursor.fetchall()]
        
        for sym in symbols:
            cursor.execute("""
                SELECT 
                    AVG(avg_spread), MAX(max_spread),
                    AVG(avg_atr), AVG(spread_ratio),
                    SUM(samples)
                FROM daily_summary WHERE symbol = ?
            """, (sym,))
            
            row = cursor.fetchone()
            if row:
                avg_spread, max_spread, avg_atr, spread_ratio, total_samples = row
                
                # Calculate adrenaline score
                adrenaline = (avg_atr / avg_spread) if avg_spread and avg_spread > 0 else 0
                
                # Determine if tradeable
                is_tradeable = 1 if spread_ratio and spread_ratio < 10 else 0
                
                cursor.execute("""
                    INSERT OR REPLACE INTO symbol_profiles
                    (symbol, last_updated, avg_spread, max_spread, avg_atr,
                     spread_ratio, adrenaline_score, is_tradeable, total_samples)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sym, datetime.utcnow().isoformat(),
                    avg_spread, max_spread, avg_atr,
                    spread_ratio, adrenaline, is_tradeable, total_samples
                ))
        
        conn.commit()
        conn.close()
        print(f"Updated profiles for {len(symbols)} symbols")
    
    def get_tradeable_symbols(self, max_spread_ratio: float = 10.0) -> List[Dict]:
        """Get symbols that are tradeable based on collected intelligence."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT symbol, avg_spread, avg_atr, spread_ratio, adrenaline_score, total_samples
            FROM symbol_profiles
            WHERE spread_ratio < ? AND total_samples >= 5
            ORDER BY adrenaline_score DESC
        """, (max_spread_ratio,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "symbol": row[0],
                "avg_spread": row[1],
                "avg_atr": row[2],
                "spread_ratio": row[3],
                "adrenaline_score": row[4],
                "samples": row[5]
            })
        
        conn.close()
        return results
    
    def print_intelligence_report(self, top_n: int = 30):
        """Print market intelligence report."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get sample count
        cursor.execute("SELECT COUNT(*) FROM spread_samples")
        total_samples = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) FROM spread_samples")
        total_symbols = cursor.fetchone()[0]
        
        print("\n" + "=" * 80)
        print("MARKET INTELLIGENCE REPORT")
        print("=" * 80)
        print(f"Total samples: {total_samples}")
        print(f"Symbols tracked: {total_symbols}")
        
        # Get top symbols by adrenaline
        cursor.execute("""
            SELECT symbol, avg_spread, avg_atr, spread_ratio, adrenaline_score, total_samples
            FROM symbol_profiles
            WHERE total_samples >= 3
            ORDER BY adrenaline_score DESC
            LIMIT ?
        """, (top_n,))
        
        print(f"\n{'Symbol':<20} {'AvgSpread':<10} {'ATR':<10} {'Ratio%':<10} {'Adrenaline':<12} {'Samples'}")
        print("-" * 80)
        
        for row in cursor.fetchall():
            symbol, avg_spread, avg_atr, ratio, adrenaline, samples = row
            ratio_str = f"{ratio:.1f}%" if ratio else "N/A"
            adr_str = f"{adrenaline:.1f}" if adrenaline else "N/A"
            print(f"{symbol:<20} {avg_spread or 0:<10.1f} {avg_atr or 0:<10.1f} {ratio_str:<10} {adr_str:<12} {samples}")
        
        conn.close()


def run_continuous_tracking(interval_minutes: int = 15):
    """Run continuous market tracking."""
    intel = MarketIntelligence()
    
    print("=" * 60)
    print("MARKET INTELLIGENCE TRACKER STARTED")
    print(f"Sampling every {interval_minutes} minutes")
    print("=" * 60)
    
    sample_count = 0
    
    while True:
        try:
            count = intel.sample_all_symbols()
            sample_count += 1
            
            now = datetime.now()
            print(f"\n[{now.strftime('%H:%M')}] Sample #{sample_count}: {count} symbols")
            
            # Calculate daily summary every hour
            if now.minute < interval_minutes:
                intel.calculate_daily_summary()
                intel.update_symbol_profiles()
            
            # Print report every 6 samples
            if sample_count % 6 == 0:
                intel.print_intelligence_report(top_n=15)
                
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    import sys
    
    intel = MarketIntelligence()
    mt5.initialize()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "sample":
            count = intel.sample_all_symbols()
            print(f"Sampled {count} symbols")
        
        elif sys.argv[1] == "summary":
            intel.calculate_daily_summary()
            intel.update_symbol_profiles()
        
        elif sys.argv[1] == "report":
            intel.print_intelligence_report()
        
        elif sys.argv[1] == "daemon":
            run_continuous_tracking(interval_minutes=15)
        
        elif sys.argv[1] == "tradeable":
            symbols = intel.get_tradeable_symbols()
            print(f"\n{len(symbols)} Tradeable Symbols (spread ratio < 10%):")
            for s in symbols[:20]:
                print(f"  {s['symbol']}: ratio={s['spread_ratio']:.1f}%, adrenaline={s['adrenaline_score']:.1f}")
    else:
        # Default: sample once
        count = intel.sample_all_symbols()
        print(f"Sampled {count} symbols")
        print("\nCommands:")
        print("  python market_intelligence.py sample   - Take one sample")
        print("  python market_intelligence.py summary  - Calculate daily summary")
        print("  python market_intelligence.py report   - Print intelligence report")
        print("  python market_intelligence.py daemon   - Run continuous tracking")
        print("  python market_intelligence.py tradeable - List tradeable symbols")
    
    mt5.shutdown()
