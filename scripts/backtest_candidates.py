"""
Backtest All Candidate Strategies
=================================
Processes all candidate strategies in the registry, backtests them,
and updates their status based on results.

Usage:
    python scripts/backtest_candidates.py
    python scripts/backtest_candidates.py --validate  # With robustness tests
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import json
from titan_system.factory.strategy_registry import StrategyRegistry
from titan_system.factory.strategy_genome import StrategyGenome
from titan_system.factory.validation.backtest_runner import StrategyBacktestRunner


def main():
    parser = argparse.ArgumentParser(description="Backtest all candidate strategies")
    parser.add_argument('--validate', action='store_true',
                        help='Run full robustness validation (slower)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of strategies to test')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("BACKTESTING CANDIDATE STRATEGIES")
    print("=" * 60)
    
    # Initialize
    registry = StrategyRegistry()
    runner = StrategyBacktestRunner(registry)
    
    # Get all candidates
    candidates = registry.get_strategies_by_status('candidate')
    
    if len(candidates) == 0:
        print("\n❌ No candidate strategies to backtest")
        print("💡 Run: python scripts/run_factory.py --mode single")
        return
    
    print(f"\nFound {len(candidates)} candidate strategies")
    
    if args.limit:
        candidates = candidates[:args.limit]
        print(f"Testing first {len(candidates)} strategies")
    
    # Backtest each
    results_summary = []
    
    for i, candidate in enumerate(candidates, 1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(candidates)}] Processing {candidate['id'][:8]}...")
        print(f"{'=' * 60}")
        
        try:
            # Parse genome
            genome_data = json.loads(candidate['genome'])
            genome = StrategyGenome(genome_data)
            
            # Run backtest
            results = runner.backtest_genome(
                genome,
                validate=args.validate,
                update_registry=True
            )
            
            results_summary.append({
                'id': candidate['id'][:8],
                'name': genome.name,
                'sharpe': results.get('sharpe', 0),
                'win_rate': results.get('win_rate', 0),
                'trades': results.get('total_trades', 0),
                'passed': results.get('passed', False)
            })
            
        except Exception as e:
            print(f"❌ Error: {e}")
            results_summary.append({
                'id': candidate['id'][:8],
                'name': 'ERROR',
                'sharpe': 0,
                'win_rate': 0,
                'trades': 0,
                'passed': False
            })
    
    # Print summary
    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    print(f"{'ID':<10} {'Sharpe':<8} {'Win%':<8} {'Trades':<8} {'Result'}")
    print("-" * 60)
    
    passed_count = 0
    for r in results_summary:
        result_icon = "✅" if r['passed'] else "❌"
        print(f"{r['id']:<10} {r['sharpe']:<8.2f} {r['win_rate']*100:<8.1f} {r['trades']:<8} {result_icon}")
        if r['passed']:
            passed_count += 1
    
    print("=" * 60)
    print(f"PASSED: {passed_count}/{len(results_summary)}")
    print("=" * 60)
    
    # Show what to do next
    if passed_count > 0:
        print("\n✅ Next steps:")
        print("   1. Check validated strategies:")
        print("      python -c \"from titan_system.factory.strategy_registry import StrategyRegistry; r = StrategyRegistry(); [print(s['id'], s['bt_sharpe']) for s in r.get_strategies_by_status('validated')]\"")
        print("   2. Deploy to paper trading:")
        print("      python scripts/deploy_to_paper.py <strategy_id>")


if __name__ == "__main__":
    main()
