"""
Macro Strategist Agent
======================
QuantAI Architecture - Context & Bias Agent

Provides higher-timeframe context and market participation gates.
Determines if current conditions are suitable for trading.

Responsibilities:
1. HTF Trend Bias (D1, W1 direction)
2. Session Quality Analysis
3. Inter-market Correlation Check
4. Market Participation Gate
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import MetaTrader5 as mt5
import pandas as pd

logger = logging.getLogger("Titan.MacroStrategist")


# =============================================================================
# DATA STRUCTURES
# =============================================================================

class MarketDirection(Enum):
    """HTF market direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"


class SessionQuality(Enum):
    """Quality of current trading session"""
    PRIME = "PRIME"      # Best conditions - London/NY overlap
    GOOD = "GOOD"        # Active session
    MARGINAL = "MARGINAL"  # Early/late session
    POOR = "POOR"        # Asian for non-JPY, holidays, etc.


@dataclass
class MacroBias:
    """Output of MacroStrategist analysis"""
    direction: str  # BULLISH, BEARISH, NEUTRAL
    session_quality: str  # PRIME, GOOD, MARGINAL, POOR
    htf_trend: str  # UP, DOWN, SIDEWAYS
    correlation_aligned: bool = True
    participation_allowed: bool = True
    score_adjustment: int = 0  # -20 to +20 adjustment to quant score
    reasoning: List[str] = field(default_factory=list)
    
    # Detailed data
    d1_trend: str = "NEUTRAL"
    h4_trend: str = "NEUTRAL"
    current_session: str = "UNKNOWN"
    session_time_remaining: int = 0  # minutes


# =============================================================================
# MACRO STRATEGIST AGENT
# =============================================================================

