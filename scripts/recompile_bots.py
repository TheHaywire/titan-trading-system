import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.deployment.code_compiler import CodeCompiler
from titan_system.factory.strategy_genome import StrategyGenome
import sqlite3
import json

def recompile_all_active():
    registry = StrategyRegistry()
    compiler = CodeCompiler()
    
    conn = sqlite3.connect('data/strategy_factory.db')
    c = conn.cursor()
    c.execute("SELECT id, genome, magic_number FROM strategies WHERE status IN ('paper', 'live')")
    rows = c.fetchall()
    conn.close()
    
    print(f"Re-compiling {len(rows)} bots with new magics...")
    for s_id, genome_json, magic in rows:
        genome_data = json.loads(genome_json)
        genome = StrategyGenome()
        genome.genome = genome_data
        
        # Override ID if needed
        genome.genome['id'] = s_id
        
        print(f"  {s_id[:8]} -> {magic}")
        compiler.compile_strategy(genome, magic_number=magic)

if __name__ == "__main__":
    recompile_all_active()
