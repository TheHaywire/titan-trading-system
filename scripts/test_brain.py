
import asyncio
import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from titan_system.analytics.market_state import MarketAnalyzer
from titan_system.core.execution import MT5Execution
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TestBrain")

async def test_brain():
    logger.info("🧠 Testing Titan Analytical Engine...")
    
    # Init execution wrapper
    execution = MT5Execution(settings)
    if not execution.connect():
        logger.error("Failed to connect to MT5")
        return

    brain = MarketAnalyzer(execution)
    symbol = settings.trading_symbols[0] 
    
    logger.info(f"🔎 Analyzing {symbol}...")
    
    report = await brain.analyze_symbol(symbol)
    
    if report:
        print("\n" + "="*40)
        print(f" TITAN INTELLIGENCE REPORT: {report['symbol']}")
        print("="*40)
        print(f"SCORE: {report['score']}/100")
        print(f"BIAS:  {report['bias']}")
        print("-" * 20)
        print("REASONING:")
        for reason in report['reasoning']:
            print(f" • {reason}")
        print("-" * 20)
        print("TIMEFRAMES:")
        for tf, state in report['timeframes'].items():
            print(f" [{tf}] Trend: {state['trend']} | Mom: {state['momentum']}")
        print("="*40 + "\n")
    else:
        logger.error("Analysis Failed (No Data?)")

    execution.shutdown()

if __name__ == "__main__":
    asyncio.run(test_brain())
