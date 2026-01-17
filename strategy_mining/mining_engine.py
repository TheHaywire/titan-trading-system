"""
Main Orchestrator for Brute-Force Strategy Mining & Execution Engine
Triggers the full pipeline: Data Fetch -> Mining -> WFA -> Execution.
Now with BATCH PROCESSING support for comprehensive symbol mining.
"""

import logging
import pandas as pd
import threading
import time
from strategy_mining.data_engine import DataEngine
from strategy_mining.backtester import BacktestingEngine
from strategy_mining.walk_forward import WalkForwardAnalyzer
from strategy_mining.execution_engine import ExecutionEngine
from strategy_mining.progress_logger import ProgressLogger
import strategy_mining.mining_config as config
import os

# Setup logging
def setup_logging():
    ensure_directories()
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(os.path.join(config.LOGS_DIR, "engine.log")),
                            logging.StreamHandler()
                        ])
    return logging.getLogger("MiningEngine")

def ensure_directories():
    """Create necessary directories if they don't exist."""
    for d in [config.RESULTS_DIR, config.LOGS_DIR, config.CACHE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

# Placeholder logger until setup_logging is called
logger = logging.getLogger("MiningEngine")

def run_batch_mining(batch_symbols, batch_num, total_batches, progress_logger, all_results):
    """Process a single batch of symbols and return robust strategies."""
    progress_logger.log_batch_start(batch_num, total_batches, batch_symbols)
    
    # Initialize engine
    engine = DataEngine()
    
    # Data Fetching
    progress_logger.log_phase("Data Fetch", f"Starting for {len(batch_symbols)} symbols")
    df = engine.parallel_fetch_all(batch_symbols, list(config.TIMEFRAMES.keys()))
    
    if df.empty:
        progress_logger.log_error(batch_num, "No data fetched for this batch")
        return pd.DataFrame()
    
    progress_logger.log_phase("Data Fetch", "Complete")
    
    # Combinatorial Backtesting
    progress_logger.log_phase("Backtesting", "Running parameter combinations")
    backtester = BacktestingEngine(df)
    results = backtester.run_all_combinations()
    
    if results.empty:
        progress_logger.log_phase("Backtesting", "No candidates passed filters")
        return pd.DataFrame()
    
    progress_logger.log_phase("Backtesting", f"Found {len(results)} candidates")
    
    # Walk-Forward Analysis
    progress_logger.log_phase("WFA Validation", "Testing robustness")
    wf_analyzer = WalkForwardAnalyzer(df)
    robust_winners = wf_analyzer.filter_robust_strategies(results)
    
    if robust_winners.empty:
        progress_logger.log_phase("WFA Validation", "No robust strategies found")
        return pd.DataFrame()
    
    progress_logger.log_phase("WFA Validation", f"Found {len(robust_winners)} robust strategies")
    
    # Save batch results
    batch_file = os.path.join(config.RESULTS_DIR, f"batch_{batch_num}_results.csv")
    robust_winners.to_csv(batch_file, index=False)
    progress_logger.log_phase("Persistence", f"Saved to {os.path.basename(batch_file)}")
    
    # Update totals
    total_found = len(all_results) + len(robust_winners)
    progress_logger.log_batch_complete(batch_num, len(robust_winners), total_found)
    
    return robust_winners

def run_mining_pipeline():
    """Run the full brute-force mining and validation pipeline with batch processing."""
    global logger
    logger = setup_logging()
    
    # Initialize progress logger
    progress_logger = ProgressLogger()
    
    # 0. Check for existing results (Persistence)
    winners_path = os.path.join(config.RESULTS_DIR, config.WINNERS_FILE)
    if not config.FORCE_REMINE and os.path.exists(winners_path):
        logger.info(f"Existing winners found at {winners_path}. Loading state...")
        try:
            top_5 = pd.read_csv(winners_path)
            if not top_5.empty:
                logger.info(f"Successfully loaded {len(top_5)} winners. Skipping mining phase.")
                return top_5
        except Exception as e:
            logger.error(f"Failed to load existing winners: {e}. Proceeding to remine.")

    # 1. Initialize Engine & Discover Symbols
    engine = DataEngine()
    
    # Check if using Sniper Mode or Full Mining
    if hasattr(config, 'USE_SNIPER_MODE') and config.USE_SNIPER_MODE:
        # Sniper Mode: Use predefined list
        logger.info(f"Sniper Mode: Initializing mining on {len(config.SNIPER_LIST)} top-tier symbols...")
        import MetaTrader5 as mt5
        symbols = []
        for s in config.SNIPER_LIST:
            if mt5.symbol_select(s, True):
                symbols.append(s)
    else:
        # Full Mining Mode: Get all visible symbols
        logger.info("Full Mining Mode: Discovering all visible symbols...")
        symbols = engine.get_market_watch_symbols()
    
    if not symbols:
        logger.error("No tradable symbols found. Check MT5 connection and credentials.")
        return None

    # 2. Batch Processing
    batch_size = getattr(config, 'BATCH_SIZE', 100)
    total_batches = (len(symbols) + batch_size - 1) // batch_size
    
    progress_logger.log_mining_start(len(symbols), batch_size)
    
    # Process in batches
    all_results = []
    for i in range(total_batches):
        batch_num = i + 1
        start_idx = i * batch_size
        end_idx = min((i + 1) * batch_size, len(symbols))
        batch_symbols = symbols[start_idx:end_idx]
        
        try:
            batch_results = run_batch_mining(batch_symbols, batch_num, total_batches, 
                                            progress_logger, all_results)
            if not batch_results.empty:
                all_results.append(batch_results)
        except Exception as e:
            progress_logger.log_error(batch_num, str(e))
            logger.error(f"Batch {batch_num} failed: {e}")
            continue
    
    # 3. Consolidate Results
    if not all_results:
        logger.warning("No robust strategies found across all batches.")
        return None
    
    robust_winners = pd.concat(all_results, ignore_index=True)
    progress_logger.log_mining_complete(len(robust_winners))
    
    # 4. Save Consolidated Results
    output_path = os.path.join(config.RESULTS_DIR, config.MINING_RESULTS_FILE)
    robust_winners.to_csv(output_path, index=False)
    logger.info(f"Consolidated results saved to {output_path}")
    
    # 5. Select Top 5 Winners
    top_5 = robust_winners.head(config.TOP_WINNERS_COUNT)
    
    # Save Top Winners for persistence
    top_5.to_csv(os.path.join(config.RESULTS_DIR, config.WINNERS_FILE), index=False)
    
    logger.info("TOP WINNERS SELECTED FOR LIVE EXECUTION:")
    print(top_5[['symbol', 'timeframe', 'strategy', 'profit_factor', 'oos_profitable_windows']])
    
    return top_5

def mt5_heartbeat():
    """Background thread to keep MT5 connection alive and prevent socket timeouts."""
    import MetaTrader5 as mt5
    while True:
        if not mt5.initialize():
            print(f"Heartbeat failed to initialize MT5: {mt5.last_error()}")
        time.sleep(config.HEARTBEAT_INTERVAL_SEC)

if __name__ == "__main__":
    # Start the Mining Phase
    top_winners = run_mining_pipeline()
    
    if top_winners is not None and not top_winners.empty:
        # Start Heartbeat Thread
        heartbeat_thread = threading.Thread(target=mt5_heartbeat, daemon=True)
        heartbeat_thread.start()
        logger.info(f"Heartbeat thread started (Interval: {config.HEARTBEAT_INTERVAL_SEC}s)")
        
        # Start the 24/7 Live Execution Phase
        executor = ExecutionEngine(top_winners)
        executor.start_live_loop()
    else:
        logger.error("System could not find any profitable/robust strategies to trade.")
