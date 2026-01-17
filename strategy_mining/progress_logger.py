"""
Progress Logger for Batch Mining Operations
Provides live commentary and detailed tracking for multi-hour mining sessions.
"""

import logging
from datetime import datetime
import os
import strategy_mining.mining_config as config

class ProgressLogger:
    def __init__(self, log_file="mining_progress.log"):
        self.log_file = os.path.join(config.LOGS_DIR, log_file)
        self.batch_start_time = None
        self.total_start_time = datetime.now()
        
        # Setup dual logging (file + console)
        self.logger = logging.getLogger("MiningProgress")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(self.log_file, mode='w')
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def log_mining_start(self, total_symbols, batch_size):
        """Log the start of the full mining operation."""
        total_batches = (total_symbols + batch_size - 1) // batch_size
        self.logger.info("=" * 80)
        self.logger.info("🚀 TITAN MINING ENGINE - FULL SYMBOL BRUTE-FORCE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Symbols: {total_symbols}")
        self.logger.info(f"Batch Size: {batch_size}")
        self.logger.info(f"Total Batches: {total_batches}")
        self.logger.info(f"Estimated Time: {total_batches * 12:.0f}-{total_batches * 15:.0f} minutes")
        self.logger.info("=" * 80)
    
    def log_batch_start(self, batch_num, total_batches, symbols):
        """Log the start of a batch."""
        self.batch_start_time = datetime.now()
        symbol_preview = ', '.join(symbols[:5]) + ('...' if len(symbols) > 5 else '')
        
        self.logger.info("")
        self.logger.info("─" * 80)
        self.logger.info(f"📦 BATCH {batch_num}/{total_batches} | Symbols: {len(symbols)}")
        self.logger.info(f"   Preview: {symbol_preview}")
        self.logger.info("─" * 80)
    
    def log_phase(self, phase_name, details=""):
        """Log a specific phase within a batch."""
        msg = f"  ▸ {phase_name}"
        if details:
            msg += f": {details}"
        self.logger.info(msg)
    
    def log_progress(self, current, total, item_type="items"):
        """Log incremental progress within a phase."""
        pct = (current / total * 100) if total > 0 else 0
        self.logger.info(f"    → {current}/{total} {item_type} complete ({pct:.1f}%)")
    
    def log_batch_complete(self, batch_num, strategies_found, total_strategies):
        """Log the completion of a batch."""
        elapsed = (datetime.now() - self.batch_start_time).total_seconds()
        mins, secs = divmod(int(elapsed), 60)
        
        self.logger.info(f"  ✓ Batch Complete: {strategies_found} robust strategies found")
        self.logger.info(f"  ⏱ Elapsed: {mins}m {secs}s | Total Found: {total_strategies}")
        self.logger.info("─" * 80)
    
    def log_mining_complete(self, total_strategies):
        """Log the completion of the entire mining operation."""
        total_elapsed = (datetime.now() - self.total_start_time).total_seconds()
        hours, remainder = divmod(int(total_elapsed), 3600)
        mins, secs = divmod(remainder, 60)
        
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("🏆 MINING COMPLETE")
        self.logger.info("=" * 80)
        self.logger.info(f"Total Robust Strategies Found: {total_strategies}")
        self.logger.info(f"Total Time: {hours}h {mins}m {secs}s")
        self.logger.info("=" * 80)
    
    def log_error(self, batch_num, error_msg):
        """Log errors during batch processing."""
        self.logger.error(f"❌ BATCH {batch_num} ERROR: {error_msg}")
