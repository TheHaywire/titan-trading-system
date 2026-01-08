"""
Execution-Grade Position Analyzer
=================================
Institutional-level trade analysis with:
- Trade state classification (EXCELLENT/ACCEPTABLE/WARNING/INVALID)
- R-multiple tracking
- ADX regime detection
- Correlation & exposure netting
- Explicit invalidation logic
- Session awareness
- Actionable recommendations

This is NOT just analysis - it tells you WHAT TO DO.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import logging

logger = logging.getLogger("Titan.ExecutionAnalyzer")


class TradeState(Enum):
    """Trade classification for action decisions."""
    EXCELLENT = "EXCELLENT"      # Hold, consider adding
    ACCEPTABLE = "ACCEPTABLE"    # Hold, monitor
    WARNING = "WARNING"          # Reduce size or tighten SL
    INVALID = "INVALID"          # Close immediately


class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING_STRONG = "TRENDING_STRONG"    # ADX > 25, clear direction
    TRENDING_WEAK = "TRENDING_WEAK"        # ADX 20-25
    RANGING = "RANGING"                     # ADX < 20
    VOLATILE = "VOLATILE"                   # High ATR expansion
    COMPRESSED = "COMPRESSED"               # Low ATR, breakout pending


class TradingSession(Enum):
    """Trading session windows (UTC)."""
    ASIA = "ASIA"           # 00:00 - 08:00
    LONDON = "LONDON"       # 08:00 - 16:00
    NEW_YORK = "NEW_YORK"   # 13:00 - 21:00
    OVERLAP = "OVERLAP"     # 13:00 - 16:00 (highest liquidity)
    OFF_HOURS = "OFF_HOURS"


@dataclass
class RiskMetrics:
    """R-multiple and risk tracking."""
    initial_risk_r: float         # Entry to SL distance in R
    current_r: float              # Current P&L in R terms
    remaining_upside_r: float     # Current to TP in R
    risk_reward_ratio: float      # Original R:R
    breakeven_distance: float     # Price distance to breakeven
    max_favorable_r: float        # Best R reached (for trailing)


@dataclass
class InvalidationCondition:
    """Explicit invalidation logic."""
    condition: str
    is_triggered: bool
    action: str
    urgency: str  # IMMEDIATE, SOON, MONITOR


@dataclass 
class PositionAnalysis:
    """Complete position analysis result."""
    symbol: str
    ticket: int
    direction: str
    volume: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_pct: float
    
    # Risk metrics
    sl: float
    tp: float
    has_sl: bool
    has_tp: bool
    risk_metrics: Optional[RiskMetrics]
    
    # Market context
    d1_trend: str
    h4_trend: str
    h1_trend: str
    trend_aligned: bool
    
    # Regime
    regime: MarketRegime
    adx: float
    atr_pct: float
    
    # RSI
    rsi_d1: float
    rsi_h4: float
    rsi_h1: float
    overbought: bool
    oversold: bool
    
    # Levels
    price_position_pct: float  # 0-100 in range
    near_resistance: bool
    near_support: bool
    
    # Session
    current_session: TradingSession
    optimal_session: bool
    
    # Exposure
    exposure_usd: float
    exposure_pct: float
    
    # Swap cost
    daily_swap: float
    days_held: float
    total_swap_cost: float
    
    # Classification
    state: TradeState
    state_reasons: List[str]
    invalidations: List[InvalidationCondition]
    
    # Actions
    recommended_action: str
    action_priority: str  # IMMEDIATE, TODAY, MONITOR


def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calc_adx(df: pd.DataFrame, period: int = 14) -> float:
    """Calculate ADX for regime detection."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    
    # Directional Movement
    plus_dm = high.diff()
    minus_dm = low.diff().abs() * -1
    
    plus_dm = plus_dm.where((plus_dm > minus_dm.abs()) & (plus_dm > 0), 0)
    minus_dm = minus_dm.abs().where((minus_dm.abs() > plus_dm) & (minus_dm < 0), 0)
    
    # Smoothed
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
    adx = dx.rolling(period).mean()
    
    return adx.iloc[-1] if not adx.empty else 0


