"""
Opening Range Breakout (ORB) Strategy
=====================================
Institutional trend-following strategy based on the first M15 candle of the session.

Logic:
1. Calculate the High/Low of the M15 Opening Range (first 15-min candle)
2. Calculate VWAP (Volume Weighted Average Price)
3. BUY Signal: Price > ORB_High AND Price > VWAP
4. SELL Signal: Price < ORB_Low AND Price < VWAP

Features:
- Session-aware (London/NY opens)
- VWAP confirmation reduces false breakouts
- ATR-based dynamic stop losses
- Vectorbt-compatible for backtesting
"""

import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import logging
from typing import Dict, Optional, List, Any
from datetime import datetime, time, timedelta
from dataclasses import dataclass
import sys
import os

sys.path.append(os.getcwd())

from titan_system.strategies.base import BaseStrategy

logger = logging.getLogger("Titan.MultiSymbol.ORB")


@dataclass
class SessionConfig:
    """Trading session configuration."""
    name: str
    start_hour: int  # UTC
    start_minute: int
    duration_hours: int


# Major session open times (UTC)
SESSIONS = {
    'london': SessionConfig('London', 8, 0, 8),
    'newyork': SessionConfig('New York', 13, 0, 8),
    'tokyo': SessionConfig('Tokyo', 0, 0, 8),
    'sydney': SessionConfig('Sydney', 22, 0, 8),
}


