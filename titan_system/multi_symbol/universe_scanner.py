"""
Universe Scanner - Multi-Symbol Data Layer
==========================================
Retrieves all MT5 symbols and filters for high-liquidity "Active Symbols"
using Relative Volume (RVOL) and Average True Range (ATR).

Designed to handle 1,500+ symbols efficiently using:
- Polars for vectorized calculations
- ThreadPoolExecutor for parallel symbol processing
- Caching to minimize MT5 API calls
"""

import MetaTrader5 as mt5
import pandas as pd
import polars as pl
import numpy as np
import logging
from typing import List, Dict, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger("Titan.MultiSymbol.Scanner")


@dataclass
class ActiveSymbol:
    """Represents a symbol that passed liquidity filters."""
    symbol: str
    rvol: float           # Relative Volume ratio
    atr: float            # Average True Range
    atr_percent: float    # ATR as % of price
    last_price: float
    spread: float         # In points
    volume_min: float     # Minimum lot size
    volume_step: float    # Lot increment
    category: str         # forex, commodity, index, crypto


class UniverseScanner:
    """
    Multi-Symbol Universe Scanner
    
    Features:
    - Retrieves all tradeable symbols from MT5
    - Calculates RVOL (Relative Volume) for liquidity detection
    - Calculates ATR for volatility assessment
    - Filters for "Active Symbols" where Volume > 2.0 * AvgVolume
    
    Usage:
        scanner = UniverseScanner()
        active = scanner.scan_universe(min_rvol=2.0)
        print(f"Found {len(active)} active symbols")
    """
    
    def __init__(self, max_workers: int = 20):
        """
        Initialize the scanner.
        
        Args:
            max_workers: Number of parallel threads for symbol processing
        """
        self.max_workers = max_workers
        self._symbol_cache = {}
        self._last_cache_time = 0
        self._cache_ttl = 300  # 5 minutes
        
    def connect(self) -> bool:
        """Ensure MT5 connection is established."""
        if not mt5.initialize():
            logger.error(f"MT5 initialization failed: {mt5.last_error()}")
            return False
        return True
    
    def get_all_symbols(self, include_disabled: bool = False) -> List[str]:
        """
        Retrieve all symbols from MT5 using mt5.symbols_get().
        
        Args:
            include_disabled: Include symbols not visible in Market Watch
            
        Returns:
            List of symbol names
        """
        if not self.connect():
            return []
        
        symbols = mt5.symbols_get()
        if symbols is None:
            logger.error(f"Failed to get symbols: {mt5.last_error()}")
            return []
        
        result = []
        for sym in symbols:
            # Filter out synthetics/derived instruments
            if sym.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED and not include_disabled:
                continue
            # Only include tradeable symbols
            if sym.trade_mode in [mt5.SYMBOL_TRADE_MODE_FULL, mt5.SYMBOL_TRADE_MODE_LONGONLY, 
                                   mt5.SYMBOL_TRADE_MODE_SHORTONLY, mt5.SYMBOL_TRADE_MODE_CLOSEONLY]:
                result.append(sym.name)
        
        logger.info(f"Retrieved {len(result)} tradeable symbols from MT5")
        return result
    
    def categorize_symbol(self, symbol: str) -> str:
        """Categorize symbol type for analysis grouping."""
        symbol_upper = symbol.upper()
        
        # Crypto
        if any(crypto in symbol_upper for crypto in ['BTC', 'ETH', 'XRP', 'LTC', 'DOGE', 'SOL', 'ADA']):
            return 'crypto'
        
        # Commodities
        if any(comm in symbol_upper for comm in ['XAU', 'GOLD', 'XAG', 'SILVER', 'OIL', 'WTI', 
                                                   'BRENT', 'NATGAS', 'COPPER', 'PLATINUM']):
            return 'commodity'
        
        # Indices
        if any(idx in symbol_upper for idx in ['US30', 'US500', 'US100', 'NAS', 'SPX', 'DAX', 
                                                 'FTSE', 'NIK', 'DJ30', 'SP500', 'NDX']):
            return 'index'
        
        # Forex (default)
        return 'forex'
    
    def calculate_rvol(self, symbol: str, lookback: int = 20) -> Optional[float]:
        """
        Calculate Relative Volume (RVOL).
        
        RVOL = Current Volume / Average Volume (lookback period)
        
        Args:
            symbol: MT5 symbol name
            lookback: Number of bars for average volume calculation
            
        Returns:
            RVOL ratio (>2.0 indicates high liquidity) or None on error
        """
        try:
            # Fetch M15 bars for volume analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, lookback + 5)
            if rates is None or len(rates) < lookback:
                return None
            
            df = pl.from_pandas(pd.DataFrame(rates))
            volumes = df['tick_volume'].to_list()
            
            # Use most recent completed bars only (exclude currently forming bar)
            # Get the last N completed bars for average
            completed_volumes = volumes[:-1]  # Exclude current bar
            
            if len(completed_volumes) < lookback:
                return None
            
            # Current bar's volume (the one just before the forming bar)
            current_volume = completed_volumes[-1]
            
            # Average of previous bars (excluding the current one we're comparing)
            historical_volumes = completed_volumes[-(lookback+1):-1]
            
            if len(historical_volumes) == 0:
                return None
            
            avg_volume = sum(historical_volumes) / len(historical_volumes)
            
            if avg_volume == 0 or avg_volume is None:
                return None
            
            rvol = current_volume / avg_volume
            return round(rvol, 2)
            
        except Exception as e:
            logger.debug(f"RVOL calculation failed for {symbol}: {e}")
            return None
    
    def calculate_atr(self, symbol: str, period: int = 14) -> Optional[Tuple[float, float]]:
        """
        Calculate Average True Range (ATR).
        
        Args:
            symbol: MT5 symbol name
            period: ATR period (default 14)
            
        Returns:
            Tuple of (ATR value, ATR as percentage of price) or None on error
        """
        try:
            # Fetch H1 bars for ATR (more stable)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, period + 10)
            if rates is None or len(rates) < period:
                return None
            
            df = pl.from_pandas(pd.DataFrame(rates))
            
            # True Range calculation using Polars
            tr1 = df['high'] - df['low']
            tr2 = (df['high'] - df['close'].shift(1)).abs()
            tr3 = (df['low'] - df['close'].shift(1)).abs()
            
            # Stack and get max for each row
            df = df.with_columns([
                pl.max_horizontal([tr1, tr2, tr3]).alias('tr')
            ])
            
            # ATR = SMA of True Range
            atr = df['tr'].tail(period).mean()
            last_price = df['close'][-1]
            
            if last_price == 0:
                return None
            
            atr_percent = (atr / last_price) * 100
            
            return (round(atr, 5), round(atr_percent, 2))
            
        except Exception as e:
            logger.debug(f"ATR calculation failed for {symbol}: {e}")
            return None
    
    def _process_single_symbol(self, symbol: str, min_rvol: float) -> Optional[ActiveSymbol]:
        """
        Process a single symbol (designed for parallel execution).
        
        Args:
            symbol: Symbol name
            min_rvol: Minimum RVOL threshold
            
        Returns:
            ActiveSymbol if passes filters, None otherwise
        """
        try:
            # Get symbol info
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
            
            # Skip if spread is unreasonably high (illiquid)
            if info.spread > 200:  # More than 200 points spread
                return None
            
            # Calculate RVOL
            rvol = self.calculate_rvol(symbol)
            if rvol is None or rvol < min_rvol:
                return None
            
            # Calculate ATR
            atr_result = self.calculate_atr(symbol)
            if atr_result is None:
                return None
            
            atr, atr_percent = atr_result
            
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            
            last_price = (tick.bid + tick.ask) / 2
            
            return ActiveSymbol(
                symbol=symbol,
                rvol=rvol,
                atr=atr,
                atr_percent=atr_percent,
                last_price=last_price,
                spread=info.spread,
                volume_min=info.volume_min,
                volume_step=info.volume_step,
                category=self.categorize_symbol(symbol)
            )
            
        except Exception as e:
            logger.debug(f"Error processing {symbol}: {e}")
            return None
    
    def scan_universe(self, min_rvol: float = 2.0, max_symbols: int = None) -> List[ActiveSymbol]:
        """
        Main scanner: Find all Active Symbols with high liquidity.
        
        Filter criteria:
        - Volume > 2.0 * Average Volume (RVOL > 2.0)
        - Spread < 200 points
        - Valid price data available
        
        Args:
            min_rvol: Minimum Relative Volume threshold (default 2.0)
            max_symbols: Optional limit on symbols to scan (for testing)
            
        Returns:
            List of ActiveSymbol objects that passed all filters
        """
        start_time = time.time()
        
        if not self.connect():
            return []
        
        # Get all symbols
        all_symbols = self.get_all_symbols()
        if max_symbols:
            all_symbols = all_symbols[:max_symbols]
        
        logger.info(f"Scanning {len(all_symbols)} symbols for RVOL > {min_rvol}...")
        
        active_symbols = []
        processed = 0
        
        # Parallel processing with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self._process_single_symbol, sym, min_rvol): sym 
                for sym in all_symbols
            }
            
            for future in as_completed(futures):
                processed += 1
                result = future.result()
                
                if result is not None:
                    active_symbols.append(result)
                
                # Progress logging every 100 symbols
                if processed % 100 == 0:
                    logger.info(f"Progress: {processed}/{len(all_symbols)} symbols processed...")
        
        # Sort by RVOL descending (highest liquidity first)
        active_symbols.sort(key=lambda x: x.rvol, reverse=True)
        
        elapsed = time.time() - start_time
        logger.info(f"Scan complete: {len(active_symbols)} active symbols found in {elapsed:.1f}s")
        
        # Log top 10 by category
        for category in ['forex', 'commodity', 'index', 'crypto']:
            cat_symbols = [s for s in active_symbols if s.category == category]
            if cat_symbols:
                top = cat_symbols[:3]
                names = ", ".join([f"{s.symbol}({s.rvol}x)" for s in top])
                logger.info(f"  {category.upper()}: {len(cat_symbols)} found - Top: {names}")
        
        return active_symbols
    
    def get_symbol_data(self, symbol: str, timeframe: int = mt5.TIMEFRAME_M15, 
                        bars: int = 200) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data for a symbol.
        
        Args:
            symbol: MT5 symbol name
            timeframe: MT5 timeframe constant
            bars: Number of bars to fetch
            
        Returns:
            DataFrame with OHLCV data or None
        """
        if not self.connect():
            return None
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def get_bulk_data(self, symbols: List[str], timeframe: int = mt5.TIMEFRAME_M15,
                      bars: int = 200) -> Dict[str, pd.DataFrame]:
        """
        Fetch OHLCV data for multiple symbols in parallel.
        
        Args:
            symbols: List of symbol names
            timeframe: MT5 timeframe constant
            bars: Number of bars per symbol
            
        Returns:
            Dictionary mapping symbol -> DataFrame
        """
        result = {}
        
        def fetch_one(sym):
            return sym, self.get_symbol_data(sym, timeframe, bars)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(fetch_one, sym) for sym in symbols]
            
            for future in as_completed(futures):
                sym, df = future.result()
                if df is not None:
                    result[sym] = df
        
        return result


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    scanner = UniverseScanner()
    
    # Test with limited symbols first
    active = scanner.scan_universe(min_rvol=1.5, max_symbols=100)
    
    print(f"\n{'='*60}")
    print(f"ACTIVE SYMBOLS (RVOL > 1.5)")
    print(f"{'='*60}")
    
    for sym in active[:20]:
        print(f"{sym.symbol:12} | RVOL: {sym.rvol:5.2f}x | ATR: {sym.atr_percent:5.2f}% | "
              f"Spread: {sym.spread:4} | {sym.category}")
