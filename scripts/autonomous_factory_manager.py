"""
AUTONOMOUS FACTORY MANAGER
==========================
This script manages the entire Strategy Factory pipeline:
1. Generation of new ideas
2. Systematic backtesting & validation
3. Automated scoring and selection
4. Auto-compilation and deployment to paper trading

Designed to run for extended periods for deep strategy discovery.
"""

import sys, os
import time
import json
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory.strategy_factory import StrategyFactory
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.strategy_genome import StrategyGenome
from titan_system.factory.validation.backtest_runner import StrategyBacktestRunner
from titan_system.factory.validation.gatekeeper import StrategyGatekeeper
from titan_system.factory.deployment.code_compiler import CodeCompiler

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [AUTO-FACTORY] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AutonomousFactory")

def run_step_1_generation(factory):
    """Run generation cycle."""
    logger.info("--- STEP 1: GENERATION ---")
    factory.run_cycle()

def run_step_2_backtesting(registry, runner, gatekeeper):
    """Backtest all pending candidates."""
    logger.info("--- STEP 2: BACKTESTING & VALIDATION ---")
    candidates = registry.get_strategies_by_status('candidate')
    
    if not candidates:
        logger.info("No candidates to backtest.")
        return
    
    logger.info(f"Processing {len(candidates)} candidates...")
    
    for c in candidates:
        try:
            genome_data = json.loads(c['genome'])
            genome = StrategyGenome(genome_data)
            symbol = genome.symbols[0] if genome.symbols else "UNKNOWN"
            
            logger.info(f"Backtesting {genome.name} ({c['id'][:8]})...")
            # Stage 1: Standard Backtest & Robustness
            results = runner.backtest_genome(genome, validate=True, update_registry=True)
            
            if results.get('passed'):
                logger.info(f"✅ Stage 1 Clear: {c['id'][:8]} PASSED basic validation.")
                
                # APPLY HARSHER FILTERS (Council Audit #2)
                # 1. Spread-to-Profit Buffer (Avg Trade must be > 0.01%)
                if results.get('avg_trade_pct', 0) < 0.01:
                    logger.info(f"⚠️  Rejected {c['id'][:8]}: Profit margin too thin ({results.get('avg_trade_pct'):.4f}%)")
                    registry.update_status(c['id'], 'rejected')
                    continue
                
                # Stage 2: Gatekeeper (Heuristic + ML)
                passed_gk, gk_details = gatekeeper.validate(genome_data, results)
                logger.info(f"Gatekeeper Audit: {gk_details}")
                
                if passed_gk:
                    logger.info(f"🏆 Strategy {c['id'][:8]} PASSED Gatekeeper!")
                    registry.update_status(c['id'], 'validated')
                    
                    # STREAM-DEPLOYMENT (Immediate promotion to paper if slots available)
                    paper_slots = registry.get_paper_strategies()
                    if len(paper_slots) < 25: # New cap from supercharged config
                         logger.info(f"🚀 STREAM-DEPLOYING {c['id'][:8]} to paper immediately...")
                         try:
                             # Compile and deploy
                             bot_path, magic_number = compiler.compile_strategy(genome)
                             registry.update_status(c['id'], 'paper', updates={'magic_number': magic_number})
                             logger.info(f"✅ Successfully deployed {c['id'][:8]} as Magic {magic_number}")
                         except Exception as deploy_err:
                             logger.error(f"Failed to deploy {c['id'][:8]}: {deploy_err}")
                    else:
                         logger.info(f"⏸  Paper fleet full ({len(paper_slots)}). Staying in 'validated' queue.")
                else:
                    logger.info(f"⛔ Strategy {c['id'][:8]} REJECTED by Gatekeeper.")
                    registry.update_status(c['id'], 'rejected')
            else:
                logger.info(f"❌ Strategy {c['id'][:8]} FAILED Stage 1 validation.")
                
        except Exception as e:
            logger.error(f"Error backtesting {c['id'][:8]}: {e}")

def run_step_3_deployment(registry, compiler):
    """Auto-deploy validated strategies to paper trading."""
    logger.info("--- STEP 3: AUTO-DEPLOYMENT ---")
    validated = registry.get_strategies_by_status('validated')
    
    if not validated:
        logger.info("No validated strategies ready for deployment.")
        return
    
    for v in validated:
        try:
            genome_data = json.loads(v['genome'])
            genome = StrategyGenome(genome_data)
            
            logger.info(f"Deploying {genome.name} ({v['id'][:8]}) to paper...")
            
            # Compile to bot
            bot_path, magic_number = compiler.compile_strategy(genome)
            
            # Update status and magic number
            registry.update_magic_number(v['id'], magic_number)
            registry.update_status(v['id'], registry.STATUS_PAPER)
            
            logger.info(f"✅ DEPLOYED: {genome.name} (Magic: {magic_number}) -> {bot_path}")
            
        except Exception as e:
            logger.error(f"Error deploying {v['id'][:8]}: {e}")

def main():
    logger.info("=" * 60)
    logger.info("STRATEGY FACTORY - STARTING AUTONOMOUS EXECUTION")
    logger.info("=" * 60)
    
    factory = StrategyFactory()
    registry = StrategyRegistry()
    runner = StrategyBacktestRunner(registry)
    gatekeeper = StrategyGatekeeper()
    compiler = CodeCompiler()
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            logger.info(f"\n🚀 STARTING AUTONOMOUS CYCLE #{cycle_count}")
            
            # Step 1: Generate candidates
            run_step_1_generation(factory)
            
            # Step 2: Backtest and validate (with Gatekeeper)
            run_step_2_backtesting(registry, runner, gatekeeper)
            
            # Step 3: Deploy winners
            run_step_3_deployment(registry, compiler)
            
            # Step 4: Summary
            metrics = registry.get_portfolio_metrics()
            logger.info("\n" + "=" * 40)
            logger.info("SYSTEM STATUS SUMMARY")
            logger.info("=" * 40)
            logger.info(f"Total strategies: {metrics['total_strategies']}")
            logger.info(f"Paper strategies: {metrics['paper_count']}")
            logger.info(f"Live strategies:  {metrics['live_count']}")
            logger.info(f"Avg Sharpe:       {metrics['avg_sharpe']:.2f}")
            logger.info("=" * 40)
            
            # Sleep between cycles (5 minutes for testing, normally much longer)
            wait_time = 300 
            logger.info(f"Cycle #{cycle_count} complete. Waiting {wait_time}s for next cycle...")
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        logger.info("Autonomous execution stopped by user.")
    except Exception as e:
        logger.error(f"Fatal error in autonomous execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