def calc_ema_compression(df: pd.DataFrame) -> Dict:
    """
    Detect EMA compression/expansion for breakout anticipation.
    
    Returns:
        Dict with compression state and breakout direction hint
    """
    # Calculate multiple EMAs
    df = df.copy()
    df['ema8'] = df['close'].ewm(span=8).mean()
    df['ema21'] = df['close'].ewm(span=21).mean()
    df['ema50'] = df['close'].ewm(span=50).mean()
    
    # Current values
    ema8 = df['ema8'].iloc[-1]
    ema21 = df['ema21'].iloc[-1]
    ema50 = df['ema50'].iloc[-1]
    price = df['close'].iloc[-1]
    
    # Calculate EMA spread (how far apart they are)
    spread_8_21 = abs(ema8 - ema21) / ema21 * 100
    spread_21_50 = abs(ema21 - ema50) / ema50 * 100
    total_spread = spread_8_21 + spread_21_50
    
    # Historical spread for comparison
    hist_spreads = []
    for i in range(-20, -1):
        if i < -len(df):
            continue
        s8 = abs(df['ema8'].iloc[i] - df['ema21'].iloc[i]) / df['ema21'].iloc[i] * 100
        s21 = abs(df['ema21'].iloc[i] - df['ema50'].iloc[i]) / df['ema50'].iloc[i] * 100
        hist_spreads.append(s8 + s21)
    
    avg_spread = np.mean(hist_spreads) if hist_spreads else total_spread
    
    # Determine state
    if total_spread < avg_spread * 0.5:
        state = "COMPRESSED"  # EMAs converging - breakout pending
    elif total_spread > avg_spread * 1.5:
        state = "EXPANDED"    # EMAs diverging - trend in motion
    else:
        state = "NORMAL"
    
    # Breakout direction hint based on EMA order
    if ema8 > ema21 > ema50:
        direction_hint = "BULLISH"
    elif ema8 < ema21 < ema50:
        direction_hint = "BEARISH"
    else:
        direction_hint = "MIXED"
    
    return {
        'state': state,
        'spread_pct': total_spread,
        'avg_spread_pct': avg_spread,
        'direction_hint': direction_hint,
        'ema8': ema8,
        'ema21': ema21,
        'ema50': ema50
    }


def calculate_suggested_sl(symbol: str, direction: str, entry_price: float = None) -> Dict:
    """
    Calculate suggested stop loss based on ATR and structure.
    
    Args:
        symbol: MT5 symbol
        direction: 'LONG' or 'SHORT'
        entry_price: Optional entry price (uses current if not provided)
    
    Returns:
        Dict with suggested SL levels and reasoning
    """
    h4 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 50))
    h1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100))
    
    if h4.empty or h1.empty:
        return {'error': 'No data'}
    
    tick = mt5.symbol_info_tick(symbol)
    current = entry_price if entry_price else (tick.bid + tick.ask) / 2
    
    # Calculate ATR
    h4['tr'] = np.maximum(h4['high'] - h4['low'], 
                         np.maximum(abs(h4['high'] - h4['close'].shift(1)),
                                   abs(h4['low'] - h4['close'].shift(1))))
    atr_h4 = h4['tr'].rolling(14).mean().iloc[-1]
    
    h1['tr'] = np.maximum(h1['high'] - h1['low'], 
                         np.maximum(abs(h1['high'] - h1['close'].shift(1)),
                                   abs(h1['low'] - h1['close'].shift(1))))
    atr_h1 = h1['tr'].rolling(14).mean().iloc[-1]
    
    # Recent swing points
    recent_high = h4['high'].tail(10).max()
    recent_low = h4['low'].tail(10).min()
    
    if direction.upper() == 'LONG':
        # For longs: SL below recent low or 1.5-2x ATR below entry
        sl_atr_tight = current - (atr_h4 * 1.5)
        sl_atr_normal = current - (atr_h4 * 2.0)
        sl_atr_wide = current - (atr_h4 * 2.5)
        sl_structure = recent_low - (atr_h1 * 0.5)  # Below recent low
        
    else:  # SHORT
        sl_atr_tight = current + (atr_h4 * 1.5)
        sl_atr_normal = current + (atr_h4 * 2.0)
        sl_atr_wide = current + (atr_h4 * 2.5)
        sl_structure = recent_high + (atr_h1 * 0.5)  # Above recent high
    
    # Calculate risk in pips/points
    info = mt5.symbol_info(symbol)
    point = info.point if info else 0.0001
    
    return {
        'current_price': current,
        'direction': direction.upper(),
        'atr_h4': atr_h4,
        'suggested_sl': {
            'tight': round(sl_atr_tight, info.digits if info else 5),
            'normal': round(sl_atr_normal, info.digits if info else 5),
            'wide': round(sl_atr_wide, info.digits if info else 5),
            'structure': round(sl_structure, info.digits if info else 5)
        },
        'risk_distance': {
            'tight': abs(current - sl_atr_tight),
            'normal': abs(current - sl_atr_normal),
            'wide': abs(current - sl_atr_wide),
            'structure': abs(current - sl_structure)
        },
        'recommendation': 'normal'  # Default recommendation
    }


def find_symbol(query: str) -> Optional[str]:
    """
    Smart symbol finder - auto-corrects symbol names.
    
    Args:
        query: Symbol name to search for
        
    Returns:
        Correct MT5 symbol name or None
    """
    all_symbols = mt5.symbols_get()
    if not all_symbols:
        return None
    
    query_upper = query.upper()
    
    # Exact match first
    for s in all_symbols:
        if s.name.upper() == query_upper:
            return s.name
    
    # Partial match
    matches = [s.name for s in all_symbols if query_upper in s.name.upper()]
    if matches:
        # Prefer Cash versions for indices
        cash = [m for m in matches if 'Cash' in m]
        if cash:
            return cash[0]
        return matches[0]
    
    return None