class ORBStrategy(BaseStrategy):
    """
    Opening Range Breakout Strategy
    
    A trend-following strategy that trades breakouts from the first
    M15 candle of a trading session, confirmed by VWAP.
    
    Parameters:
        session (str): Which session to use ('london', 'newyork', 'auto')
        orb_timeframe (int): Timeframe for ORB calculation (default M15)
        vwap_confirmation (bool): Require VWAP confirmation
        atr_stop_multiplier (float): SL = ATR * multiplier
        risk_reward (float): Target R:R ratio
    
    Usage:
        orb = ORBStrategy({'session': 'london', 'risk_reward': 2.0})
        signal = orb.analyze('EURUSD', df)
    """
    
    def __init__(self, config: Dict = None):
        config = config or {}
        super().__init__("ORB_Breakout", config)
        
        self.session = config.get('session', 'auto')
        self.orb_timeframe = config.get('orb_timeframe', mt5.TIMEFRAME_M15)
        self.vwap_confirmation = config.get('vwap_confirmation', True)
        self.atr_stop_multiplier = config.get('atr_stop_multiplier', 1.5)
        self.risk_reward = config.get('risk_reward', 2.0)
        self.atr_period = config.get('atr_period', 14)
        
    def get_current_session(self) -> Optional[SessionConfig]:
        """
        Determine the current active trading session based on UTC time.
        Always returns a valid session for better reliability.
        """
        now = datetime.utcnow()
        current_hour = now.hour
        
        # Check for active sessions
        for name, session in SESSIONS.items():
            session_start = session.start_hour
            session_end = (session.start_hour + session.duration_hours) % 24
            
            # Handle session that crosses midnight
            if session_end < session_start:
                if current_hour >= session_start or current_hour < session_end:
                    return session
            else:
                if session_start <= current_hour < session_end:
                    return session
        
        # Fallback: Return the most recently started session
        # This ensures ORB still works outside typical hours
        best_session = None
        min_distance = 24
        
        for name, session in SESSIONS.items():
            # Calculate how many hours since this session started
            hours_since_start = (current_hour - session.start_hour) % 24
            if hours_since_start < min_distance:
                min_distance = hours_since_start
                best_session = session
        
        return best_session if best_session else SESSIONS['london']
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculate Volume Weighted Average Price (VWAP).
        
        VWAP = Σ(Typical Price * Volume) / Σ(Volume)
        Typical Price = (High + Low + Close) / 3
        
        Args:
            df: DataFrame with 'high', 'low', 'close', 'tick_volume' columns
            
        Returns:
            Series with cumulative VWAP values
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # Use tick_volume if real_volume not available
        volume = df.get('real_volume', df.get('tick_volume', 1))
        
        # Cumulative VWAP
        cum_vol = volume.cumsum()
        cum_vol_price = (typical_price * volume).cumsum()
        
        vwap = cum_vol_price / cum_vol
        return vwap
    
    def calculate_atr(self, df: pd.DataFrame, period: int = None) -> float:
        """Calculate Average True Range."""
        period = period or self.atr_period
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1] if not atr.empty else 0
    
    def get_opening_range(self, df: pd.DataFrame, session: SessionConfig = None) -> Optional[Dict]:
        """
        Get the Opening Range (first M15 candle of the session).
        
        Args:
            df: DataFrame with datetime index or 'time' column
            session: Session configuration to use
            
        Returns:
            Dict with {'high': float, 'low': float, 'time': datetime} or None
        """
        if session is None:
            session = self.get_current_session()
            if session is None:
                return None
        
        # Ensure we have datetime
        if 'time' in df.columns:
            df = df.copy()
            if not pd.api.types.is_datetime64_any_dtype(df['time']):
                df['time'] = pd.to_datetime(df['time'], unit='s')
            df = df.set_index('time')
        
        # Find today's session start
        now = datetime.utcnow()
        session_start = now.replace(
            hour=session.start_hour, 
            minute=session.start_minute, 
            second=0, 
            microsecond=0
        )
        
        # If it's before session start, use yesterday's session
        if now < session_start:
            session_start -= timedelta(days=1)
        
        # Find the first M15 bar after session start
        session_bars = df[df.index >= session_start]
        
        if session_bars.empty:
            return None
        
        first_bar = session_bars.iloc[0]
        
        return {
            'high': first_bar['high'],
            'low': first_bar['low'],
            'time': session_bars.index[0],
            'session': session.name
        }
    
    def analyze(self, symbol: str, df: pd.DataFrame) -> Optional[Dict[str, Any]]:
        """
        Analyze dataframe for ORB breakout signals.
        
        Args:
            symbol: Trading symbol
            df: DataFrame with OHLCV data (M15 timeframe recommended)
            
        Returns:
            Signal dictionary or None
            {
                "signal": "BUY" | "SELL",
                "setup": "ORB_BREAKOUT_BULL" | "ORB_BREAKOUT_BEAR",
                "entry": float,
                "stop_loss": float,
                "take_profit": float,
                "confidence": float,
                "metadata": {...}
            }
        """
        if df is None or df.empty or len(df) < 20:
            return None
        
        # Get session config
        if self.session == 'auto':
            session = self.get_current_session()
        else:
            session = SESSIONS.get(self.session)
        
        if session is None:
            return None
        
        # Get Opening Range
        orb = self.get_opening_range(df, session)
        if orb is None:
            logger.debug(f"{symbol}: No ORB found for {session.name} session")
            return None
        
        # Calculate VWAP
        df = df.copy()
        df['vwap'] = self.calculate_vwap(df)
        
        # Calculate ATR
        atr = self.calculate_atr(df)
        if atr == 0:
            return None
        
        # Current price
        current = df.iloc[-1]
        current_price = current['close']
        current_vwap = current['vwap']
        
        orb_high = orb['high']
        orb_low = orb['low']
        orb_range = orb_high - orb_low
        
        signal = None
        
        # ====== BULLISH BREAKOUT ======
        # Price > ORB High AND Price > VWAP
        if current_price > orb_high:
            if not self.vwap_confirmation or current_price > current_vwap:
                stop_loss = orb_low - (atr * 0.5)  # Below ORB low
                risk = current_price - stop_loss
                take_profit = current_price + (risk * self.risk_reward)
                
                signal = {
                    "signal": "BUY",
                    "setup": "ORB_BREAKOUT_BULL",
                    "entry": current_price,
                    "stop_loss": round(stop_loss, 5),
                    "take_profit": round(take_profit, 5),
                    "confidence": self._calculate_confidence(current_price, orb, current_vwap, atr),
                    "metadata": {
                        "orb_high": orb_high,
                        "orb_low": orb_low,
                        "orb_range": orb_range,
                        "vwap": current_vwap,
                        "atr": atr,
                        "session": session.name,
                        "breakout_size": current_price - orb_high,
                        "breakout_atr_ratio": (current_price - orb_high) / atr
                    }
                }
        
        # ====== BEARISH BREAKOUT ======
        # Price < ORB Low AND Price < VWAP
        elif current_price < orb_low:
            if not self.vwap_confirmation or current_price < current_vwap:
                stop_loss = orb_high + (atr * 0.5)  # Above ORB high
                risk = stop_loss - current_price
                take_profit = current_price - (risk * self.risk_reward)
                
                signal = {
                    "signal": "SELL",
                    "setup": "ORB_BREAKOUT_BEAR",
                    "entry": current_price,
                    "stop_loss": round(stop_loss, 5),
                    "take_profit": round(take_profit, 5),
                    "confidence": self._calculate_confidence(current_price, orb, current_vwap, atr),
                    "metadata": {
                        "orb_high": orb_high,
                        "orb_low": orb_low,
                        "orb_range": orb_range,
                        "vwap": current_vwap,
                        "atr": atr,
                        "session": session.name,
                        "breakout_size": orb_low - current_price,
                        "breakout_atr_ratio": (orb_low - current_price) / atr
                    }
                }
        
        if signal:
            logger.info(f"ORB Signal: {symbol} {signal['signal']} @ {signal['entry']:.5f} "
                       f"(SL: {signal['stop_loss']:.5f}, TP: {signal['take_profit']:.5f})")
        
        return signal
    
    def _calculate_confidence(self, price: float, orb: Dict, vwap: float, atr: float) -> float:
        """
        Calculate signal confidence based on multiple factors.
        
        Factors:
        - Breakout size relative to ATR
        - VWAP alignment
        - ORB range relative to ATR
        """
        confidence = 0.5  # Base confidence
        
        orb_high = orb['high']
        orb_low = orb['low']
        orb_range = orb_high - orb_low
        
        # Factor 1: Breakout size (bigger = more confident)
        if price > orb_high:
            breakout_size = (price - orb_high) / atr
        else:
            breakout_size = (orb_low - price) / atr
        
        if breakout_size > 0.5:
            confidence += 0.15
        elif breakout_size > 0.3:
            confidence += 0.10
        
        # Factor 2: VWAP alignment
        if price > orb_high and price > vwap:
            confidence += 0.15
        elif price < orb_low and price < vwap:
            confidence += 0.15
        
        # Factor 3: ORB range (tighter = better breakout potential)
        orb_atr_ratio = orb_range / atr
        if orb_atr_ratio < 0.5:  # Tight range
            confidence += 0.10
        elif orb_atr_ratio < 1.0:
            confidence += 0.05
        
        return min(0.95, confidence)
    
    def analyze_bulk(self, data_dict: Dict[str, pd.DataFrame]) -> Dict[str, Optional[Dict]]:
        """
        Analyze multiple symbols in bulk (vectorized where possible).
        
        Args:
            data_dict: Dictionary mapping symbol -> DataFrame
            
        Returns:
            Dictionary mapping symbol -> signal (or None)
        """
        results = {}
        
        for symbol, df in data_dict.items():
            try:
                results[symbol] = self.analyze(symbol, df)
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {e}")
                results[symbol] = None
        
        return results


# Quick test
if __name__ == "__main__":
    import MetaTrader5 as mt5
    
    logging.basicConfig(level=logging.INFO)
    
    if not mt5.initialize():
        print("MT5 init failed")
        exit()
    
    # Fetch M15 data for EURUSD
    rates = mt5.copy_rates_from_pos("EURUSD", mt5.TIMEFRAME_M15, 0, 100)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Test strategy
    orb = ORBStrategy({'session': 'auto', 'vwap_confirmation': True})
    
    print(f"Current Session: {orb.get_current_session()}")
    print(f"Opening Range: {orb.get_opening_range(df)}")
    
    signal = orb.analyze("EURUSD", df)
    print(f"Signal: {signal}")
    
    mt5.shutdown()
