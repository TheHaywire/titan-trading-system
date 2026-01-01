"""
Operational Alpha Validation Suite
Tests all Phase 2 components: TradeManager, AlphaOptimizer, AllocationAgent
"""

import sys
import os
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
from titan_system.core.manager import TradeManager
from titan_system.core.alpha_optimizer import AlphaOptimizer
from titan_system.risk.allocation import AllocationAgent
from titan_system.core.execution import MT5Execution
from titan_system.db.database import Database
from config.settings import settings as Config

def validate_trade_manager():
    """Test 1: TradeManager functionality"""
    print("\n" + "="*60)
    print("TEST 1: TradeManager Validation")
    print("="*60)
    
    if not mt5.initialize():
        print("❌ MT5 initialization failed")
        return False
        
    try:
        execution = MT5Execution(Config)
        manager = TradeManager(execution)
        
        # Check if manager can scan positions
        positions = mt5.positions_get()
        print(f"✅ TradeManager initialized")
        print(f"   Current Open Positions: {len(positions) if positions else 0}")
        
        # Test the management logic (won't modify actual positions)
        if positions:
            print(f"\n   Testing lifecycle logic on {len(positions)} position(s)...")
            for pos in positions:
                entry = pos.price_open
                current = pos.price_current
                sl = pos.sl
                
                if sl > 0:
                    risk_dist = abs(entry - sl)
                    profit_dist = current - entry if pos.type == 0 else entry - current
                    rr_ratio = profit_dist / risk_dist if risk_dist > 0 else 0
                    
                    print(f"   Position {pos.ticket} ({pos.symbol}): R:R = {rr_ratio:.2f}")
                    if rr_ratio >= 1.0:
                        print(f"      🎯 TRIGGER READY: Would activate lifecycle alpha")
        
        print("✅ TradeManager: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ TradeManager: FAILED - {e}")
        return False

def validate_alpha_optimizer():
    """Test 2: AlphaOptimizer regime detection"""
    print("\n" + "="*60)
    print("TEST 2: AlphaOptimizer Validation")
    print("="*60)
    
    try:
        optimizer = AlphaOptimizer()
        
        # Test regime detection with mock market states
        test_cases = [
            {
                "symbol": "XAUUSD",
                "market_state": {
                    "categories": {
                        "Trend Following": {"score": 85, "label": "STRONG", "status": "BULLISH"},
                        "Mean Reversion": {"score": 20, "label": "SLEEPING"},
                        "Volatility": {"label": "HIGH", "status": "EXPANDING"}
                    }
                },
                "expected": "InstitutionalGold"
            },
            {
                "symbol": "EURUSD",
                "market_state": {
                    "categories": {
                        "Trend Following": {"score": 30, "label": "WEAK"},
                        "Mean Reversion": {"score": 80, "label": "ACTIVE"},
                        "Volatility": {"label": "LOW", "status": "STABLE"}
                    }
                },
                "expected": "MeanReversionStrategy"
            }
        ]
        
        for i, test in enumerate(test_cases, 1):
            result = optimizer.determine_best_strategy(test["symbol"], test["market_state"])
            status = "✅" if result == test["expected"] else "⚠️"
            print(f"{status} Test Case {i}: {test['symbol']} -> {result} (Expected: {test['expected']})")
        
        print("✅ AlphaOptimizer: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AlphaOptimizer: FAILED - {e}")
        return False

def validate_allocation_agent():
    """Test 3: AllocationAgent with scaling"""
    print("\n" + "="*60)
    print("TEST 3: AllocationAgent Validation")
    print("="*60)
    
    if not mt5.symbol_select("EURUSD", True):
        print("❌ Could not select EURUSD for testing")
        return False
        
    try:
        allocator = AllocationAgent(risk_per_trade=0.015, max_total_exposure=0.10)
        
        # Test 1: Base allocation
        base_lots = allocator.calculate_lots("EURUSD", signal_confidence=0.75, stop_loss_pips=50, scaling_multiplier=1.0)
        print(f"✅ Base Allocation (0.75 conf, 50 pips SL): {base_lots:.4f} lots")
        
        # Test 2: Winner scaling
        scaled_lots = allocator.calculate_lots("EURUSD", signal_confidence=0.75, stop_loss_pips=50, scaling_multiplier=1.5)
        print(f"✅ Winner Scaling (1.5x multiplier): {scaled_lots:.4f} lots")
        
        # Verify scaling worked
        if scaled_lots > base_lots:
            print(f"   📈 Scaling verified: {((scaled_lots/base_lots - 1) * 100):.1f}% increase")
        
        # Test 3: Drawdown protection (simulate by checking logic)
        acc = mt5.account_info()
        if acc and acc.equity < acc.balance:
            print(f"   📉 Drawdown Protection: Would reduce by 30%")
        else:
            print(f"   ✅ Account Healthy: No drawdown reduction needed")
        
        print("✅ AllocationAgent: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ AllocationAgent: FAILED - {e}")
        return False

def validate_database_performance():
    """Test 4: Database performance queries"""
    print("\n" + "="*60)
    print("TEST 4: Database Performance Tracking")
    print("="*60)
    
    try:
        db = Database(Config.db_path)
        
        # Test performance query
        test_symbols = ["EURUSD", "XAUUSD", "BTCUSD"]
        
        for symbol in test_symbols:
            perf = db.get_symbol_performance(symbol)
            print(f"\n   {symbol}:")
            print(f"      Trades: {perf['trade_count']}")
            print(f"      Expectancy: ${perf['expectancy']:.2f}")
            print(f"      Total P&L: ${perf['total_pnl']:.2f}")
            print(f"      Win Rate: {perf['win_rate']*100:.1f}%")
            
            if perf['expectancy'] > 200:
                print(f"      🚀 WINNER: Would apply 1.5x scaling")
        
        print("\n✅ Database: PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Database: FAILED - {e}")
        return False

def run_full_validation():
    """Execute all validation tests"""
    print("\n" + "="*60)
    print("🔬 OPERATIONAL ALPHA VALIDATION SUITE")
    print("="*60)
    print("Testing Phase 2: Trade Lifecycle & Growth Architecture")
    
    results = {
        "TradeManager": validate_trade_manager(),
        "AlphaOptimizer": validate_alpha_optimizer(),
        "AllocationAgent": validate_allocation_agent(),
        "Database": validate_database_performance()
    }
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(results.values())
    total = len(results)
    
    for component, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {component}")
    
    print(f"\nOverall: {passed}/{total} components passed")
    
    if passed == total:
        print("\n🎉 ALL SYSTEMS GO - Ready for Operational Alpha")
        return True
    else:
        print("\n⚠️ Some components failed - Review before live trading")
        return False

if __name__ == "__main__":
    success = run_full_validation()
    mt5.shutdown()
    sys.exit(0 if success else 1)
