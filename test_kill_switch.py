"""
Kill Switch Test Suite
Demonstrates and tests all 3 tiers of emergency stops
"""

import sys
import os
sys.path.append(os.getcwd())

from titan_system.risk.kill_switch import KillSwitch
import MetaTrader5 as mt5

def test_kill_switch():
    """Test all kill switch functions"""
    
    print("="*60)
    print("KILL SWITCH DEMONSTRATION")
    print("="*60)
    
    #Initialize MT5
    if not mt5.initialize():
        print("❌ MT5 not initialized. Tests will be limited.")
    
    # Create kill switch
    ks = KillSwitch()
    
    # Test 1: Check status
    print("\n1. Initial Status:")
    status = ks.get_status()
    print(f"   Global Enabled: {status['global_enabled']}")
    print(f"   Account Active: {status['account_active']}")
    print(f"   Blacklisted: {status['blacklisted_symbols']}")
    
    # Test 2: Symbol blacklist
    print("\n2. Testing Symbol Blacklist...")
    result = ks.trigger_symbol("GBPUSD", "Test: Excessive slippage")
    print(f"   Result: {result}")
    
    can_trade, reason = ks.can_trade("GBPUSD")
    print(f"   Can trade GBPUSD? {can_trade} ({reason})")
    
    can_trade, reason = ks.can_trade("EURUSD")
    print(f"   Can trade EURUSD? {can_trade} ({reason})")
    
    # Test 3: Account pause
    print("\n3. Testing Account Pause...")
    result = ks.trigger_account("Test: Temporary pause")
    print(f"   Result: {result}")
    
    can_trade, reason = ks.can_trade("EURUSD")
    print(f"   Can trade after pause? {can_trade} ({reason})")
    
    # Resume
    ks.reset_account()
    can_trade, reason = ks.can_trade("EURUSD")
    print(f"   Can trade after resume? {can_trade} (GBPUSD still blocked: {reason})")
    
    # Test 4: Global kill (DANGEROUS - will close positions!)
    print("\n4. Global K Switch (DEMO - NOT TRIGGERED)")
    print("   Would close ALL positions and block ALL trading")
    print("   To trigger: ks.trigger_global('Emergency reason')")
    print("   To reset: ks.reset_global('TITAN_RESET_GLOBAL')")
    
    # Test 5: Remove blacklist
    print("\n5. Removing GBPUSD from blacklist...")
    ks.remove_symbol_blacklist("GBPUSD")
    can_trade, reason = ks.can_trade("GBPUSD")
    print(f"   Can trade GBPUSD now? {can_trade}")
    
    print("\n" + "="*60)
    print("✅ KILL SWITCH TESTS COMPLETE")
    print("="*60)
    
    print("\n📋 Kill Switch Status:")
    final_status = ks.get_status()
    for key, value in final_status.items():
        print(f"   {key}: {value}")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_kill_switch()
