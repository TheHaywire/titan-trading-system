import polars as pl
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(name)s | %(levelname)s | %(message)s')
logger = logging.getLogger("Titan.Backtest")

class VectorBacktester:
    def __init__(self, data_path, symbol="Unknown"):
        self.data_path = data_path
        self.symbol = symbol
        self.df = None
        self.initial_capital = 10000.0
        
    def load_data(self):
        """Loads data from CSV/Parquet into Polars DataFrame"""
        try:
            # Detect file type
            if self.data_path.endswith('.csv'):
                self.df = pl.read_csv(self.data_path)
            elif self.data_path.endswith('.parquet'):
                self.df = pl.read_parquet(self.data_path)
            else:
                logger.error("Unsupported file format")
                return False
                
            # Ensure time is sorted
            self.df = self.df.sort("time")
            logger.info(f"Loaded {len(self.df)} rows for {self.symbol}")
            return True
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return False

    def run(self, strategy_func):
        """
        Runs a vectorized backtest.
        strategy_func: A function that takes the DataFrame and returns a list/series of signals (1, -1, 0)
        """
        if self.df is None:
            if not self.load_data(): return
            
        logger.info("🚀 Running Backtest...")
        start_time = datetime.now()
        
        # 1. Apply Strategy Logic (The "Alpha")
        # We pass the dataframe to the strategy, it returns a 'signal' column
        # Signals: 1 (Buy), -1 (Sell), 0 (Hold)
        
        # Add signals column
        df_strat = strategy_func(self.df)
        
        # 2. Vectorized P&L Calculation
        # We enter on the Open of the NEXT bar after the signal
        # Return = (Close - Open) * Direction
        # But commonly we trade Open-to-Open or Close-to-Close. 
        # Simplest Vector Model: Log Returns of Close Price * Shifted Signal
        
        # Calculate Percentage Returns of Price: ln(P_t / P_t-1)
        # Using Polars expressions
        df_res = df_strat.with_columns([
            (pl.col("close") / pl.col("close").shift(1)).log().alias("log_ret")
        ])
        
        # Shift signal by 1 (we trade based on PREVIOUS candle's signal)
        df_res = df_res.with_columns([
            pl.col("signal").shift(1).fill_null(0).alias("pos")
        ])
        
        # Strategy Returns = Market Returns * Position
        df_res = df_res.with_columns([
            (pl.col("log_ret") * pl.col("pos")).alias("strat_ret")
        ])
        
        # Equity Curve
        df_res = df_res.with_columns([
            (pl.col("strat_ret").cum_sum()).alias("cum_ret")
        ])
        
        # Stats
        total_return = df_res["strat_ret"].sum()
        win_rate = (df_res.filter(pl.col("strat_ret") > 0).height / 
                   (df_res.filter(pl.col("pos") != 0).height + 1e-9)) * 100
                   
        duration = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Backtest Complete in {duration:.4f}s")
        logger.info(f"📊 Total Return: {total_return*100:.2f}%")
        logger.info(f"🎯 Win Rate: {win_rate:.1f}%")
        
        return {
            "total_return": total_return,
            "win_rate": win_rate,
            "equity_curve": df_res["cum_ret"].to_list()[-1]
        }

if __name__ == "__main__":
    # Example Usage (requires data file to exist)
    pass
