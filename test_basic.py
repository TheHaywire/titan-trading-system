"""
Minimal test script to verify system components work individually.
"""
import sys
import os
sys.path.append(os.getcwd())

print("=" * 50)
print("TITAN SYSTEM - BASIC VERIFICATION")
print("=" * 50)

# Test 1: MT5 Connection
print("\n[1/4] Testing MT5 Connection...")
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        print("✅ MT5 Connected")
        print(f"   Version: {mt5.version()}")
        mt5.shutdown()
    else:
        print(f"❌ MT5 Failed: {mt5.last_error()}")
except Exception as e:
    print(f"❌ MT5 Error: {e}")

# Test 2: Database
print("\n[2/4] Testing Database...")
try:
    from titan_system.db.database import Database
    db = Database("titan_system/titan.db")
    print("✅ Database Initialized")
except Exception as e:
    print(f"❌ Database Error: {e}")

# Test 3: Config
print("\n[3/4] Testing Config...")
try:
    from config.settings import settings
    print(f"✅ Config Loaded")
    print(f"   Account: {settings.mt5_login}")
except Exception as e:
    print(f"❌ Config Error: {e}")

# Test 4: Polars
print("\n[4/4] Testing Polars...")
try:
    import polars as pl
    print("✅ Polars Available")
except Exception as e:
    print(f"❌ Polars Error: {e}")

print("\n" + "=" * 50)
print("Verification Complete!")
print("=" * 50)
