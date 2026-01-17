import json
import logging
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.deployment.code_compiler import CodeCompiler
from titan_system.factory.strategy_genome import StrategyGenome

logging.basicConfig(level=logging.INFO, format='%(asctime)s [DEPLOIER] %(message)s')
logger = logging.getLogger("ManualDeploy")

def deploy_validated():
    registry = StrategyRegistry()
    compiler = CodeCompiler()
    
    validated = registry.get_strategies_by_status('validated')
    logger.info(f"Found {len(validated)} validated strategies pending deployment.")
    
    for v in validated:
        try:
            genome = StrategyGenome(json.loads(v['genome']))
            logger.info(f"Deploying {v['id'][:8]} ({genome.symbols[0]}) to paper...")
            
            bot_path, magic = compiler.compile_strategy(genome)
            registry.update_status(v['id'], 'paper', updates={'magic_number': magic})
            logger.info(f"✅ DEPLOYED: {v['id'][:8]} | Magic: {magic}")
            
        except Exception as e:
            logger.error(f"Failed to deploy {v['id'][:8]}: {e}")

if __name__ == "__main__":
    deploy_validated()