class MacroStrategist:
    """
    Context & Bias Agent - Provides HTF direction and market participation gates.
    
    Analyzes:
    - D1/H4 trend direction (EMA stack, structure)
    - Session timing and quality
    - Inter-market correlations
    - Market participation conditions
    """
    
    # Session definitions (UTC hours)
    SESSIONS = {
        "ASIAN": {"start": 0, "end": 8, "quality": "MARGINAL"},
        "LONDON": {"start": 8, "end": 12, "quality": "GOOD"},
        "OVERLAP": {"start": 12, "end": 16, "quality": "PRIME"},
        "NEW_YORK": {"start": 16, "end": 21, "quality": "GOOD"},
        "CLOSED": {"start": 21, "end": 24, "quality": "POOR"}
    }
    
    # Symbol session preferences
    SYMBOL_SESSIONS = {
        # JPY pairs best in Asian
        "USDJPY": ["ASIAN", "OVERLAP"],
        "EURJPY": ["ASIAN", "LONDON", "OVERLAP"],
        "GBPJPY": ["LONDON", "OVERLAP"],
        
        # EUR pairs best in London
        "EURUSD": ["LONDON", "OVERLAP"],
        "EURGBP": ["LONDON", "OVERLAP"],
        
        # GBP pairs best in London
        "GBPUSD": ["LONDON", "OVERLAP"],
        
        # USD pairs best in NY
        "USDCAD": ["NEW_YORK", "OVERLAP"],
        "USDCHF": ["LONDON", "OVERLAP", "NEW_YORK"],
        
        # Commodities
        "GOLD": ["LONDON", "OVERLAP", "NEW_YORK"],
        "XAUUSD": ["LONDON", "OVERLAP", "NEW_YORK"],
        "WTI": ["NEW_YORK"],
        
        # Indices
        "US500": ["NEW_YORK"],
        "US30": ["NEW_YORK"],
        "USTEC": ["NEW_YORK"],
        "GER40": ["LONDON", "OVERLAP"],
        
        # Crypto - 24/7 but volume varies
        "BTCUSD": ["OVERLAP", "NEW_YORK"],
        "ETHUSD": ["OVERLAP", "NEW_YORK"]
    }
    
    # Correlation matrix (simplified)
    POSITIVE_CORRELATIONS = {
        "EURUSD": ["GBPUSD", "AUDUSD", "NZDUSD"],
        "GBPUSD": ["EURUSD", "AUDUSD"],
        "USDJPY": ["USDCHF", "USDCAD"],
        "GOLD": ["SILVER", "EURUSD"],  # Gold often inversely correlated with USD
        "BTCUSD": ["ETHUSD", "SOLUSD"]
    }
    
    NEGATIVE_CORRELATIONS = {
        "EURUSD": ["USDCHF", "USDJPY"],
        "GOLD": ["USDJPY"]  # Simplified - both are safe havens but different dynamics
    }
    
    def __init__(self):
        self._bias_cache: Dict[str, Tuple[MacroBias, datetime]] = {}
        self._cache_duration_minutes = 15  # Cache bias for 15 mins
        
    def analyze(self, symbol: str, open_positions: Dict[str, float] = None) -> MacroBias:
        """
        Analyze macro conditions for a symbol.
        
        Args:
            symbol: Symbol to analyze
            open_positions: Dict of symbol -> exposure (positive = long, negative = short)
            
        Returns:
            MacroBias with direction, session quality, and participation gate
        """
        # Check cache
        cached = self._bias_cache.get(symbol)
        if cached:
            bias, cache_time = cached
            if (datetime.now(timezone.utc) - cache_time).total_seconds() < self._cache_duration_minutes * 60:
                return bias
        
        reasoning = []
        score_adjustment = 0
        
        # =====================================================================
        # 1. HTF Trend Analysis
        # =====================================================================
        d1_trend, h4_trend, htf_reasoning = self._analyze_htf_trend(symbol)
        reasoning.extend(htf_reasoning)
        
        # Determine overall direction
        if d1_trend == "UP" and h4_trend == "UP":
            direction = "BULLISH"
            score_adjustment += 10
        elif d1_trend == "DOWN" and h4_trend == "DOWN":
            direction = "BEARISH"
            score_adjustment += 10
        elif d1_trend != h4_trend:
            direction = "NEUTRAL"
            score_adjustment -= 5
            reasoning.append("⚠️ D1/H4 trend divergence")
        else:
            direction = "NEUTRAL"
        
        # =====================================================================
        # 2. Session Analysis
        # =====================================================================
        current_session, session_quality, session_remaining = self._analyze_session(symbol)
        
        if session_quality == "PRIME":
            score_adjustment += 5
            reasoning.append(f"🌟 Prime session: {current_session}")
        elif session_quality == "POOR":
            score_adjustment -= 10
            reasoning.append(f"⚠️ Poor liquidity session: {current_session}")
        else:
            reasoning.append(f"Session: {current_session} ({session_quality})")
        
        # =====================================================================
        # 3. Correlation Check
        # =====================================================================
        correlation_aligned = True
        if open_positions:
            aligned, corr_reasoning = self._check_correlations(symbol, direction, open_positions)
            correlation_aligned = aligned
            if not aligned:
                score_adjustment -= 10
            reasoning.extend(corr_reasoning)
        
        # =====================================================================
        # 4. Participation Gate
        # =====================================================================
        participation_allowed, gate_reason = self._check_participation_gate(
            symbol, current_session, session_quality
        )
        if not participation_allowed:
            score_adjustment -= 20
        if gate_reason:
            reasoning.append(gate_reason)
        
        # =====================================================================
        # 5. Build result
        # =====================================================================
        htf_trend = "UP" if direction == "BULLISH" else "DOWN" if direction == "BEARISH" else "SIDEWAYS"
        
        bias = MacroBias(
            direction=direction,
            session_quality=session_quality,
            htf_trend=htf_trend,
            correlation_aligned=correlation_aligned,
            participation_allowed=participation_allowed,
            score_adjustment=score_adjustment,
            reasoning=reasoning,
            d1_trend=d1_trend,
            h4_trend=h4_trend,
            current_session=current_session,
            session_time_remaining=session_remaining
        )
        
        # Cache result
        self._bias_cache[symbol] = (bias, datetime.now(timezone.utc))
        
        return bias
    
    def _analyze_htf_trend(self, symbol: str) -> Tuple[str, str, List[str]]:
        """
        Analyze D1 and H4 trends.
        Returns: (d1_trend, h4_trend, reasoning)
        """
        reasoning = []
        d1_trend = "SIDEWAYS"
        h4_trend = "SIDEWAYS"
        
        try:
            # D1 Analysis
            d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
            if d1_rates is not None and len(d1_rates) >= 20:
                df_d1 = pd.DataFrame(d1_rates)
                df_d1['ema20'] = df_d1['close'].ewm(span=20).mean()
                df_d1['ema50'] = df_d1['close'].ewm(span=50).mean()
                
                last = df_d1.iloc[-1]
                if last['close'] > last['ema20'] > last['ema50']:
                    d1_trend = "UP"
                    reasoning.append("D1: Price > EMA20 > EMA50 (Bullish)")
                elif last['close'] < last['ema20'] < last['ema50']:
                    d1_trend = "DOWN"
                    reasoning.append("D1: Price < EMA20 < EMA50 (Bearish)")
                else:
                    reasoning.append("D1: Mixed EMA structure (Neutral)")
            
            # H4 Analysis
            h4_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50)
            if h4_rates is not None and len(h4_rates) >= 20:
                df_h4 = pd.DataFrame(h4_rates)
                df_h4['ema20'] = df_h4['close'].ewm(span=20).mean()
                df_h4['ema50'] = df_h4['close'].ewm(span=50).mean()
                
                last = df_h4.iloc[-1]
                if last['close'] > last['ema20'] > last['ema50']:
                    h4_trend = "UP"
                    reasoning.append("H4: Price > EMA20 > EMA50 (Bullish)")
                elif last['close'] < last['ema20'] < last['ema50']:
                    h4_trend = "DOWN"
                    reasoning.append("H4: Price < EMA20 < EMA50 (Bearish)")
                else:
                    reasoning.append("H4: Mixed EMA structure (Neutral)")
                    
        except Exception as e:
            logger.warning(f"HTF analysis failed for {symbol}: {e}")
            reasoning.append(f"⚠️ HTF analysis error: {e}")
        
        return d1_trend, h4_trend, reasoning
    
    def _analyze_session(self, symbol: str) -> Tuple[str, str, int]:
        """
        Analyze current session and quality for this symbol.
        Returns: (session_name, quality, minutes_remaining)
        """
        now_utc = datetime.now(timezone.utc)
        current_hour = now_utc.hour
        
        # Determine current session
        current_session = "CLOSED"
        session_end = 24
        
        for name, info in self.SESSIONS.items():
            if info["start"] <= current_hour < info["end"]:
                current_session = name
                session_end = info["end"]
                break
        
        # Calculate time remaining in session
        minutes_remaining = (session_end - current_hour) * 60 - now_utc.minute
        
        # Determine quality for this specific symbol
        preferred_sessions = self.SYMBOL_SESSIONS.get(symbol, ["LONDON", "OVERLAP", "NEW_YORK"])
        
        if current_session in preferred_sessions:
            if current_session == "OVERLAP":
                quality = "PRIME"
            else:
                quality = "GOOD"
        elif current_session == "CLOSED":
            quality = "POOR"
        else:
            quality = "MARGINAL"
        
        return current_session, quality, minutes_remaining
    
    def _check_correlations(
        self, 
        symbol: str, 
        proposed_direction: str,
        open_positions: Dict[str, float]
    ) -> Tuple[bool, List[str]]:
        """
        Check if proposed trade aligns with existing correlated positions.
        Returns: (is_aligned, reasoning)
        """
        reasoning = []
        
        # Get correlated symbols
        positive_corr = self.POSITIVE_CORRELATIONS.get(symbol, [])
        negative_corr = self.NEGATIVE_CORRELATIONS.get(symbol, [])
        
        # Check positive correlations
        for corr_symbol in positive_corr:
            if corr_symbol in open_positions:
                pos_direction = "BULLISH" if open_positions[corr_symbol] > 0 else "BEARISH"
                if pos_direction != proposed_direction:
                    reasoning.append(
                        f"⚠️ Correlation conflict: {symbol} {proposed_direction} vs "
                        f"{corr_symbol} {pos_direction} (positive correlation)"
                    )
                    return False, reasoning
        
        # Check negative correlations
        for corr_symbol in negative_corr:
            if corr_symbol in open_positions:
                pos_direction = "BULLISH" if open_positions[corr_symbol] > 0 else "BEARISH"
                if pos_direction == proposed_direction:
                    reasoning.append(
                        f"⚠️ Correlation conflict: {symbol} {proposed_direction} vs "
                        f"{corr_symbol} {pos_direction} (negative correlation)"
                    )
                    return False, reasoning
        
        return True, reasoning
    
    def _check_participation_gate(
        self, 
        symbol: str, 
        current_session: str,
        session_quality: str
    ) -> Tuple[bool, str]:
        """
        Final check on whether to participate in the market now.
        Returns: (should_participate, reason)
        """
        # Block trading in CLOSED session for most instruments
        if current_session == "CLOSED":
            if symbol not in ["BTCUSD", "ETHUSD", "SOLUSD"]:  # Crypto OK 24/7
                return False, "🚫 Market closed - no participation"
        
        # Block very early Asian session for non-JPY
        now_utc = datetime.now(timezone.utc)
        if current_session == "ASIAN" and now_utc.hour < 2:
            if "JPY" not in symbol:
                return False, "🚫 Early Asian - low liquidity for this pair"
        
        # Allow otherwise
        return True, ""
    
    def get_bias_summary(self, symbols: List[str]) -> Dict[str, str]:
        """Get quick bias summary for multiple symbols"""
        summary = {}
        for symbol in symbols:
            bias = self.analyze(symbol)
            summary[symbol] = f"{bias.direction} ({bias.session_quality})"
        return summary
    
    def clear_cache(self):
        """Clear bias cache"""
        self._bias_cache.clear()


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
    else:
        strategist = MacroStrategist()
        
        # Analyze EURUSD
        bias = strategist.analyze("EURUSD")
        
        print("\n=== Macro Bias: EURUSD ===")
        print(f"Direction: {bias.direction}")
        print(f"HTF Trend: {bias.htf_trend}")
        print(f"Session: {bias.current_session} ({bias.session_quality})")
        print(f"Session Time Remaining: {bias.session_time_remaining} mins")
        print(f"Participation Allowed: {bias.participation_allowed}")
        print(f"Score Adjustment: {bias.score_adjustment:+d}")
        
        print("\n=== Reasoning ===")
        for r in bias.reasoning:
            print(f"  • {r}")
        
        # Quick summary
        print("\n=== Universe Summary ===")
        symbols = ["EURUSD", "GBPUSD", "GOLD", "BTCUSD"]
        summary = strategist.get_bias_summary(symbols)
        for sym, bias_str in summary.items():
            print(f"  {sym}: {bias_str}")
        
        mt5.shutdown()
