"""
MINING-ONLY Mode: Just discover strategies, don't execute them.
Run this to backtest all symbols and save the results to CSV.
"""

import logging
import pandas as pd
from strategy_mining.data_engine import DataEngine
from strategy_mining.backtester import BacktestingEngine
from strategy_mining.walk_forward import WalkForwardAnalyzer
from strategy_mining.progress_logger import ProgressLogger
import strategy_mining.mining_config as config
import os

def ensure_directories():
    """Create necessary directories if they don't exist."""
    for d in [config.RESULTS_DIR, config.LOGS_DIR, config.CACHE_DIR]:
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)

def run_batch_mining(batch_symbols, batch_num, total_batches, progress_logger, all_results):
    """Process a single batch of symbols and return robust strategies."""
    progress_logger.log_batch_start(batch_num, total_batches, batch_symbols)
    
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
    
    total_found = len(all_results) + len(robust_winners)
    progress_logger.log_batch_complete(batch_num, len(robust_winners), total_found)
    
    return robust_winners

if __name__ == "__main__":
    ensure_directories()
    progress_logger = ProgressLogger()
    
    # Get all symbols
    engine = DataEngine()
    symbols = engine.get_market_watch_symbols()
    
    if not symbols:
        print("ERROR: No symbols found. Check MT5 connection.")
        exit(1)
    
    # Batch processing
    batch_size = getattr(config, 'BATCH_SIZE', 100)
    total_batches = (len(symbols) + batch_size - 1) // batch_size
    
    progress_logger.log_mining_start(len(symbols), batch_size)
    
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
            print(f"ERROR in Batch {batch_num}: {e}")
            continue
    
    # Consolidate results
    if not all_results:
        print("WARNING: No robust strategies found across all batches.")
        exit(0)
    
    robust_winners = pd.concat(all_results, ignore_index=True)
    progress_logger.log_mining_complete(len(robust_winners))
    
    # Save final results
    output_path = os.path.join(config.RESULTS_DIR, config.MINING_RESULTS_FILE)
    robust_winners.to_csv(output_path, index=False)
    print(f"\n✅ MINING COMPLETE: {len(robust_winners)} strategies saved to {output_path}")
