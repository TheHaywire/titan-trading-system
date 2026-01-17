"""
Comprehensive Market Intelligence System
=========================================
Tracks ALL critical trading metrics that aren't in historical data:

DATA COLLECTED:
1. Spread Metrics: current, min, max, avg, std, by hour/session
2. Volume Metrics: tick volume by hour, volume spikes
3. Price Movement: ATR, spread ratio, adrenaline score
4. Time Analysis: best hours, session profiles, day-of-week patterns
5. Risk Metrics: max spread, swap rates, margin requirements
6. Contract Specs: point value, lot sizes, trade modes

Run as daemon to collect continuously, then query for insights.
"""
import MetaTrader5 as mt5
import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict
import time

DB_PATH = "data/comprehensive_intel.db"

# Key symbols to track in detail
KEY_SYMBOLS = [
    # Forex
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF",
    "EURGBP", "EURJPY", "GBPJPY",
    # Commodities
    "GOLD", "SILVER", "OILCash", "BRENTCash", "XAUEUR",
    # Indices
    "US100Cash", "US30Cash", "US500Cash", "GER40Cash", "UK100Cash", 
    "JP225Cash", "AUS200Cash", "HK50Cash",
    # Crypto
    "BTCUSD", "ETHUSD", "XRPUSD", "LTCUSD",
]


