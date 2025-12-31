
import MetaTrader5 as mt5
import pandas as pd
import logging
from titan_system.db.database import Database
from titan_system.backtest.engine import Backtester
from titan_system.strategies.trend_surfer import TrendSurfer
from titan_system.strategies.scalper import MomentumScalper
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Titan.Optimizer")

class StrategyOptimizer:
    def __init__(self):
        self.db = Database(settings.db_path)
        self.backtester = Backtester(initial_capital=10000.0)
        
        # Define Universe of Strategies
        # We usage default configs for now. 
        # Advanced: Genetic Algos would tweak these params.
        self.strategies = [
            TrendSurfer(config={"fast_period": 50, "slow_period": 200, "adx_threshold": 20}),
            MomentumScalper(config={"rsi_period": 14, "adx_threshold": 25})
        ]

    def connect(self):
        if not mt5.initialize():
            return False
        if settings.mt5_login:
            mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)
        return True

    def optimize_universe(self, limit=50):
        """
        1. Fetch Active Universe (Top 50 volatile) from DB.
        2. Download history (1000 candles).
        3. Run all strategies.
        4. Update DB with winner.
        """
        logger.info("🧪 Starting Strategy Optimization...")
        
        # 1. Get Targets
        symbols = self.db.get_active_universe(limit=limit)
        if not symbols:
            logger.warning("No active universe found. Run Recon first!")
            return

        logger.info(f"optimizing {len(symbols)} symbols: {symbols}")
        
        updates = []
        
        for symbol in symbols:
            logger.info(f"  > Testing {symbol}...")
            
            # 2. Get Data (H1)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000)
            if rates is None or len(rates) < 500:
                logger.warning(f"    Skipping {symbol} (No Data)")
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            # volume mapping
            if 'tick_volume' in df.columns: df['volume'] = df['tick_volume']
            
            best_score = -99999
            best_strat_name = "HOLD"
            
            # 3. Competition
            for strat in self.strategies:
                result = self.backtester.run(strat, symbol, df)
                score = result['profit'] # Using Net Profit as metric
                trades = result['trades']
                
                logger.info(f"    - {strat.name}: ${score:.2f} ({trades} trades)")
                
                if score > best_score and trades > 5: # Min trade filter
                    best_score = score
                    best_strat_name = strat.name
            
            # 4. Record Winner
            logger.info(f"    🏆 Winner: {best_strat_name} (${best_score:.2f}%)")
            
            # IMMEDIATE UPDATE:
            # We update the DB immediately so the running TitanEngine can pick it up.
            self._update_symbol(symbol, best_strat_name, float(best_score))

        logger.info("✅ Optimization Complete.")

    def _update_symbol(self, symbol, strategy, score):
        try:
            conn = self.db._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE market_universe 
                SET active_strategy = ?, backtest_score = ?
                WHERE symbol = ?
            ''', (strategy, score, symbol))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to update DB for {symbol}: {e}")

if __name__ == "__main__":
    opt = StrategyOptimizer()
    if opt.connect():
        opt.optimize_universe()