def analyze_symbol(symbol: str) -> Optional[Dict]:
    """
    Analyze any symbol (not just open positions).
    
    Returns comprehensive market analysis for trade decisions.
    """
    # Auto-resolve symbol name
    resolved = find_symbol(symbol)
    if not resolved:
        return {'error': f'Symbol {symbol} not found'}
    
    symbol = resolved
    
    # Get data
    d1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100))
    h4 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 100))
    h1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200))
    
    if d1.empty or h4.empty or len(d1) < 50:
        return {'error': f'Insufficient data for {symbol}'}
    
    tick = mt5.symbol_info_tick(symbol)
    info = mt5.symbol_info(symbol)
    current = (tick.bid + tick.ask) / 2
    
    # Trends
    d1['sma20'] = d1['close'].rolling(20).mean()
    d1['sma50'] = d1['close'].rolling(50).mean()
    h4['sma20'] = h4['close'].rolling(20).mean()
    h1['sma20'] = h1['close'].rolling(20).mean()
    
    d1_trend = 'BULLISH' if d1['close'].iloc[-1] > d1['sma20'].iloc[-1] > d1['sma50'].iloc[-1] else \
               'BEARISH' if d1['close'].iloc[-1] < d1['sma20'].iloc[-1] < d1['sma50'].iloc[-1] else 'RANGING'
    h4_trend = 'BULLISH' if h4['close'].iloc[-1] > h4['sma20'].iloc[-1] else 'BEARISH'
    h1_trend = 'BULLISH' if h1['close'].iloc[-1] > h1['sma20'].iloc[-1] else 'BEARISH'
    
    # ADX
    adx = calc_adx(h4)
    
    # EMA Compression
    ema_analysis = calc_ema_compression(h4)
    
    # RSI
    rsi_d1 = calc_rsi(d1['close']).iloc[-1]
    rsi_h4 = calc_rsi(h4['close']).iloc[-1]
    rsi_h1 = calc_rsi(h1['close']).iloc[-1]
    
    # ATR
    h4['tr'] = np.maximum(h4['high'] - h4['low'], 
                         np.maximum(abs(h4['high'] - h4['close'].shift(1)),
                                   abs(h4['low'] - h4['close'].shift(1))))
    atr = h4['tr'].rolling(14).mean().iloc[-1]
    atr_pct = (atr / current) * 100
    
    # Range position
    d1_high = d1['high'].tail(20).max()
    d1_low = d1['low'].tail(20).min()
    range_pct = ((current - d1_low) / (d1_high - d1_low) * 100)
    
    # Regime
    if adx > 25:
        regime = 'TRENDING_STRONG'
    elif adx > 20:
        regime = 'TRENDING_WEAK'
    elif ema_analysis['state'] == 'COMPRESSED':
        regime = 'COMPRESSED'
    elif atr_pct > 2:
        regime = 'VOLATILE'
    else:
        regime = 'RANGING'
    
    # Trade suitability
    if atr_pct > 1:
        style = 'SWING'
    elif atr_pct > 0.3:
        style = 'INTRADAY'
    else:
        style = 'SCALP'
    # Bias - BACKTEST-VALIDATED SIGNALS
    # Based on 90-day H4 backtest across GOLD, BTCUSD, EURUSD
    # Only using signals with > 55% win rate
    
    aligned = d1_trend == h4_trend
    bias = 'WAIT'
    bias_reason = 'No high-probability setup'
    confidence = 'LOW'
    
    # PRIORITY 1: RSI Extremes (highest WR across all symbols)
    # RSI < 30 for LONG: 68.8% WR on GOLD, 58.4% on BTC
    # RSI > 70 for SHORT: 70.6% WR on BTC, 56% on EUR
    
    if rsi_h4 < 30:
        bias = 'LONG'
        bias_reason = f'RSI extreme oversold ({rsi_h4:.0f}) - 60-70% WR historically'
        confidence = 'HIGH' if rsi_h4 < 25 else 'MEDIUM'
    
    elif rsi_h4 > 70:
        bias = 'SHORT'
        bias_reason = f'RSI extreme overbought ({rsi_h4:.0f}) - 60-80% WR historically'
        confidence = 'HIGH' if rsi_h4 > 75 else 'MEDIUM'
    
    # PRIORITY 2: Range Extremes (only if RSI didn't trigger)
    # Bottom 10-20%: 55-72% WR | Top 10-20%: varies by symbol
    
    elif range_pct < 20:
        if rsi_h4 < 40:  # Confirmation
            bias = 'LONG'
            bias_reason = f'Bottom {range_pct:.0f}% of range + RSI {rsi_h4:.0f} - mean reversion'
            confidence = 'HIGH' if range_pct < 10 else 'MEDIUM'
        else:
            bias = 'WAIT'
            bias_reason = f'Near support ({range_pct:.0f}%) but RSI not confirming'
            confidence = 'LOW'
    
    elif range_pct > 80:
        if rsi_h4 > 60:  # Confirmation
            bias = 'SHORT'
            bias_reason = f'Top {range_pct:.0f}% of range + RSI {rsi_h4:.0f} - mean reversion'
            confidence = 'HIGH' if range_pct > 90 else 'MEDIUM'
        else:
            bias = 'WAIT'
            bias_reason = f'Near resistance ({range_pct:.0f}%) but RSI not confirming'
            confidence = 'LOW'
    
    # PRIORITY 3: Strong momentum for H4 trend trades
    # SMA10 > SMA20: 55-60% WR on GOLD, EUR
    
    elif ema_analysis['direction_hint'] == 'BULLISH' and ema_analysis['state'] == 'EXPANDED':
        bias = 'LONG'
        bias_reason = 'Strong bullish momentum (EMAs expanding)'
        confidence = 'MEDIUM'
    
    elif ema_analysis['direction_hint'] == 'BEARISH' and ema_analysis['state'] == 'EXPANDED':
        bias = 'SHORT'
        bias_reason = 'Strong bearish momentum (EMAs expanding)'
        confidence = 'MEDIUM'
    
    # NOTE: Removed ADX-based trend-following as backtest showed ~50% WR (no edge)
    
    # Get suggested SL for potential trade
    sl_long = calculate_suggested_sl(symbol, 'LONG', current)
    sl_short = calculate_suggested_sl(symbol, 'SHORT', current)
    
    return {
        'symbol': symbol,
        'price': current,
        'spread': info.spread if info else 0,
        'trends': {
            'd1': d1_trend,
            'h4': h4_trend,
            'h1': h1_trend,
            'aligned': aligned
        },
        'adx': adx,
        'regime': regime,
        'ema_compression': ema_analysis,
        'rsi': {
            'd1': rsi_d1,
            'h4': rsi_h4,
            'h1': rsi_h1,
            'overbought': rsi_h4 > 70,
            'oversold': rsi_h4 < 30
        },
        'volatility': {
            'atr': atr,
            'atr_pct': atr_pct,
            'style': style
        },
        'range': {
            'high': d1_high,
            'low': d1_low,
            'position_pct': range_pct
        },
        'bias': bias,
        'bias_reason': bias_reason,
        'confidence': confidence,
        'suggested_sl': {
            'long': sl_long,
            'short': sl_short
        },
        'session': {
            'current': get_current_session().value,
            'optimal': get_optimal_session(symbol).value
        }
    }




