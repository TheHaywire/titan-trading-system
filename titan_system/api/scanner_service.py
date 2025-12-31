import asyncio
import logging
import pandas as pd
import MetaTrader5 as mt5
import time
from typing import List, AsyncGenerator
from titan_system.smc.institutional_engine import InstitutionalEngine

logger = logging.getLogger("Titan.ScannerService")

class ScannerService:
    def __init__(self, execution_client=None):
        self.engine = InstitutionalEngine()
        self.execution = execution_client 
        self.last_scan_time = {}

    async def get_all_symbols(self) -> List[str]:
        """Fetch all visible Symbols from MT5 Market Watch"""
        loop = asyncio.get_running_loop()
        def fetch_universes():
            symbols = mt5.symbols_get(group="*") # Get all? Be careful with thousands.
            # Let's filter for active ones or just visible in Market Watch for speed
            visible_symbols = mt5.symbols_get(visible=True)
            if not visible_symbols:
                return ["EURUSD"] # Fallback
            return [s.name for s in visible_symbols]
        
        return await loop.run_in_executor(None, fetch_universes)

    async def gather_data(self, symbol: str) -> pd.DataFrame:
        """Async wrapper for MT5 data fetching"""
        # Throttling to prevent DDOSing MT5
        loop = asyncio.get_running_loop()
        def fetch():
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
            if rates is None or len(rates) == 0:
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            return df
            
        return await loop.run_in_executor(None, fetch)

    async def scan_stream(self, symbols: List[str] = None) -> AsyncGenerator[dict, None]:
        """
        Universal Scanner: Scans ALL visible symbols in parallel chunks.
        """
        if not symbols:
            symbols = await self.get_all_symbols()
            logger.info(f"Loaded {len(symbols)} symbols for Universal Scan")

        # Process in chunks of 5 to manage asyncio overhead + MT5 locks
        chunk_size = 5
        
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            tasks = []
            
            for symbol in chunk:
                tasks.append(self.process_symbol(symbol))
            
            # Run chunk concurrently
            results = await asyncio.gather(*tasks)
            
            # Yield valid results
            for res in results:
                if res:
                    yield res
            
            # Small yield/sleep to prevent freezing the event loop completely
            await asyncio.sleep(0.05)

    async def process_symbol(self, symbol: str):
        try:
            df = await self.gather_data(symbol)
            if df is None: return None
            
            # CPU Bound Analysis
            analysis = self.engine.analyze_symbol(df, symbol)
            
            setups = analysis.get('setup', [])
            regime = analysis.get('regime', 'UNDEFINED')
            
            # Filtering: Only stream interesting stuff to save bandwidth?
            # Or stream everything for the 'table fill' effect.
            # Let's stream everything but prioritize setups.
            
            score = 0
            if setups: score += 50
            if regime == "TREND_STRONG": score += 20
            
            return {
                "symbol": symbol,
                "price": float(df['close'].iloc[-1]),
                "trend": analysis.get('trend', {}).get('bias', 'NEUTRAL'),
                "regime": regime,
                "setups": [s['name'] for s in setups],
                "score": score
            }
        except Exception:
            return None
