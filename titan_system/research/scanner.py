import logging
import pandas as pd
from titan_system.data.ingest_mt5 import ingest_history
from titan_system.research.data_loader import load_data

logger = logging.getLogger("Titan.Scanner")

class MarketScanner:
    """
    Scans a universe of symbols across multiple timeframes to find the best opportunities.
    """
    def __init__(self, strategy, universe=None, timeframes=None):
        self.strategy = strategy
        self.universe = universe or ["GOLD", "EURUSD", "BTCUSD", "GBPUSD", "USDJPY"]
        # Standardize for MTF analysis
        self.timeframes = ["H4", "H1"]

    def scan(self) -> list:
        """
        Performs the scan and returns a ranked list of opportunities.
        """
        from titan_system.research.auditor import TitanAuditor
        opportunities = []
        logger.info(f"[SCAN] Starting Market Scan across {len(self.universe)} symbols...")

        for raw_symbol in self.universe:
            try:
                # 0. Resolve Broker-Specific Symbol Name
                auditor = TitanAuditor(raw_symbol)
                symbol = auditor.symbol # Resolved name (e.g. BTCUSD or BTCUSD.pro)
                
                # 1. Ensure data for both timeframes
                ingest_history(symbol, "H4", days=40)
                ingest_history(symbol, "H1", days=10)
                
                # 2. Load from DB
                h4_df = load_data(symbol, "H4")
                h1_df = load_data(symbol, "H1")
                
                if h4_df.empty or h1_df.empty or len(h4_df) < 50 or len(h1_df) < 50:
                    logger.warning(f"Insufficient data for {symbol}")
                    continue

                # 3. Local Context (Volatility Check)
                context = self.get_context(h1_df)
                
                # 4. Strategy Analysis
                result = self.strategy.analyze_mtf(symbol, {"H4": h4_df, "H1": h1_df})
                result['context'] = context
                
                opportunities.append(result)

            except Exception as e:
                logger.error(f"Scanner Error for {symbol}: {e}")
                
        # Sort by score (descending)
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities

    def get_context(self, df: pd.DataFrame) -> dict:
        """Calculates current market climate (Volatility speed)."""
        # Calculate ATR (24) for benchmark
        high_low = df['high'] - df['low']
        tr = high_low
        atr = tr.rolling(24).mean().iloc[-2] # Previous candle's 24-bar window
        current_range = tr.iloc[-1] # Most recent candle
        
        speed_ratio = current_range / atr if (atr and atr > 0) else 1.0
        
        climate = "QUIET"
        if speed_ratio > 1.5: climate = "AGGRESSIVE"
        elif speed_ratio > 1.2: climate = "ACTIVE"
        elif speed_ratio < 0.8: climate = "THIN/SLOW"
        
        # ASCII Meter
        meter_val = int(min(speed_ratio, 2.0) * 5)
        meter = "[" + "=" * meter_val + "-" * (10 - meter_val) + "]"
        
        return {
            "speed_ratio": speed_ratio,
            "climate": climate,
            "meter": meter
        }