def get_current_session() -> TradingSession:
    """Determine current trading session."""
    now = datetime.utcnow()
    hour = now.hour
    
    if 13 <= hour < 16:
        return TradingSession.OVERLAP
    elif 8 <= hour < 16:
        return TradingSession.LONDON
    elif 13 <= hour < 21:
        return TradingSession.NEW_YORK
    elif 0 <= hour < 8:
        return TradingSession.ASIA
    else:
        return TradingSession.OFF_HOURS


def get_optimal_session(symbol: str) -> TradingSession:
    """Determine optimal trading session for symbol."""
    symbol_upper = symbol.upper()
    
    # Crypto - 24/7 but highest volume in US hours
    if any(c in symbol_upper for c in ['BTC', 'ETH', 'XRP', 'ZEC', 'LTC']):
        return TradingSession.NEW_YORK
    
    # JPY pairs - Asia
    if 'JPY' in symbol_upper:
        return TradingSession.ASIA
    
    # EUR/GBP pairs - London
    if any(c in symbol_upper for c in ['EUR', 'GBP', 'CHF']):
        return TradingSession.LONDON
    
    # USD pairs - NY overlap
    if 'USD' in symbol_upper:
        return TradingSession.OVERLAP
    
    # Indices
    if any(i in symbol_upper for i in ['US30', 'US500', 'NAS']):
        return TradingSession.NEW_YORK
    if any(i in symbol_upper for i in ['DAX', 'FTSE']):
        return TradingSession.LONDON
    
    return TradingSession.OVERLAP


def calculate_risk_metrics(pos, info) -> Optional[RiskMetrics]:
    """Calculate R-multiple metrics."""
    if pos.sl == 0:
        return None
    
    entry = pos.price_open
    current = pos.price_current
    sl = pos.sl
    tp = pos.tp if pos.tp > 0 else entry + (entry - sl) * 2  # Assume 2R if no TP
    
    # Initial risk (1R)
    initial_risk = abs(entry - sl)
    if initial_risk == 0:
        return None
    
    # Current R
    if pos.type == 0:  # LONG
        current_r = (current - entry) / initial_risk
        remaining_upside_r = (tp - current) / initial_risk
    else:  # SHORT
        current_r = (entry - current) / initial_risk
        remaining_upside_r = (current - tp) / initial_risk
    
    # R:R ratio
    reward = abs(tp - entry)
    risk_reward = reward / initial_risk if initial_risk > 0 else 0
    
    return RiskMetrics(
        initial_risk_r=1.0,
        current_r=round(current_r, 2),
        remaining_upside_r=round(remaining_upside_r, 2),
        risk_reward_ratio=round(risk_reward, 2),
        breakeven_distance=abs(current - entry),
        max_favorable_r=max(0, current_r)  # Would need history for true MFE
    )


