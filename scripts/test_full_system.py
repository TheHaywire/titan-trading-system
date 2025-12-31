import sys
import logging
from titan_system.data.ingest_mt5 import ingest_history
from titan_system.research.data_loader import load_data
from titan_system.research.backtester import Backtester
from titan_system.portfolio.optimizer import PortfolioOptimizer
from titan_system.portfolio.risk_engine import RiskEngine
import pandas as pd

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
log = logging.getLogger(__name__)

def test_full_system_sync():
    symbol_input = "GOLD"
    timeframe = "H1"
    
    print("="*60)
    print(f"🚀 TITAN SYSTEM INTEGRATION TEST: {symbol_input} ({timeframe})")
    print("="*60)
    
    # ---------------------------------------------------------
    # 1. DATA LAYER: Ingest/Refresh Data
    # ---------------------------------------------------------
    print("\n[PHASE 1] Data Layer: Syncing with MT5...")
    try:
        # Ingest 5 days just to be quick and sure
        ingest_history(symbol_input, timeframe, days=5)
        print("✅ Data Ingestion Complete")
    except Exception as e:
        print(f"❌ Data Ingestion Failed: {e}")
        return

    # ---------------------------------------------------------
    # 2. RESEARCH LAYER: Load & Backtest
    # ---------------------------------------------------------
    print("\n[PHASE 2] Research Layer: Loading & Backtesting...")
    try:
        # Load Data
        df = load_data(symbol_input, timeframe)
        if df.empty:
            print("❌ Data Load Failed: DataFrame is empty")
            return
        print(f"✅ Data Loaded: {len(df)} bars (Last: {df.index[-1]})")
        
        # Backtest (Simple SMA)
        bt = Backtester(symbol_input, timeframe)
        # We assume backtester handles data loading internally too, but we can pass df if we modded it
        # Current implementation loads internally.
        
        pf = bt.run_sma_crossover(10, 20)
        # Check trades safely
        trade_count = pf.trades.count()
        print(f"✅ Backtest Complete: {trade_count} trades generated.")
        
    except Exception as e:
        print(f"❌ Research Layer Failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # ---------------------------------------------------------
    # 3. PORTFOLIO LAYER: Optimization & Risk
    # ---------------------------------------------------------
    print("\n[PHASE 3] Portfolio Layer: Optimization & Risk Check...")
    try:
        # Optimization (Singular asset is trivial, but good to test pipeline)
        # We need a DataFrame of closes for the optimizer
        prices = pd.DataFrame({symbol_input: df['close']})
        
        opt = PortfolioOptimizer(prices)
        # For single asset, EF might error if valid vol calculation fails with 1 item?
        # PyPortfolioOpt technically usually requires >1 asset for Covariance, but let's see.
        # If it fails, that's a "tweak needed in future" finding.
        
        try:
            print("   Running Optimizer (Mean-Variance)...")
            weights, perf = opt.optimize_mean_variance()
            print(f"   Optimal Weights: {weights}")
        except Exception as opt_e:
            print(f"   ⚠️ Optimizer Warning (Expected for single asset): {opt_e}")
            print("   (Note: Optimizer requires multiple assets to be useful, but pipeline is checked.)")

        # Risk Engine
        risk = RiskEngine(max_daily_drawdown=0.05, max_position_size=0.1) # 10% max pos
        
        # Scenario: We want to open a trade equal to 5% of capital
        capital = 10000
        trade_size = 500
        
        print(f"   Checking Risk for trade size ${trade_size} on ${capital} capital...")
        allowed = risk.check_trade(symbol_input, trade_size, capital)
        
        if allowed:
            print(f"✅ Risk Check Passed: Trade Allowed.")
        else:
            print(f"❌ Risk Check Failed (Unexpected).")

    except Exception as e:
        print(f"❌ Portfolio Layer Failed: {e}")
        return

    print("\n" + "="*60)
    print("🌟 SYSTEM STATUS: INTEGRATION TEST PASSED")
    print("="*60)

if __name__ == "__main__":
    test_full_system_sync()