class ComprehensiveIntel:
    """Full-spectrum market intelligence collector."""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database with all required tables."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 1. Tick samples (high frequency data)
        c.execute("""
            CREATE TABLE IF NOT EXISTS tick_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                symbol TEXT NOT NULL,
                bid REAL,
                ask REAL,
                spread INTEGER,
                tick_volume INTEGER,
                last_price REAL,
                hour INTEGER,
                minute INTEGER,
                weekday INTEGER,
                session TEXT
            )
        """)
        
        # 2. Hourly aggregates
        c.execute("""
            CREATE TABLE IF NOT EXISTS hourly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                hour INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                min_spread INTEGER,
                max_spread INTEGER,
                avg_spread REAL,
                total_volume INTEGER,
                high REAL,
                low REAL,
                range_pips REAL,
                samples INTEGER,
                UNIQUE(date, hour, symbol)
            )
        """)
        
        # 3. Session profiles
        c.execute("""
            CREATE TABLE IF NOT EXISTS session_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                session TEXT NOT NULL,
                avg_spread REAL,
                min_spread INTEGER,
                max_spread INTEGER,
                avg_volume REAL,
                avg_range REAL,
                spread_ratio REAL,
                samples INTEGER,
                last_updated TEXT,
                UNIQUE(symbol, session)
            )
        """)
        
        # 4. Symbol master data (static + calculated)
        c.execute("""
            CREATE TABLE IF NOT EXISTS symbol_master (
                symbol TEXT PRIMARY KEY,
                description TEXT,
                category TEXT,
                currency TEXT,
                point REAL,
                digits INTEGER,
                lot_min REAL,
                lot_max REAL,
                lot_step REAL,
                contract_size REAL,
                margin_initial REAL,
                swap_long REAL,
                swap_short REAL,
                swap_mode INTEGER,
                trade_mode INTEGER,
                -- Calculated fields
                avg_h1_atr REAL,
                avg_spread REAL,
                spread_ratio REAL,
                adrenaline_score REAL,
                best_session TEXT,
                worst_session TEXT,
                is_tradeable INTEGER,
                last_updated TEXT
            )
        """)
        
        # 5. Daily summary
        c.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol TEXT NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                daily_range REAL,
                avg_spread REAL,
                max_spread INTEGER,
                total_volume INTEGER,
                best_hour INTEGER,
                worst_hour INTEGER,
                samples INTEGER,
                UNIQUE(date, symbol)
            )
        """)
        
        # 6. Correlation matrix (updated daily)
        c.execute("""
            CREATE TABLE IF NOT EXISTS correlations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                symbol1 TEXT NOT NULL,
                symbol2 TEXT NOT NULL,
                correlation REAL,
                UNIQUE(date, symbol1, symbol2)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_session(self, hour: int) -> str:
        """Get trading session name from UTC hour."""
        if 0 <= hour < 7:
            return "ASIAN"
        elif 7 <= hour < 12:
            return "LONDON"
        elif 12 <= hour < 17:
            return "OVERLAP"
        elif 17 <= hour < 21:
            return "NEW_YORK"
        else:
            return "AFTER_HOURS"
    
    def _get_category(self, symbol: str) -> str:
        """Categorize a symbol."""
        sym = symbol.upper()
        if any(x in sym for x in ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]) and len(sym) == 6:
            return "FOREX"
        elif any(x in sym for x in ["GOLD", "SILVER", "XAU", "XAG"]):
            return "METALS"
        elif any(x in sym for x in ["OIL", "BRENT", "GAS"]):
            return "ENERGY"
        elif any(x in sym for x in ["BTC", "ETH", "XRP", "LTC", "CRYPTO"]):
            return "CRYPTO"
        elif any(x in sym for x in ["100", "500", "30", "40", "225", "200", "50", "CASH"]):
            return "INDEX"
        else:
            return "OTHER"
    
    def update_symbol_master(self, symbols: List[str] = None):
        """Update static symbol information from MT5."""
        if not mt5.initialize():
            return
        
        if symbols is None:
            symbols = KEY_SYMBOLS
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        for sym in symbols:
            info = mt5.symbol_info(sym)
            if not info:
                continue
            
            # Get ATR
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 24)
            if rates is not None and len(rates) > 0:
                atr = sum(r['high'] - r['low'] for r in rates) / len(rates)
                atr_points = atr / info.point if info.point > 0 else 0
            else:
                atr_points = 0
            
            spread_ratio = (info.spread / atr_points * 100) if atr_points > 0 else 100
            adrenaline = atr_points / info.spread if info.spread > 0 else 0
            is_tradeable = 1 if spread_ratio < 15 and info.trade_mode == 4 else 0
            
            c.execute("""
                INSERT OR REPLACE INTO symbol_master
                (symbol, description, category, currency, point, digits,
                 lot_min, lot_max, lot_step, contract_size, margin_initial,
                 swap_long, swap_short, swap_mode, trade_mode,
                 avg_h1_atr, avg_spread, spread_ratio, adrenaline_score,
                 is_tradeable, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sym, info.description, self._get_category(sym), info.currency_profit,
                info.point, info.digits, info.volume_min, info.volume_max,
                info.volume_step, info.trade_contract_size, info.margin_initial,
                info.swap_long, info.swap_short, info.swap_mode, info.trade_mode,
                atr_points, info.spread, spread_ratio, adrenaline,
                is_tradeable, datetime.utcnow().isoformat()
            ))
        
        conn.commit()
        conn.close()
        print(f"Updated symbol master for {len(symbols)} symbols")
    
    def collect_tick_sample(self, symbols: List[str] = None) -> int:
        """Collect current tick data for all symbols."""
        if not mt5.initialize():
            return 0
        
        if symbols is None:
            symbols = KEY_SYMBOLS
        
        now = datetime.utcnow()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        count = 0
        for sym in symbols:
            try:
                info = mt5.symbol_info(sym)
                tick = mt5.symbol_info_tick(sym)
                
                if info and tick:
                    c.execute("""
                        INSERT INTO tick_samples
                        (timestamp, symbol, bid, ask, spread, tick_volume, last_price,
                         hour, minute, weekday, session)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        now.isoformat(), sym, tick.bid, tick.ask, info.spread,
                        tick.volume, tick.last, now.hour, now.minute,
                        now.weekday(), self._get_session(now.hour)
                    ))
                    count += 1
            except Exception as e:
                pass
        
        conn.commit()
        conn.close()
        return count
    
    def calculate_hourly_stats(self, date: str = None, hour: int = None):
        """Calculate hourly statistics from tick samples."""
        if date is None:
            date = datetime.utcnow().strftime("%Y-%m-%d")
        if hour is None:
            hour = datetime.utcnow().hour
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Get all symbols for this hour
        c.execute("""
            SELECT DISTINCT symbol FROM tick_samples
            WHERE timestamp LIKE ? AND hour = ?
        """, (f"{date}%", hour))
        
        symbols = [row[0] for row in c.fetchall()]
        
        for sym in symbols:
            c.execute("""
                SELECT 
                    MIN(spread), MAX(spread), AVG(spread),
                    SUM(tick_volume), MAX(last_price), MIN(last_price), COUNT(*)
                FROM tick_samples
                WHERE symbol = ? AND timestamp LIKE ? AND hour = ?
            """, (sym, f"{date}%", hour))
            
            row = c.fetchone()
            if row and row[6] > 0:
                min_spread, max_spread, avg_spread = row[0], row[1], row[2]
                total_vol, high, low, samples = row[3], row[4], row[5], row[6]
                
                info = mt5.symbol_info(sym)
                range_pips = (high - low) / info.point if info and info.point > 0 else 0
                
                c.execute("""
                    INSERT OR REPLACE INTO hourly_stats
                    (date, hour, symbol, min_spread, max_spread, avg_spread,
                     total_volume, high, low, range_pips, samples)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    date, hour, sym, min_spread, max_spread, avg_spread,
                    total_vol or 0, high, low, range_pips, samples
                ))
        
        conn.commit()
        conn.close()
    
    def update_session_profiles(self):
        """Update session profiles from hourly data."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        sessions = {
            "ASIAN": range(0, 7),
            "LONDON": range(7, 12),
            "OVERLAP": range(12, 17),
            "NEW_YORK": range(17, 21),
            "AFTER_HOURS": range(21, 24)
        }
        
        c.execute("SELECT DISTINCT symbol FROM hourly_stats")
        symbols = [row[0] for row in c.fetchall()]
        
        for sym in symbols:
            for session_name, hours in sessions.items():
                hours_list = list(hours)
                placeholders = ",".join("?" * len(hours_list))
                
                c.execute(f"""
                    SELECT 
                        AVG(avg_spread), MIN(min_spread), MAX(max_spread),
                        AVG(total_volume), AVG(range_pips), SUM(samples)
                    FROM hourly_stats
                    WHERE symbol = ? AND hour IN ({placeholders})
                """, [sym] + hours_list)
                
                row = c.fetchone()
                if row and row[5] and row[5] > 0:
                    avg_spread, min_spread, max_spread = row[0], row[1], row[2]
                    avg_volume, avg_range, samples = row[3], row[4], row[5]
                    
                    spread_ratio = (avg_spread / avg_range * 100) if avg_range and avg_range > 0 else 100
                    
                    c.execute("""
                        INSERT OR REPLACE INTO session_profiles
                        (symbol, session, avg_spread, min_spread, max_spread,
                         avg_volume, avg_range, spread_ratio, samples, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        sym, session_name, avg_spread, min_spread, max_spread,
                        avg_volume, avg_range, spread_ratio, samples,
                        datetime.utcnow().isoformat()
                    ))
        
        conn.commit()
        conn.close()
    
    def get_symbol_intelligence(self, symbol: str) -> Dict:
        """Get complete intelligence for a symbol."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        result = {"symbol": symbol}
        
        # Master data
        c.execute("SELECT * FROM symbol_master WHERE symbol = ?", (symbol,))
        row = c.fetchone()
        if row:
            cols = [d[0] for d in c.description]
            result["master"] = dict(zip(cols, row))
        
        # Session profiles
        c.execute("SELECT * FROM session_profiles WHERE symbol = ?", (symbol,))
        rows = c.fetchall()
        if rows:
            cols = [d[0] for d in c.description]
            result["sessions"] = [dict(zip(cols, row)) for row in rows]
        
        # Recent hourly stats
        c.execute("""
            SELECT * FROM hourly_stats 
            WHERE symbol = ? 
            ORDER BY date DESC, hour DESC LIMIT 24
        """, (symbol,))
        rows = c.fetchall()
        if rows:
            cols = [d[0] for d in c.description]
            result["recent_hourly"] = [dict(zip(cols, row)) for row in rows]
        
        conn.close()
        return result
    
    def print_intelligence_report(self):
        """Print comprehensive market intelligence report."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE MARKET INTELLIGENCE REPORT")
        print("=" * 80)
        
        # Stats
        c.execute("SELECT COUNT(*) FROM tick_samples")
        tick_count = c.fetchone()[0]
        c.execute("SELECT COUNT(DISTINCT symbol) FROM symbol_master")
        symbol_count = c.fetchone()[0]
        
        print(f"\nTotal tick samples: {tick_count:,}")
        print(f"Symbols tracked: {symbol_count}")
        
        # Top tradeable symbols
        c.execute("""
            SELECT symbol, category, avg_spread, avg_h1_atr, spread_ratio, 
                   adrenaline_score, swap_long, swap_short, is_tradeable
            FROM symbol_master
            WHERE is_tradeable = 1
            ORDER BY adrenaline_score DESC
            LIMIT 20
        """)
        
        print("\n" + "-" * 80)
        print("TOP TRADEABLE SYMBOLS (by Adrenaline Score)")
        print("-" * 80)
        print(f"{'Symbol':<12} {'Cat':<8} {'Spread':<8} {'ATR':<10} {'Ratio%':<8} {'Adrenaline':<12} {'SwapL':<8} {'SwapS':<8}")
        
        for row in c.fetchall():
            sym, cat, spread, atr, ratio, adr, swapL, swapS, _ = row
            print(f"{sym:<12} {cat:<8} {spread or 0:<8.0f} {atr or 0:<10.0f} {ratio or 0:<8.1f} {adr or 0:<12.1f} {swapL or 0:<8.2f} {swapS or 0:<8.2f}")
        
        # Session comparison for key symbols
        print("\n" + "-" * 80)
        print("SESSION PROFILES (Key Symbols)")
        print("-" * 80)
        
        for sym in ["GOLD", "US100Cash", "EURUSD"]:
            c.execute("""
                SELECT session, avg_spread, avg_range, spread_ratio
                FROM session_profiles
                WHERE symbol = ?
                ORDER BY spread_ratio
            """, (sym,))
            
            rows = c.fetchall()
            if rows:
                print(f"\n{sym}:")
                print(f"  {'Session':<15} {'AvgSpread':<12} {'AvgRange':<12} {'Ratio%'}")
                for row in rows:
                    sess, spread, rng, ratio = row
                    print(f"  {sess:<15} {spread or 0:<12.1f} {rng or 0:<12.0f} {ratio or 0:.1f}%")
        
        conn.close()
    
    def export_to_json(self, filepath: str = "data/market_intelligence_export.json"):
        """Export all intelligence to JSON."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        export = {
            "generated_at": datetime.utcnow().isoformat(),
            "symbols": {}
        }
        
        c.execute("SELECT symbol FROM symbol_master")
        symbols = [row[0] for row in c.fetchall()]
        
        for sym in symbols:
            export["symbols"][sym] = self.get_symbol_intelligence(sym)
        
        with open(filepath, 'w') as f:
            json.dump(export, f, indent=2, default=str)
        
        conn.close()
        print(f"Exported intelligence for {len(symbols)} symbols to {filepath}")