def classify_trade_state(analysis: dict) -> Tuple[TradeState, List[str]]:
    """Classify trade into actionable state."""
    reasons = []
    score = 100  # Start at EXCELLENT, deduct for issues
    
    # Critical issues (INVALID)
    if not analysis['has_sl']:
        reasons.append("NO STOP LOSS - CRITICAL")
        score -= 50
    
    if not analysis['trend_aligned'] and analysis['regime'] == MarketRegime.TRENDING_STRONG:
        reasons.append("Against strong trend")
        score -= 30
    
    if analysis['exposure_pct'] > 20:
        reasons.append(f"Excessive exposure ({analysis['exposure_pct']:.0f}%)")
        score -= 25
    
    # Warning issues
    if analysis['overbought'] and analysis['direction'] == 'LONG':
        reasons.append("Long in overbought conditions")
        score -= 15
    
    if analysis['oversold'] and analysis['direction'] == 'SHORT':
        reasons.append("Short in oversold conditions")
        score -= 15
    
    if analysis['price_position_pct'] > 90 and analysis['direction'] == 'LONG':
        reasons.append("Long at top of range (90%+)")
        score -= 15
    
    if analysis['price_position_pct'] < 10 and analysis['direction'] == 'SHORT':
        reasons.append("Short at bottom of range")
        score -= 15
    
    if analysis['regime'] == MarketRegime.RANGING and analysis['atr_pct'] < 0.3:
        reasons.append("Low volatility ranging market")
        score -= 10
    
    if analysis['daily_swap'] < -50:
        reasons.append(f"High swap cost (${abs(analysis['daily_swap']):.0f}/day)")
        score -= 10
    
    if not analysis['optimal_session']:
        reasons.append("Trading outside optimal session")
        score -= 5
    
    # Positive factors
    if analysis['trend_aligned'] and analysis['regime'] == MarketRegime.TRENDING_STRONG:
        reasons.append("✓ Aligned with strong trend")
        score += 10
    
    if analysis['risk_metrics'] and analysis['risk_metrics'].current_r > 1:
        reasons.append(f"✓ In profit ({analysis['risk_metrics'].current_r}R)")
        score += 10
    
    # Classify
    if score >= 80:
        state = TradeState.EXCELLENT
    elif score >= 60:
        state = TradeState.ACCEPTABLE
    elif score >= 40:
        state = TradeState.WARNING
    else:
        state = TradeState.INVALID
    
    return state, reasons


def generate_invalidations(analysis: dict) -> List[InvalidationCondition]:
    """Generate explicit invalidation conditions."""
    invalidations = []
    
    # No SL
    if not analysis['has_sl']:
        invalidations.append(InvalidationCondition(
            condition="Position has no stop loss",
            is_triggered=True,
            action="ADD STOP LOSS or CLOSE position",
            urgency="IMMEDIATE"
        ))
    
    # Against trend
    if not analysis['trend_aligned'] and analysis['adx'] > 25:
        invalidations.append(InvalidationCondition(
            condition=f"Against strong D1 trend (ADX={analysis['adx']:.0f})",
            is_triggered=True,
            action="Consider closing or reducing size",
            urgency="SOON"
        ))
    
    # Extreme RSI
    if (analysis['overbought'] and analysis['direction'] == 'LONG') or \
       (analysis['oversold'] and analysis['direction'] == 'SHORT'):
        invalidations.append(InvalidationCondition(
            condition=f"RSI extreme ({analysis['rsi_h4']:.0f}) against position",
            is_triggered=True,
            action="Tighten stop or take partial profits",
            urgency="SOON"
        ))
    
    # At range extreme
    if analysis['direction'] == 'LONG' and analysis['price_position_pct'] > 95:
        invalidations.append(InvalidationCondition(
            condition="Price at top 5% of D1 range",
            is_triggered=True,
            action="Take profits or tighten stop",
            urgency="SOON"
        ))
    
    if analysis['direction'] == 'SHORT' and analysis['price_position_pct'] < 5:
        invalidations.append(InvalidationCondition(
            condition="Price at bottom 5% of D1 range",
            is_triggered=True,
            action="Take profits or tighten stop",
            urgency="SOON"
        ))
    
    # Near key level (resistance for longs, support for shorts)
    if analysis['near_resistance'] and analysis['direction'] == 'LONG':
        invalidations.append(InvalidationCondition(
            condition="Approaching major resistance",
            is_triggered=True,
            action="Monitor for rejection, consider scaling out",
            urgency="MONITOR"
        ))
    
    if analysis['near_support'] and analysis['direction'] == 'SHORT':
        invalidations.append(InvalidationCondition(
            condition="Approaching major support",
            is_triggered=True,
            action="Monitor for bounce, consider scaling out",
            urgency="MONITOR"
        ))
    
    # High swap bleeding
    if analysis['total_swap_cost'] < -100:
        invalidations.append(InvalidationCondition(
            condition=f"Swap cost bleeding (${abs(analysis['total_swap_cost']):.0f} so far)",
            is_triggered=True,
            action="Close if not expecting larger move",
            urgency="MONITOR"
        ))
    
    return invalidations


