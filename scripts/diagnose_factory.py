"""
Strategy Factory System Diagnostic
==================================
Tests all components and identifies issues.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test if all modules can be imported."""
    print("=" * 60)
    print("TEST 1: MODULE IMPORTS")
    print("=" * 60)
    
    try:
        from titan_system.factory.strategy_genome import StrategyGenome
        print("✅ StrategyGenome")
    except Exception as e:
        print(f"❌ StrategyGenome: {e}")
        return False
    
    try:
        from titan_system.factory.strategy_registry import StrategyRegistry
        print("✅ StrategyRegistry")
    except Exception as e:
        print(f"❌ StrategyRegistry: {e}")
        return False
    
    try:
        from titan_system.factory.generators.idea_generator import IdeaGenerator
        print("✅ IdeaGenerator")
    except Exception as e:
        print(f"❌ IdeaGenerator: {e}")
        return False
    
    try:
        from titan_system.factory.validation.backtest_runner import StrategyBacktestRunner
        print("✅ BacktestRunner")
    except Exception as e:
        print(f"❌ BacktestRunner: {e}")
        return False
    
    try:
        from titan_system.factory.scoring.strategy_scorer import StrategyScorer
        print("✅ StrategyScorer")
    except Exception as e:
        print(f"❌ StrategyScorer: {e}")
        return False
    
    try:
        from titan_system.factory.deployment.code_compiler import CodeCompiler
        print("✅ CodeCompiler")
    except Exception as e:
        print(f"❌ CodeCompiler: {e}")
        return False
    
    print("\n✅ All modules imported successfully\n")
    return True


def test_database():
    """Test database connectivity."""
    print("=" * 60)
    print("TEST 2: DATABASE")
    print("=" * 60)
    
    try:
        from titan_system.factory.strategy_registry import StrategyRegistry
        registry = StrategyRegistry()
        metrics = registry.get_portfolio_metrics()
        
        print(f"✅ Database connected")
        print(f"   Total strategies: {metrics['total_strategies']}")
        print(f"   Live: {metrics['live_count']}")
        print(f"   Paper: {metrics['paper_count']}")
        print(f"   Retired: {metrics['retired_count']}")
        print()
        return True
    except Exception as e:
        print(f"❌ Database error: {e}\n")
        return False


def test_generation():
    """Test strategy generation."""
    print("=" * 60)
    print("TEST 3: STRATEGY GENERATION")
    print("=" * 60)
    
    try:
        from titan_system.factory.generators.idea_generator import IdeaGenerator
        
        generator = IdeaGenerator()
        candidates = generator.generate_batch(count=3)
        
        print(f"✅ Generated {len(candidates)} strategies:")
        for i, c in enumerate(candidates, 1):
            print(f"   {i}. {c.name}")
            print(f"      Type: {c.type}, Symbol: {c.symbols[0]}, TF: {c.timeframe}")
        print()
        return True
    except Exception as e:
        print(f"❌ Generation error: {e}\n")
        return False


def test_mt5():
    """Test MT5 connectivity and data."""
    print("=" * 60)
    print("TEST 4: MT5 CONNECTION & DATA")
    print("=" * 60)
    
    try:
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            print("❌ MT5 not connected")
            print("   Is MetaTrader 5 running?")
            return False
        
        print("✅ MT5 connected")
        
        account = mt5.account_info()
        if account:
            print(f"   Account: {account.login}")
            print(f"   Balance: ${account.balance:.2f}")
        
        # Test symbols
        test_symbols = ['GOLD', 'SILVER', 'EURUSD', 'GBPUSD']
        print("\n   Symbol availability:")
        available = 0
        for symbol in test_symbols:
            info = mt5.symbol_info(symbol)
            if info:
                print(f"   ✅ {symbol}: Available")
                available += 1
            else:
                print(f"   ❌ {symbol}: Not found")
        
        mt5.shutdown()
        
        print(f"\n   {available}/{len(test_symbols)} symbols available")
        
        if available < 2:
            print("   ⚠️ Warning: Limited symbol availability")
            print("   Add symbols in MT5 Market Watch")
            return False
        
        print()
        return True
        
    except Exception as e:
        print(f"❌ MT5 error: {e}\n")
        return False


def test_scoring():
    """Test strategy scoring."""
    print("=" * 60)
    print("TEST 5: STRATEGY SCORING")
    print("=" * 60)
    
    try:
        from titan_system.factory.scoring.strategy_scorer import StrategyScorer
        
        scorer = StrategyScorer()
        
        # Test with dummy metrics
        test_metrics = {
            'sharpe': 1.5,
            'calmar': 2.0,
            'win_rate': 0.55,
            'profit_factor': 2.2,
            'total_trades': 120
        }
        
        result = scorer.score_strategy(test_metrics)
        
        print(f"✅ Scoring system working")
        print(f"   Test Score: {result['total_score']:.1f}/100")
        print(f"   Rank: {result['rank']}")
        print(f"   Recommendation: {result['recommendation']}")
        print()
        return True
        
    except Exception as e:
        print(f"❌ Scoring error: {e}\n")
        return False


def test_compilation():
    """Test code compilation."""
    print("=" * 60)
    print("TEST 6: CODE COMPILATION")
    print("=" * 60)
    
    try:
        from titan_system.factory.strategy_genome import StrategyTemplates
        from titan_system.factory.deployment.code_compiler import CodeCompiler
        
        genome = StrategyTemplates.rsi_mean_reversion("GOLD", "H1")
        compiler = CodeCompiler()
        
        filepath = compiler.compile_strategy(genome)
        
        # Check if file exists
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ Code compilation working")
            print(f"   Generated: {os.path.basename(filepath)}")
            print(f"   Size: {file_size} bytes")
            print()
            return True
        else:
            print(f"❌ File not created: {filepath}\n")
            return False
            
    except Exception as e:
        print(f"❌ Compilation error: {e}\n")
        return False


def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 60)
    print("STRATEGY FACTORY SYSTEM DIAGNOSTIC")
    print("=" * 60)
    print()
    
    results = {
        'Imports': test_imports(),
        'Database': test_database(),
        'Generation': test_generation(),
        'MT5 Connection': test_mt5(),
        'Scoring': test_scoring(),
        'Compilation': test_compilation()
    }
    
    # Summary
    print("=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASSED" if passed_test else "❌ FAILED"
        print(f"{test_name:<20} {status}")
    
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS OPERATIONAL")
        print("The Strategy Factory is ready to run!")
        print("\nNext step:")
        print("  python scripts/run_factory.py --mode single")
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Please review the errors above and fix the issues.")
    
    print()


if __name__ == "__main__":
    main()
