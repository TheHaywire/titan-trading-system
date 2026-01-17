"""
TEST: Intelligent Skills Demo
=============================
Simulates market scenarios and shows how Titan's new 'Skills' react.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from titan_system.skills.registry import SkillRegistry

async def run_demo():
    registry = SkillRegistry()
    print("="*60)
    print("TITAN INTELLIGENCE SKILLS DEMO")
    print("="*60)

    # SECNARIO 1: Normal Market
    print("\n[SCENARIO 1] Normal Market (EURUSD Buy)")
    context_normal = {
        'symbol': 'EURUSD',
        'direction': 'BUY',
        'open_positions': []
    }
    result_1 = await registry.evaluate_all(context_normal)
    print(f"Status: {result_1['status']} | Adjustment: {result_1['adjustment']}")
    print(f"Outcome: System proceeds with standard analysis.")

    # SCENARIO 2: Correlation Risk
    print("\n[SCENARIO 2] Correlation Risk (USDCAD Sell while heavy on USD-Shorts)")
    # Already long EURUSD, GBPUSD, AUDUSD -> Short USD by 3 points
    # Proposed Sell USDCAD -> Sell USD, Buy CAD -> Short USD by 1 more point (Total 4)
    context_corr = {
        'symbol': 'USDCAD',
        'direction': 'SELL',
        'open_positions': ['EURUSD', 'GBPUSD', 'AUDUSD'] # Assume all are BUYs
    }
    result_2 = await registry.evaluate_all(context_corr)
    print(f"Status: {result_2['status']} | Adjustment: {result_2['adjustment']}")
    for r in result_2['reasons']:
        print(f"  • {r}")

    # SCENARIO 3: News Detection (Requires MT5 initialization to run properly)
    print("\n[SCENARIO 3] News Guardian (Live Check)")
    import MetaTrader5 as mt5
    if mt5.initialize():
        context_news = {'symbol': 'GOLD', 'direction': 'BUY'}
        result_3 = await registry.evaluate_all(context_news)
        print(f"Status: {result_3['status']} | Adjustment: {result_3['adjustment']}")
        if result_3['reasons']:
            for r in result_3['reasons']:
                print(f"  • {r}")
        else:
            print("  • Gold volatility is currently normal.")
        mt5.shutdown()
    else:
        print("  • Skipping live news check (MT5 initialization failed)")

    print("\n" + "="*60)
    print("Intelligence Phase 1 Complete.")

if __name__ == "__main__":
    asyncio.run(run_demo())
