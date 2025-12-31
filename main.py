import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from titan_system.core.engine import TitanEngine

async def main():
    print("="*50)
    print("   TITAN TRADING SYSTEM - SIMPLE MODE")
    print("="*50)
    print("1. Connecting to Market...")
    
    engine = TitanEngine()
    
    print("2. Engine Started. Press Ctrl+C to stop.")
    print("-" * 50)
    
    # Run the main loop
    while True:
        await engine.tick()
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping Titan...")