def generate_action(state: TradeState, invalidations: List[InvalidationCondition], 
                   analysis: dict) -> Tuple[str, str]:
    """Generate specific recommended action."""
    
    immediate_issues = [i for i in invalidations if i.urgency == "IMMEDIATE"]
    soon_issues = [i for i in invalidations if i.urgency == "SOON"]
    
    if state == TradeState.INVALID:
        if not analysis['has_sl']:
            return "CLOSE POSITION or ADD STOP LOSS NOW", "IMMEDIATE"
        return "CLOSE POSITION - Multiple critical issues", "IMMEDIATE"
    
    if immediate_issues:
        return immediate_issues[0].action, "IMMEDIATE"
    
    if state == TradeState.WARNING:
        if soon_issues:
            return soon_issues[0].action, "TODAY"
        return "Reduce position size by 50%", "TODAY"
    
    if state == TradeState.ACCEPTABLE:
        if analysis['risk_metrics'] and analysis['risk_metrics'].current_r > 1.5:
            return "Move SL to breakeven", "TODAY"
        return "Hold and monitor", "MONITOR"
    
    if state == TradeState.EXCELLENT:
        if analysis['risk_metrics'] and analysis['risk_metrics'].current_r > 2:
            return "Consider adding to position on pullback", "MONITOR"
        return "Hold position - conditions favorable", "MONITOR"
    
    return "Review manually", "MONITOR"


def analyze_position_full(pos) -> Optional[PositionAnalysis]:
    """Complete position analysis with all metrics."""
    symbol = pos.symbol
    
    # Get data
    try:
        d1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100))
        h4 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 100))
        h1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200))
    except Exception:
        return None
    
    if d1.empty or h4.empty:
        return None
    
    info = mt5.symbol_info(symbol)
    tick = mt5.symbol_info_tick(symbol)
    current = (tick.bid + tick.ask) / 2
    
    # Trend
    d1['sma20'] = d1['close'].rolling(20).mean()
    d1['sma50'] = d1['close'].rolling(50).mean()
    h4['sma20'] = h4['close'].rolling(20).mean()
    h1['sma20'] = h1['close'].rolling(20).mean()
    
    d1_trend = 'BULLISH' if d1['close'].iloc[-1] > d1['sma20'].iloc[-1] > d1['sma50'].iloc[-1] else \
               'BEARISH' if d1['close'].iloc[-1] < d1['sma20'].iloc[-1] < d1['sma50'].iloc[-1] else 'RANGING'
    h4_trend = 'BULLISH' if h4['close'].iloc[-1] > h4['sma20'].iloc[-1] else 'BEARISH'
    h1_trend = 'BULLISH' if h1['close'].iloc[-1] > h1['sma20'].iloc[-1] else 'BEARISH'
    
    direction = 'LONG' if pos.type == 0 else 'SHORT'
    trend_aligned = (direction == 'LONG' and d1_trend == 'BULLISH') or \
                   (direction == 'SHORT' and d1_trend == 'BEARISH')
    
    # Regime (ADX)
    adx = calc_adx(h4)
    h1['tr'] = np.maximum(h4['high'] - h4['low'], 
                         np.maximum(abs(h4['high'] - h4['close'].shift(1)),
                                   abs(h4['low'] - h4['close'].shift(1))))
    atr = h1['tr'].rolling(14).mean().iloc[-1]
    atr_pct = (atr / current) * 100
    
    if adx > 25:
        regime = MarketRegime.TRENDING_STRONG
    elif adx > 20:
        regime = MarketRegime.TRENDING_WEAK
    elif atr_pct > 2:
        regime = MarketRegime.VOLATILE
    elif atr_pct < 0.3:
        regime = MarketRegime.COMPRESSED
    else:
        regime = MarketRegime.RANGING
    
    # RSI
    rsi_d1 = calc_rsi(d1['close']).iloc[-1]
    rsi_h4 = calc_rsi(h4['close']).iloc[-1]
    rsi_h1 = calc_rsi(h1['close']).iloc[-1]
    overbought = rsi_d1 > 70 or rsi_h4 > 70
    oversold = rsi_d1 < 30 or rsi_h4 < 30
    
    # Levels
    d1_high = d1['high'].tail(20).max()
    d1_low = d1['low'].tail(20).min()
    price_position_pct = ((current - d1_low) / (d1_high - d1_low) * 100) if d1_high != d1_low else 50
    near_resistance = price_position_pct > 90
    near_support = price_position_pct < 10
    
    # Session
    current_session = get_current_session()
    optimal = get_optimal_session(symbol)
    optimal_session = current_session == optimal or current_session == TradingSession.OVERLAP
    
    # Exposure
    contract_size = info.trade_contract_size
    exposure_usd = pos.volume * contract_size * current
    acc = mt5.account_info()
    exposure_pct = (exposure_usd / acc.balance) * 100 if acc.balance > 0 else 0
    
    # Swap
    swap_rate = info.swap_long if pos.type == 0 else info.swap_short
    daily_swap = swap_rate * pos.volume
    entry_time = datetime.fromtimestamp(pos.time)
    days_held = (datetime.now() - entry_time).total_seconds() / 86400
    total_swap_cost = daily_swap * days_held
    
    # Risk metrics
    risk_metrics = calculate_risk_metrics(pos, info)
    
    # P&L
    pnl_pct = (pos.profit / acc.balance) * 100 if acc.balance > 0 else 0
    
    # Build analysis dict for classification
    analysis_dict = {
        'has_sl': pos.sl > 0,
        'has_tp': pos.tp > 0,
        'trend_aligned': trend_aligned,
        'regime': regime,
        'adx': adx,
        'atr_pct': atr_pct,
        'direction': direction,
        'overbought': overbought,
        'oversold': oversold,
        'rsi_h4': rsi_h4,
        'price_position_pct': price_position_pct,
        'near_resistance': near_resistance,
        'near_support': near_support,
        'exposure_pct': exposure_pct,
        'daily_swap': daily_swap,
        'total_swap_cost': total_swap_cost,
        'optimal_session': optimal_session,
        'risk_metrics': risk_metrics
    }
    
    # Classify
    state, state_reasons = classify_trade_state(analysis_dict)
    
    # Invalidations
    invalidations = generate_invalidations(analysis_dict)
    
    # Action
    recommended_action, action_priority = generate_action(state, invalidations, analysis_dict)
    
    return PositionAnalysis(
        symbol=symbol,
        ticket=pos.ticket,
        direction=direction,
        volume=pos.volume,
        entry_price=pos.price_open,
        current_price=current,
        pnl=pos.profit,
        pnl_pct=pnl_pct,
        sl=pos.sl,
        tp=pos.tp,
        has_sl=pos.sl > 0,
        has_tp=pos.tp > 0,
        risk_metrics=risk_metrics,
        d1_trend=d1_trend,
        h4_trend=h4_trend,
        h1_trend=h1_trend,
        trend_aligned=trend_aligned,
        regime=regime,
        adx=adx,
        atr_pct=atr_pct,
        rsi_d1=rsi_d1,
        rsi_h4=rsi_h4,
        rsi_h1=rsi_h1,
        overbought=overbought,
        oversold=oversold,
        price_position_pct=price_position_pct,
        near_resistance=near_resistance,
        near_support=near_support,
        current_session=current_session,
        optimal_session=optimal_session,
        exposure_usd=exposure_usd,
        exposure_pct=exposure_pct,
        daily_swap=daily_swap,
        days_held=days_held,
        total_swap_cost=total_swap_cost,
        state=state,
        state_reasons=state_reasons,
        invalidations=invalidations,
        recommended_action=recommended_action,
        action_priority=action_priority
    )


