"""
ALPHA BURST - High-Intensity Strategy discovery
================================================
Bypasses standard factory throttles to flood the registry with high-quality candidates.
"""

import sys, os
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory.strategy_factory import StrategyFactory
from titan_system.factory.generators.idea_generator import IdeaGenerator
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.validation.backtest_runner import StrategyBacktestRunner
from titan_system.factory.validation.gatekeeper import StrategyGatekeeper
from titan_system.factory.deployment.code_compiler import CodeCompiler
from titan_system.factory import factory_config as cfg

# Override config for intensity
cfg.MAX_CANDIDATES_PER_CYCLE = 250
cfg.MAX_PAPER_STRATEGIES = 50

logging.basicConfig(level=logging.INFO, format='%(asctime)s [BURST] %(message)s')
logger = logging.getLogger("AlphaBurst")

def main():
    logger.info("🔥 STARTING ALPHA BURST DISCOVERY...")
    
    factory = StrategyFactory()
    registry = StrategyRegistry()
    runner = StrategyBacktestRunner(registry)
    gatekeeper = StrategyGatekeeper()
    compiler = CodeCompiler()
    
    # 1. Generate massive batch
    logger.info("🧬 Step 1: Performing Real-World Data Recon & Batch Generation...")
    # Initialize with registry to enable Bayesian/Real-world data lookup
    factory.idea_generator = IdeaGenerator(registry_db=cfg.STRATEGY_DB)
    candidates = factory.idea_generator.generate_batch(count=250)
    
    new_ids = []
    for c in candidates:
        s_id = registry.add_candidate(c, notes="Alpha Burst Seed")
        new_ids.append((s_id, c))
    
    logger.info(f"✅ Registered {len(new_ids)} candidates.")
    
    # 2. Parallel Backtest
    logger.info("🧪 Step 2: Running High-Speed Validation Pipeline...")
    passed_count = 0
    for s_id, genome in new_ids:
        try:
            # Run quick backtest
            result = runner.backtest_genome(genome, validate=True, update_registry=True)
            
            if result.get('passed'):
                logger.info(f"  ✨ {genome.name} PASSED (Sharpe: {result.get('sharpe', 0):.2f})")
                passed_count += 1
                
                # Auto-deploy if it passed
                bot_path, magic = compiler.compile_strategy(genome)
                registry.update_magic_number(s_id, magic)
                registry.update_status(s_id, 'paper')
                logger.info(f"  🚀 DEPLOYED -> {bot_path}")
        except Exception as e:
            continue

    logger.info("=" * 60)
    logger.info(f"🏁 BURST COMPLETE: {passed_count} new strategies deployed to paper trading.")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
