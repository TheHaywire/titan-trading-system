
import asyncio
import logging
from titan_system.core.engine import TitanEngine
from titan_system.analytics.sessions import SessionManager
import sys

# Configure basic logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

async def test_engine_cycle():
    print("=== Testing Titan Engine Cycle with Session Awareness ===")
    
    engine = TitanEngine()
    
    # 1. Test Session Manager
    print("\n1. Checking Session Status...")
    status_api = engine.get_status()
    session = status_api['session']
    print(f"   Current UTC Time: {session['utc_time']}")
    print(f"   Active Sessions: {session['active_sessions']}")
    print(f"   Liquidity Tier: {session['liquidity_tier']}")
    print(f"   Recommended: {session['recommended_symbols']}")
    
    # 2. Simulate Engine Start (Mock Connection)
    # Since we might not have MT5 terminal active in this environment, 
    # the engine.execution.connect() might fail or need mocking.
    # For this test, we just want to see if the structure holds up.
    
    print("\n2. Initializing Engine...")
    # We can't really run engine.start() because it loops forever.
    # We will try running one analysis cycle if possible, but that requires MT5 connection.
    # If MT5 is not present, it will log errors but shouldn't crash.
    
    print("   Engine initialized.")
    if engine.execution.connect():
        print("   MT5 Connect Success (Mock/Real).")
    else:
        print("   MT5 Connect failed (Expected if no terminal).")

    # 3. Check Strategies
    print("\n3. Loaded Strategies:")
    for s in engine.strategies:
        print(f"   - {s.name}")

    print("\n✅ Engine Structure Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_engine_cycle())
