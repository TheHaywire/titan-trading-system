
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_system.analytics.sessions import SessionManager
import datetime

def test_sessions():
    print("=== Session Manager Test ===")
    
    # 1. Test Current Time
    status = SessionManager.get_market_status()
    print(f"Current UTC Time: {status['utc_time']}")
    print(f"Active Sessions: {status['active_sessions']}")
    print(f"Liquidity Tier: {status['liquidity_tier']}")
    print(f"Recommended Symbols: {status['recommended_symbols']}")
    print("-" * 30)

    # 2. Test Specific Time (London Open - 09:00 UTC)
    london_time = datetime.datetime(2025, 12, 12, 9, 0, 0)
    status_london = SessionManager.get_market_status(london_time)
    print(f"Simulating 09:00 UTC (London Open):")
    print(f"Active Sessions: {status_london['active_sessions']}")
    assert "LONDON" in status_london['active_sessions']
    print("✅ London detection passed")

    # 3. Test Specific Time (NY/London Overlap - 14:00 UTC)
    overlap_time = datetime.datetime(2025, 12, 12, 14, 0, 0)
    status_overlap = SessionManager.get_market_status(overlap_time)
    print(f"\nSimulating 14:00 UTC (Overlap):")
    print(f"Active Sessions: {status_overlap['active_sessions']}")
    print(f"Liquidity: {status_overlap['liquidity_tier']}")
    assert len(status_overlap['active_sessions']) >= 2
    print("✅ Overlap detection passed")

if __name__ == "__main__":
    test_sessions()
