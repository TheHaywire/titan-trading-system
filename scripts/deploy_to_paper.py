"""
Deploy Strategy to Paper Trading
================================
Takes a validated strategy from the registry and:
1. Compiles it to executable bot code
2. Updates status to 'paper'
3. Provides instructions for running

Usage:
    python scripts/deploy_to_paper.py <strategy_id>
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.strategy_genome import StrategyGenome
from titan_system.factory.deployment.code_compiler import CodeCompiler


def main():
    parser = argparse.ArgumentParser(description="Deploy strategy to paper trading")
    parser.add_argument('strategy_id', help='Strategy ID to deploy')
    parser.add_argument('--live', action='store_true', help='Deploy to live instead of paper')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("STRATEGY DEPLOYMENT")
    print("=" * 60)
    
    # Load strategy from registry
    registry = StrategyRegistry()
    strategy = registry.get_strategy(args.strategy_id)
    
    if not strategy:
        print(f"\n❌ Strategy {args.strategy_id} not found in registry")
        return
    
    # Parse genome
    try:
        genome_data = json.loads(strategy['genome'])
        genome = StrategyGenome(genome_data)
    except Exception as e:
        print(f"\n❌ Error parsing genome: {e}")
        return
    
    print(f"\nStrategy: {genome.name}")
    print(f"Type: {genome.type}")
    print(f"Symbols: {genome.symbols}")
    print(f"Status: {strategy['status']}")
    
    # Check if strategy is validated
    if strategy['status'] not in ['validated', 'paper']:
        print(f"\n⚠️  Warning: Strategy status is '{strategy['status']}'")
        print("   Only 'validated' strategies should be deployed")
        
        response = input("\nProceed anyway? (y/N): ")
        if response.lower() != 'y':
            print("Deployment cancelled")
            return
    
    # Compile strategy to bot code
    print("\n📝 Compiling strategy to executable bot...")
    compiler = CodeCompiler()
    
    try:
        bot_filepath = compiler.compile_strategy(genome)
        print(f"✅ Bot generated: {bot_filepath}")
    except Exception as e:
        print(f"❌ Compilation failed: {e}")
        return
    
    # Update registry status
    target_status = StrategyRegistry.STATUS_LIVE if args.live else StrategyRegistry.STATUS_PAPER
    registry.update_status(args.strategy_id, target_status)
    
    mode = "LIVE" if args.live else "PAPER"
    print(f"\n✅ Strategy deployed to {mode} trading")
    
    # Print instructions
    print("\n" + "=" * 60)
    print(f"NEXT STEPS - {mode} TRADING")
    print("=" * 60)
    
    if args.live:
        print("\n⚠️  LIVE TRADING MODE")
        print("   This bot will trade with real money!")
        print("\n1. Review the generated bot code:")
        print(f"   {bot_filepath}")
        print("\n2. Start the bot:")
        print(f"   python {bot_filepath}")
        print("\n3. Monitor performance:")
        print(f"   python scripts/monitor_strategy.py {args.strategy_id}")
    else:
        print("\n📊 PAPER TRADING MODE (Simulation)")
        print("   This bot will log trades but NOT execute them")
        print("\n1. Review the generated bot code:")
        print(f"   {bot_filepath}")
        print("\n2. Start paper trading:")
        print(f"   python {bot_filepath}")
        print("\n3. After 2 weeks of paper trading with good results:")
        print(f"   python scripts/deploy_to_paper.py {args.strategy_id} --live")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
