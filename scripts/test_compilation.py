import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json
from titan_system.factory.strategy_genome import StrategyGenome, StrategyTemplates
from titan_system.factory.deployment.code_compiler import CodeCompiler

def test_compilation():
    print("Testing Strategy Compilation with PortfolioManager integration...")
    
    compiler = CodeCompiler()
    
    # Create a test Mean Reversion genome
    genome = StrategyTemplates.rsi_mean_reversion("EURUSD", "M15")
    genome.name = "Portfolio Test Bot"
    
    # Compile
    filepath = compiler.compile_strategy(genome, magic_number=777777)
    
    print(f"✅ Compilation complete: {filepath}")
    
    # Check contents
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "from titan_system.factory.portfolio.portfolio_manager import PortfolioManager" in content:
        print("✅ PASS: PortfolioManager import found.")
    else:
        print("❌ FAIL: PortfolioManager import missing.")
        
    if "pm.calculate_optimal_size" in content:
        print("✅ PASS: Sizing logic uses PortfolioManager.")
    else:
        print("❌ FAIL: Sizing logic uses old fixed risk.")

if __name__ == "__main__":
    test_compilation()