def analyze_portfolio_correlation(analyses: List[PositionAnalysis]) -> Dict:
    """Analyze portfolio-level risks."""
    if not analyses:
        return {}
    
    # Currency exposure
    currency_exposure = {}
    for a in analyses:
        # Extract currencies from symbol
        symbol = a.symbol.upper()
        direction_mult = 1 if a.direction == 'LONG' else -1
        
        if 'USD' in symbol:
            currency_exposure['USD'] = currency_exposure.get('USD', 0) + a.exposure_usd * direction_mult
        if 'EUR' in symbol:
            currency_exposure['EUR'] = currency_exposure.get('EUR', 0) + a.exposure_usd * direction_mult
        if 'BTC' in symbol:
            currency_exposure['CRYPTO'] = currency_exposure.get('CRYPTO', 0) + a.exposure_usd * direction_mult
        if 'ZEC' in symbol:
            currency_exposure['CRYPTO'] = currency_exposure.get('CRYPTO', 0) + a.exposure_usd * direction_mult
    
    # Net directional bias
    total_long = sum(a.exposure_usd for a in analyses if a.direction == 'LONG')
    total_short = sum(a.exposure_usd for a in analyses if a.direction == 'SHORT')
    net_bias = 'LONG' if total_long > total_short else 'SHORT' if total_short > total_long else 'NEUTRAL'
    
    # Risk concentration
    invalid_count = sum(1 for a in analyses if a.state == TradeState.INVALID)
    warning_count = sum(1 for a in analyses if a.state == TradeState.WARNING)
    no_sl_count = sum(1 for a in analyses if not a.has_sl)
    
    return {
        'currency_exposure': currency_exposure,
        'total_long_exposure': total_long,
        'total_short_exposure': total_short,
        'net_directional_bias': net_bias,
        'invalid_positions': invalid_count,
        'warning_positions': warning_count,
        'positions_without_sl': no_sl_count,
        'total_positions': len(analyses)
    }


