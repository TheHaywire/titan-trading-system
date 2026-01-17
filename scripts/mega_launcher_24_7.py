"""
🚀 TITAN MEGA-LAUNCHER (1500+ Symbols)
=====================================
Automated launcher for the high-throughput Async Execution Engine.
No interaction required. Armed with Intelligence Skills.
"""

import asyncio
import logging
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from titan_system.multi_symbol.async_engine import AsyncExecutionEngine
from titan_system.multi_symbol.universe_scanner import UniverseScanner

# Configure logging to be clean but informative
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MegaLauncher")

async def run_mega_trading():
    logger.info("="*60)
    logger.info("TITAN MEGA-UNIVERSE ENGINE: ACTIVATING")
    logger.info("="*60)
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("Capabilities: 1500+ Symbols | Async Scanning | Intelligence Guards")
    
    # Configuration
    RISK_PER_TRADE = 1.0  # 1% risk given the scale
    MAX_POSITIONS = 10    # Allow more concurrent positions at this scale
    SCAN_INTERVAL = 60    # Every minute
    
    # Initialize Engine
    engine = AsyncExecutionEngine(
        max_concurrent=50,
        risk_percent=RISK_PER_TRADE,
        max_positions=MAX_POSITIONS,
        scan_interval=SCAN_INTERVAL
    )
    
    logger.info(f"Engine Initialized: Risk={RISK_PER_TRADE}%, Max Positions={MAX_POSITIONS}")
    logger.info("Status: SEARCHING FOR OPPORTUNITIES...")
    
    try:
        # Start the engine (this runs the internal loop)
        await engine.start(dry_run=False)
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
    except Exception as e:
        logger.error(f"Engine Crash: {e}")
    finally:
        engine.stop()

if __name__ == "__main__":
    try:
        asyncio.run(run_mega_trading())
    except KeyboardInterrupt:
        pass
