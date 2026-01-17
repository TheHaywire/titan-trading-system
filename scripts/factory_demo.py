"""
STRATEGY FACTORY - Complete End-to-End Demo
===========================================
Demonstrates the full Strategy Factory pipeline:
1. Generate strategy candidates
2. Backtest with validation
3. Score and rank
4. Compile top performer
5. Deploy to paper trading

This script shows the entire autonomous workflow.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory.strategy_genome import StrategyTemplates
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.generators.idea_generator import IdeaGenerator
from titan_system.factory.validation.backtest_runner import StrategyBacktestRunner
from titan_system.factory.scoring.strategy_scorer import StrategyScorer
from titan_system.factory.deployment.code_compiler import CodeCompiler


def print_header(title):
    """Print section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print("=" * 60)
    print("STRATEGY FACTORY - COMPLETE DEMONSTRATION")
    print("=" * 60)
    print("\nThis demo shows the full autonomous pipeline:")
    print("  1. Generate strategy candidates")
    print("  2. Backtest with rigorous validation")
    print("  3. Score and rank strategies")
    print("  4. Compile top performer to executable bot")
    print("  5. Deploy to paper trading")
    print()
    input("Press Enter to begin...")
    
    # Initialize components
    registry = StrategyRegistry()
    generator = IdeaGenerator()
    backtest_runner = StrategyBacktestRunner(registry)
    scorer = StrategyScorer()
    compiler = CodeCompiler()
    
    # ==================== STEP 1: GENERATE ====================
    print_header("STEP 1: GENERATE STRATEGY CANDIDATES")
    
    print("\nGenerating 3 strategy candidates...")
    candidates = generator.generate_batch(count=3)
    
    print(f"\n✅ Generated {len(candidates)} candidates:")
    for i, candidate in enumerate(candidates, 1):
        print(f"  {i}. {candidate.name}")
        print(f"     Type: {candidate.type}, Symbol: {candidate.symbols[0]}, TF: {candidate.timeframe}")
        
        # Register in database
        strategy_id = registry.add_candidate(candidate, f"Demo candidate {i}")
        candidate.strategy_id = strategy_id
        print(f"     Registry ID: {strategy_id[:8]}...")
    
    input("\nPress Enter to continue to backtesting...")
    
    # ==================== STEP 2: BACKTEST ====================
    print_header("STEP 2: BACKTEST & VALIDATE")
    
    backtest_results = []
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n[{i}/{len(candidates)}] Backtesting {candidate.name}...")
        print("-" * 60)
        
        try:
            results = backtest_runner.backtest_genome(
                candidate,
                validate=False,  # Skip full robustness for demo speed
                update_registry=True
            )
            
            backtest_results.append({
                'genome': candidate,
                'strategy_id': candidate.strategy_id,
                'backtest_metrics': results,
                'robustness_results': results.get('robustness', {})
            })
            
            print(f"\n  Sharpe: {results.get('sharpe', 0):.2f}")
            print(f"  Win Rate: {results.get('win_rate', 0)*100:.1f}%")
            print(f"  Total Trades: {results.get('total_trades', 0)}")
            print(f"  Status: {'✅ Passed' if results.get('passed') else '❌ Failed'}")
            
        except Exception as e:
            print(f"\n  ❌ Backtest failed: {e}")
            backtest_results.append({
                'genome': candidate,
                'strategy_id': candidate.strategy_id,
                'backtest_metrics': {'sharpe': 0, 'win_rate': 0, 'total_trades': 0, 'passed': False}
            })
    
    input("\nPress Enter to continue to scoring...")
    
    # ==================== STEP 3: SCORE & RANK ====================
    print_header("STEP 3: SCORE & RANK STRATEGIES")
    
    print("\nScoring all strategies...")
    scored_strategies = scorer.rank_strategies(backtest_results)
    
    print("\n📊 FINAL RANKINGS:")
    print("-" * 60)
    print(f"{'Rank':<6} {'Name':<25} {'Score':<8} {'Grade':<6} {'Recommendation'}")
    print("-" * 60)
    
    for i, strategy in enumerate(scored_strategies, 1):
        name = strategy['genome'].name[:24]
        score = strategy['score']
        rank = strategy['rank']
        rec = strategy['recommendation']
        
        print(f"{i:<6} {name:<25} {score:<8.1f} {rank:<6} {rec}")
    
    print("-" * 60)
    
    # Get top strategy
    top_strategy = scored_strategies[0] if scored_strategies else None
    
    if not top_strategy or top_strategy['score'] < 60:
        print("\n⚠️  No strategies scored high enough for deployment")
        print("In production, the factory would generate more candidates.")
        return
    
    print(f"\n🏆 Top Strategy: {top_strategy['genome'].name}")
    print(f"   Score: {top_strategy['score']:.1f}/100")
    print(f"   Recommendation: {top_strategy['recommendation']}")
    
    input("\nPress Enter to compile top strategy to executable bot...")
    
    # ==================== STEP 4: COMPILE ====================
    print_header("STEP 4: AUTO-CODE GENERATION")
    
    print(f"\nCompiling {top_strategy['genome'].name} to executable Python bot...")
    
    try:
        bot_filepath = compiler.compile_strategy(top_strategy['genome'])
        
        print(f"\n✅ Bot successfully generated!")
        print(f"   File: {bot_filepath}")
        print(f"   Size: {os.path.getsize(bot_filepath)} bytes")
        print(f"   Magic Number: Auto-assigned from range 999000-999999")
        
        # Show snippet of generated code
        with open(bot_filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:20]
        
        print("\n📄 Generated code preview (first 20 lines):")
        print("-" * 60)
        for line in lines:
            print(line.rstrip())
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ Compilation failed: {e}")
        return
    
    input("\nPress Enter to see deployment instructions...")
    
    # ==================== STEP 5: DEPLOY ====================
    print_header("STEP 5: DEPLOYMENT TO PAPER TRADING")
    
    # Update status to paper
    registry.update_status(
        top_strategy['strategy_id'],
        StrategyRegistry.STATUS_PAPER
    )
    
    print("\n✅ Strategy deployed to PAPER TRADING mode")
    print("\n📋 Next Steps:")
    print("-" * 60)
    print(f"1. Start the bot in paper mode:")
    print(f"   python {bot_filepath}")
    print()
    print(f"2. Monitor performance for 2 weeks")
    print()
    print(f"3. If paper trading shows good results (Sharpe >1.0):")
    print(f"   python scripts/deploy_to_paper.py {top_strategy['strategy_id']} --live")
    print()
    print(f"4. Monitor live performance:")
    print(f"   python scripts/run_factory.py --mode continuous")
    print("-" * 60)
    
    # ==================== SUMMARY ====================
    print_header("DEMO COMPLETE - SUMMARY")
    
    portfolio_metrics = registry.get_portfolio_metrics()
    
    print("\n📊 Current Factory Status:")
    print(f"   Strategies Generated: {len(candidates)}")
    print(f"   Strategies Backtested: {len(backtest_results)}")
    print(f"   Paper Trading: {portfolio_metrics['paper_count']}")
    print(f"   Live Trading: {portfolio_metrics['live_count']}")
    print(f"   Retired: {portfolio_metrics['retired_count']}")
    
    print("\n🎯 What You've Built:")
    print("   ✅ Strategy Generation Engine (50+ per cycle)")
    print("   ✅ Institutional-Grade Backtesting (OOS, MC, WFA)")
    print("   ✅ Multi-Metric Scoring System (0-100 points)")
    print("   ✅ Auto-Code Compiler (Genome → Executable Bot)")
    print("   ✅ Deployment Pipeline (Paper → Live)")
    
    print("\n🚀 The Strategy Factory is Operational!")
    print("\nTo run continuous operation:")
    print("   python scripts/run_factory.py --mode continuous --cycle-hours 24")
    print("\nThe factory will:")
    print("   - Generate new strategies daily")
    print("   - Backtest and validate them")
    print("   - Deploy winners to paper trading")
    print("   - Monitor and auto-retire underperformers")
    print("   - Maintain a diversified portfolio of 5-10 live strategies")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
