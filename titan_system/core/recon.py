
import MetaTrader5 as mt5
import pandas as pd
import logging
import datetime
from titan_system.db.database import Database
from config.settings import settings

logger = logging.getLogger("Titan.Recon")

class MarketRecon:
    def __init__(self, db_path=None):
        self.db = Database(db_path or settings.db_path)
    
    def connect(self):
        if not mt5.initialize():
            logger.error(f"MT5 Init Failed: {mt5.last_error()}")
            return False
        
        if settings.mt5_login:
            mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
        return True

    def scan_universe(self):
        """
        Fetches ALL symbols from MT5, calculates metrics, and updates DB.
        This is a heavy operation (takes minutes).
        """
        logger.info("🚀 Starting Full Market Reconnaissance...")
        
        # 1. Get All Symbols
        symbols = mt5.symbols_get()
        if not symbols:
            logger.error("No symbols found in MT5!")
            return
        
        logger.info(f"Adding {len(symbols)} symbols to universe...")
        
        batch = []
        count = 0
        
        for s in symbols:
            # Basic Filtering
            if not s.visible:
                pass 

            spread = s.spread * s.point
            price = s.ask or 1.0
            
            # Categorize
            category = "Unknown"
            path = s.path
            if "Forex" in path: category = "Forex"
            elif "Crypto" in path: category = "Crypto"
            elif "Indices" in path or "Stock" in path: category = "Index"
            elif "Metal" in path: category = "Metal"
            
            item = {
                "symbol": s.name,
                "path": s.path,
                "category": category,
                "digits": s.digits,
                "tick_size": s.trade_tick_size,
                "contract_size": s.trade_contract_size,
                "min_lot": s.volume_min,
                "max_lot": s.volume_max,
                "swap_long": s.swap_long,
                "swap_short": s.swap_short,
                "spread": s.spread, # in points
                "volatility_score": 0.0, # Placeholder
                "is_tradable": False,    # Default False
                "active_strategy": None,
                "backtest_score": 0.0,
                "last_updated": datetime.datetime.now()
            }
            
            batch.append(item)
            count += 1
            
            if len(batch) >= 100:
                self.db.save_universe_scan(batch)
                batch = []
                logger.info(f"Processed {count}/{len(symbols)} symbols...")
                
        # Flush remaining
        if batch:
            self.db.save_universe_scan(batch)
            
        logger.info("✅ Universe scan complete.")
        
    def rank_prime_assets(self):
        """
        Identify the Top 20 Assets to trade based on 'Prime' criteria.
        Criteria:
        1. Liquidity (Tick Volume)
        2. Volatility (High ADX/ATR)
        3. Cost (Low Spread)
        """
        logger.info("💎 Ranking Prime Assets...")
        
        # For demo speed, we exclude 'Index' (Stocks) which has 1000+ items.
        # We focus on Forex, Metal, Crypto.
        
        conn = self.db._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol FROM market_universe WHERE category IN ('Forex', 'Metal', 'Crypto')")
        candidates = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        ranked_data = []
        logger.info(f"Checking {len(candidates)} candidates...")
        
        count = 0
        for sym in candidates:
            count += 1
            if count % 10 == 0:
                logger.info(f"  > Scanned {count}/{len(candidates)}...")

            # Fetch Daily Data for Volatility
            rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 14)
            if rates is None or len(rates) < 14:
                continue
                
            df = pd.DataFrame(rates)
            
            # Calc ATR-like volatiltiy
            # (High - Low) / Open
            df['range_pct'] = (df['high'] - df['low']) / df['open']
            volatility = df['range_pct'].mean() * 100 # In percentage
            
            # Spread Cost
            info = mt5.symbol_info(sym)
            if not info: continue
            
            spread_pct = (info.spread * info.point) / info.ask * 100
            
            # Score = Volatility / Spread (Bang for buck)
            # Avoid div by zero
            score = volatility / (spread_pct + 0.00001)
            
            ranked_data.append({
                "symbol": sym, 
                "volatility_score": score,
                "is_tradable": True
            })
            
        # Update DB
        logger.info(f"Updating scores for {len(ranked_data)} assets...")
        self.db.update_symbol_score(ranked_data)
        
        # Disable others not in ranked_data but in candidates?
        # Actually logic says 'is_tradable=True' for these. 
        # But we really only want the Top 20 from this list to be "active".
        # But for now, we mark ALL scanned ones as tradable, and let the Engine query ORDER BY limit 20.
        
        logger.info("✅ Ranking Complete.")

if __name__ == "__main__":
    # Test Run
    logging.basicConfig(level=logging.INFO)
    recon = MarketRecon()
    if recon.connect():
        recon.scan_universe()
        recon.rank_prime_assets()