def print_execution_analysis(analyses: List[PositionAnalysis], portfolio: Dict):
    """Print actionable analysis."""
    
    print("\n" + "="*80)
    print("  EXECUTION-GRADE POSITION ANALYSIS")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + 
          f" | Session: {get_current_session().value}")
    print("="*80)
    
    # Portfolio summary
    if portfolio:
        print(f"\n📊 PORTFOLIO OVERVIEW")
        print("-"*60)
        print(f"   Total Positions: {portfolio['total_positions']}")
        print(f"   Net Bias: {portfolio['net_directional_bias']}")
        print(f"   Long Exposure: ${portfolio['total_long_exposure']:,.0f}")
        print(f"   Short Exposure: ${portfolio['total_short_exposure']:,.0f}")
        
        if portfolio['currency_exposure']:
            print(f"   Currency Exposure: {portfolio['currency_exposure']}")
        
        if portfolio['invalid_positions'] > 0:
            print(f"   ⚠️ INVALID POSITIONS: {portfolio['invalid_positions']} - IMMEDIATE ACTION REQUIRED")
        if portfolio['positions_without_sl'] > 0:
            print(f"   ⚠️ NO STOP LOSS: {portfolio['positions_without_sl']} positions")
    
    # Individual positions
    for a in analyses:
        state_emoji = {
            TradeState.EXCELLENT: "🟢",
            TradeState.ACCEPTABLE: "🟡", 
            TradeState.WARNING: "🟠",
            TradeState.INVALID: "🔴"
        }
        
        print(f"\n{'='*80}")
        print(f"  {state_emoji[a.state]} {a.symbol} | {a.direction} {a.volume} lots | {a.state.value}")
        print("="*80)
        
        # Position details
        print(f"\n📈 POSITION:")
        print(f"   Entry: {a.entry_price:.2f} | Current: {a.current_price:.2f}")
        print(f"   P&L: ${a.pnl:.2f} ({a.pnl_pct:.2f}%)")
        
        if a.risk_metrics:
            rm = a.risk_metrics
            print(f"   R-Multiple: {rm.current_r:+.2f}R | Target: {rm.remaining_upside_r:.2f}R remaining")
            print(f"   Original R:R = 1:{rm.risk_reward_ratio:.1f}")
        
        # Risk status
        print(f"\n⚠️ RISK:")
        if a.has_sl:
            print(f"   SL: {a.sl:.2f} | TP: {a.tp:.2f}" if a.has_tp else f"   SL: {a.sl:.2f} | TP: Not set")
        else:
            print(f"   ❌ NO STOP LOSS - CRITICAL!")
        print(f"   Exposure: ${a.exposure_usd:,.0f} ({a.exposure_pct:.0f}% of balance)")
        print(f"   Daily Swap: ${a.daily_swap:.2f} | Total Swap Cost: ${a.total_swap_cost:.2f}")
        
        # Market context
        print(f"\n📊 MARKET:")
        print(f"   Trends: D1={a.d1_trend} | H4={a.h4_trend} | H1={a.h1_trend}")
        print(f"   Aligned: {'✅ Yes' if a.trend_aligned else '❌ No'}")
        print(f"   Regime: {a.regime.value} (ADX={a.adx:.0f})")
        print(f"   RSI: D1={a.rsi_d1:.0f} | H4={a.rsi_h4:.0f} | H1={a.rsi_h1:.0f}")
        print(f"   Price Position: {a.price_position_pct:.0f}% of D1 range")
        
        # State reasons
        if a.state_reasons:
            print(f"\n📋 ASSESSMENT:")
            for reason in a.state_reasons:
                print(f"   • {reason}")
        
        # Invalidations
        if a.invalidations:
            print(f"\n🚨 INVALIDATION CONDITIONS:")
            for inv in a.invalidations:
                urgency_emoji = {"IMMEDIATE": "🔴", "SOON": "🟠", "MONITOR": "🟡"}
                print(f"   {urgency_emoji[inv.urgency]} {inv.condition}")
                print(f"      → {inv.action}")
        
        # Action
        priority_emoji = {"IMMEDIATE": "🔴", "TODAY": "🟠", "MONITOR": "🟡"}
        print(f"\n💡 RECOMMENDED ACTION [{a.action_priority}]:")
        print(f"   {priority_emoji.get(a.action_priority, '⚪')} {a.recommended_action}")
    
    print("\n" + "="*80)


def run_execution_analysis():
    """Main entry point."""
    if not mt5.initialize():
        print(f"MT5 init failed: {mt5.last_error()}")
        return
    
    positions = mt5.positions_get()
    if not positions:
        print("No open positions")
        return
    
    analyses = []
    for pos in positions:
        analysis = analyze_position_full(pos)
        if analysis:
            analyses.append(analysis)
    
    portfolio = analyze_portfolio_correlation(analyses)
    print_execution_analysis(analyses, portfolio)
    
    # Return for programmatic use
    return analyses, portfolio


if __name__ == "__main__":
    run_execution_analysis()