def run_comprehensive_daemon(sample_interval_minutes: int = 5):
    """Run comprehensive data collection."""
    intel = ComprehensiveIntel()
    
    print("=" * 60)
    print("COMPREHENSIVE MARKET INTELLIGENCE DAEMON")
    print(f"Sampling every {sample_interval_minutes} minutes")
    print(f"Tracking {len(KEY_SYMBOLS)} key symbols")
    print("=" * 60)
    
    # Initial setup
    intel.update_symbol_master()
    
    sample_count = 0
    last_hourly = -1
    
    while True:
        try:
            # Collect tick sample
            count = intel.collect_tick_sample()
            sample_count += 1
            now = datetime.utcnow()
            
            print(f"\n[{now.strftime('%H:%M')} UTC] Sample #{sample_count}: {count} symbols")
            
            # Hourly calculations
            if now.hour != last_hourly:
                print("  → Calculating hourly stats...")
                intel.calculate_hourly_stats()
                intel.update_session_profiles()
                intel.update_symbol_master()
                last_hourly = now.hour
            
            # Report every 12 samples (1 hour at 5min intervals)
            if sample_count % 12 == 0:
                intel.print_intelligence_report()
            
        except Exception as e:
            print(f"[ERROR] {e}")
        
        time.sleep(sample_interval_minutes * 60)


if __name__ == "__main__":
    import sys
    
    intel = ComprehensiveIntel()
    mt5.initialize()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        
        if cmd == "daemon":
            run_comprehensive_daemon()
        elif cmd == "sample":
            count = intel.collect_tick_sample()
            print(f"Collected {count} tick samples")
        elif cmd == "master":
            intel.update_symbol_master()
        elif cmd == "hourly":
            intel.calculate_hourly_stats()
            intel.update_session_profiles()
        elif cmd == "report":
            intel.print_intelligence_report()
        elif cmd == "export":
            intel.export_to_json()
        elif cmd == "intel":
            symbol = sys.argv[2] if len(sys.argv) > 2 else "GOLD"
            data = intel.get_symbol_intelligence(symbol)
            print(json.dumps(data, indent=2, default=str))
    else:
        print("Comprehensive Market Intelligence System")
        print("\nCommands:")
        print("  daemon  - Run continuous collection (5 min intervals)")
        print("  sample  - Take single tick sample")
        print("  master  - Update symbol master data")
        print("  hourly  - Calculate hourly stats")
        print("  report  - Print full report")
        print("  export  - Export to JSON")
        print("  intel SYMBOL - Get complete intel for a symbol")
    
    mt5.shutdown()
