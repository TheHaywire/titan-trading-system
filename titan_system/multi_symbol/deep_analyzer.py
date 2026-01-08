"""
Deep Position Analyzer - Comprehensive Trade Analysis
======================================================
Multi-timeframe analysis with key levels, volatility assessment,
and trade suitability for scalping/intraday/swing.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def calc_rsi(df, period=14):
    """Calculate RSI."""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calc_atr(df, period=14):
    """Calculate ATR."""
    tr = np.maximum(df['high'] - df['low'], 
                   np.maximum(abs(df['high'] - df['close'].shift(1)),
                             abs(df['low'] - df['close'].shift(1))))
    return tr.rolling(period).mean()


def find_support_resistance(df, window=20):
    """Find key S/R levels using pivots."""
    highs = df['high'].rolling(window, center=True).max()
    lows = df['low'].rolling(window, center=True).min()
    
    # Resistance: where price touched high multiple times
    resistance_levels = []
    support_levels = []
    
    for i in range(window, len(df) - window):
        if df['high'].iloc[i] == highs.iloc[i]:
            resistance_levels.append(df['high'].iloc[i])
        if df['low'].iloc[i] == lows.iloc[i]:
            support_levels.append(df['low'].iloc[i])
    
    # Cluster nearby levels
    def cluster_levels(levels, tolerance_pct=0.5):
        if not levels:
            return []
        levels = sorted(levels)
        clustered = []
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if (level - current_cluster[0]) / current_cluster[0] * 100 < tolerance_pct:
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        clustered.append(np.mean(current_cluster))
        return clustered[-3:]  # Return top 3
    
    return cluster_levels(resistance_levels), cluster_levels(support_levels)


def analyze_symbol_deep(symbol):
    """Comprehensive multi-timeframe analysis."""
    
    if not mt5.initialize():
        return None
    
    result = {
        'symbol': symbol,
        'timestamp': datetime.now()
    }
    
    # Get multi-timeframe data
    try:
        d1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 100))
        h4 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 100))
        h1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200))
        m15 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 200))
    except Exception:
        return None
    
    if d1.empty or h4.empty:
        return None
    
    tick = mt5.symbol_info_tick(symbol)
    current = (tick.bid + tick.ask) / 2
    result['current_price'] = current
    
    # === TREND ANALYSIS ===
    d1['sma20'] = d1['close'].rolling(20).mean()
    d1['sma50'] = d1['close'].rolling(50).mean()
    h4['sma20'] = h4['close'].rolling(20).mean()
    h1['sma20'] = h1['close'].rolling(20).mean()
    
    d1_trend = 'BULLISH' if d1['close'].iloc[-1] > d1['sma20'].iloc[-1] > d1['sma50'].iloc[-1] else \
               'BEARISH' if d1['close'].iloc[-1] < d1['sma20'].iloc[-1] < d1['sma50'].iloc[-1] else 'RANGING'
    h4_trend = 'BULLISH' if h4['close'].iloc[-1] > h4['sma20'].iloc[-1] else 'BEARISH'
    h1_trend = 'BULLISH' if h1['close'].iloc[-1] > h1['sma20'].iloc[-1] else 'BEARISH'
    
    result['trend'] = {
        'D1': d1_trend,
        'H4': h4_trend,
        'H1': h1_trend,
        'aligned': d1_trend == h4_trend == h1_trend
    }
    
    # === KEY LEVELS ===
    d1_res, d1_sup = find_support_resistance(d1)
    h4_res, h4_sup = find_support_resistance(h4)
    
    result['levels'] = {
        'D1_resistance': d1_res,
        'D1_support': d1_sup,
        'H4_resistance': h4_res,
        'H4_support': h4_sup,
        'D1_high_20': d1['high'].tail(20).max(),
        'D1_low_20': d1['low'].tail(20).min(),
        'price_position_pct': ((current - d1['low'].tail(20).min()) / 
                               (d1['high'].tail(20).max() - d1['low'].tail(20).min()) * 100)
    }
    
    # === RSI ===
    d1_rsi = calc_rsi(d1).iloc[-1]
    h4_rsi = calc_rsi(h4).iloc[-1]
    h1_rsi = calc_rsi(h1).iloc[-1]
    
    result['rsi'] = {
        'D1': d1_rsi,
        'H4': h4_rsi,
        'H1': h1_rsi,
        'overbought': d1_rsi > 70 or h4_rsi > 70,
        'oversold': d1_rsi < 30 or h4_rsi < 30
    }
    
    # === VOLATILITY ===
    h1_atr = calc_atr(h1).iloc[-1]
    atr_pct = (h1_atr / current) * 100
    
    if atr_pct > 2:
        suitability = 'SWING'
    elif atr_pct > 0.5:
        suitability = 'INTRADAY'
    else:
        suitability = 'SCALPING'
    
    result['volatility'] = {
        'H1_ATR': h1_atr,
        'ATR_pct': atr_pct,
        'suitability': suitability
    }
    
    # === VOLUME ===
    avg_vol = h1['tick_volume'].rolling(20).mean().iloc[-1]
    curr_vol = h1['tick_volume'].iloc[-1]
    
    result['volume'] = {
        'current': curr_vol,
        'avg_20': avg_vol,
        'ratio': curr_vol / avg_vol if avg_vol > 0 else 0
    }
    
    # === SYMBOL PROPERTIES ===
    info = mt5.symbol_info(symbol)
    result['properties'] = {
        'spread': info.spread,
        'spread_pct': (info.spread * info.point) / current * 100,
        'volume_min': info.volume_min,
        'volume_max': info.volume_max,
        'swap_long': info.swap_long,
        'swap_short': info.swap_short,
        'high_swap': abs(info.swap_long) > 5 or abs(info.swap_short) > 5
    }
    
    # === TRADE RECOMMENDATION ===
    if result['trend']['aligned']:
        if result['trend']['D1'] == 'BULLISH':
            bias = 'LONG'
        elif result['trend']['D1'] == 'BEARISH':
            bias = 'SHORT'
        else:
            bias = 'NEUTRAL'
    else:
        bias = 'CONFLICTING - Wait for alignment'
    
    # Adjust for RSI
    if result['rsi']['overbought'] and bias == 'LONG':
        bias = 'LONG but OVERBOUGHT - Wait for pullback'
    elif result['rsi']['oversold'] and bias == 'SHORT':
        bias = 'SHORT but OVERSOLD - Wait for pullback'
    
    result['recommendation'] = {
        'bias': bias,
        'style': suitability,
        'confidence': 'HIGH' if result['trend']['aligned'] else 'LOW'
    }
    
    return result


def analyze_open_positions():
    """Analyze all open positions deeply."""
    
    if not mt5.initialize():
        return []
    
    positions = mt5.positions_get()
    if not positions:
        return []
    
    results = []
    
    for pos in positions:
        # Get symbol analysis
        analysis = analyze_symbol_deep(pos.symbol)
        if not analysis:
            continue
        
        # Position details
        info = mt5.symbol_info(pos.symbol)
        entry_time = datetime.fromtimestamp(pos.time)
        hours_held = (datetime.now() - entry_time).total_seconds() / 3600
        
        direction = 'LONG' if pos.type == 0 else 'SHORT'
        
        # Is direction correct?
        trend_match = False
        if direction == 'LONG' and 'BULLISH' in analysis['trend']['D1']:
            trend_match = True
        elif direction == 'SHORT' and 'BEARISH' in analysis['trend']['D1']:
            trend_match = True
        
        # Exposure calculation
        contract_size = info.trade_contract_size
        exposure = pos.volume * contract_size * pos.price_current
        
        # Risk assessment
        has_sl = pos.sl > 0
        has_tp = pos.tp > 0
        
        if has_sl:
            sl_distance = abs(pos.price_current - pos.sl)
            sl_risk = pos.volume * contract_size * sl_distance
        else:
            sl_risk = float('inf')
        
        results.append({
            'symbol': pos.symbol,
            'ticket': pos.ticket,
            'direction': direction,
            'volume': pos.volume,
            'entry': pos.price_open,
            'current': pos.price_current,
            'pnl': pos.profit,
            'sl': pos.sl,
            'tp': pos.tp,
            'has_sl': has_sl,
            'has_tp': has_tp,
            'exposure': exposure,
            'sl_risk': sl_risk,
            'hours_held': hours_held,
            'trend_aligned': trend_match,
            'analysis': analysis
        })
    
    return results


def print_deep_analysis(positions_analysis):
    """Print comprehensive analysis."""
    
    print("\n" + "="*70)
    print("  DEEP POSITION ANALYSIS")
    print("="*70)
    
    total_exposure = 0
    total_pnl = 0
    
    for pos in positions_analysis:
        analysis = pos['analysis']
        
        print(f"\n{'='*70}")
        print(f"  {pos['symbol']} - {pos['direction']} {pos['volume']} lots")
        print("="*70)
        
        # Price & P&L
        print(f"\n📊 POSITION:")
        print(f"   Entry: {pos['entry']:.2f} | Current: {pos['current']:.2f}")
        print(f"   P&L: ${pos['pnl']:.2f}")
        print(f"   Held: {pos['hours_held']:.1f} hours")
        
        # Trend alignment
        print(f"\n📈 TREND ALIGNMENT:")
        trend = analysis['trend']
        print(f"   D1: {trend['D1']} | H4: {trend['H4']} | H1: {trend['H1']}")
        
        if pos['trend_aligned']:
            print(f"   ✅ Position ALIGNED with trend")
        else:
            print(f"   ❌ Position AGAINST trend!")
        
        # Key levels
        levels = analysis['levels']
        print(f"\n🎯 KEY LEVELS:")
        print(f"   Price at {levels['price_position_pct']:.0f}% of D1 range")
        print(f"   D1 Range: {levels['D1_low_20']:.2f} - {levels['D1_high_20']:.2f}")
        if levels['D1_resistance']:
            print(f"   Resistance: {[f'{r:.2f}' for r in levels['D1_resistance']]}")
        if levels['D1_support']:
            print(f"   Support: {[f'{s:.2f}' for s in levels['D1_support']]}")
        
        # RSI
        rsi = analysis['rsi']
        print(f"\n📉 RSI:")
        print(f"   D1: {rsi['D1']:.1f} | H4: {rsi['H4']:.1f} | H1: {rsi['H1']:.1f}")
        if rsi['overbought']:
            print(f"   ⚠️ OVERBOUGHT - Potential reversal risk")
        elif rsi['oversold']:
            print(f"   ⚠️ OVERSOLD - Potential reversal risk")
        
        # Volatility
        vol = analysis['volatility']
        print(f"\n📊 VOLATILITY:")
        print(f"   ATR: {vol['H1_ATR']:.2f} ({vol['ATR_pct']:.2f}%)")
        print(f"   Best for: {vol['suitability']}")
        
        # Risk
        print(f"\n⚠️ RISK:")
        if pos['has_sl']:
            print(f"   SL: {pos['sl']:.2f} (Risk: ${pos['sl_risk']:.2f})")
        else:
            print(f"   ❌ NO STOP LOSS - EXTREME RISK!")
        
        if pos['has_tp']:
            print(f"   TP: {pos['tp']:.2f}")
        else:
            print(f"   ⚠️ No take profit set")
        
        # Properties
        props = analysis['properties']
        print(f"\n🔧 SYMBOL PROPERTIES:")
        print(f"   Spread: {props['spread']} pts ({props['spread_pct']:.3f}%)")
        print(f"   Swap Long: {props['swap_long']:.2f} | Short: {props['swap_short']:.2f}")
        if props['high_swap']:
            print(f"   ⚠️ High swap costs - not ideal for swing/hold")
        
        # Recommendation
        rec = analysis['recommendation']
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Market Bias: {rec['bias']}")
        print(f"   Trade Style: {rec['style']}")
        print(f"   Confidence: {rec['confidence']}")
        
        total_exposure += pos['exposure']
        total_pnl += pos['pnl']
    
    # Summary
    print(f"\n{'='*70}")
    print("  SUMMARY")
    print("="*70)
    
    acc = mt5.account_info()
    print(f"\n   Total Positions: {len(positions_analysis)}")
    print(f"   Total Exposure: ${total_exposure:,.0f}")
    print(f"   Total P&L: ${total_pnl:.2f}")
    print(f"   Account Balance: ${acc.balance:,.0f}")
    print(f"   Exposure Ratio: {(total_exposure/acc.balance)*100:.1f}%")
    
    # Positions without SL
    no_sl = [p for p in positions_analysis if not p['has_sl']]
    if no_sl:
        print(f"\n   ⚠️ {len(no_sl)} POSITIONS WITHOUT STOP LOSS!")
        for p in no_sl:
            print(f"      - {p['symbol']} {p['direction']} {p['volume']} lots")
    
    # Against trend
    against = [p for p in positions_analysis if not p['trend_aligned']]
    if against:
        print(f"\n   ⚠️ {len(against)} POSITIONS AGAINST TREND!")
        for p in against:
            print(f"      - {p['symbol']} {p['direction']}")


if __name__ == "__main__":
    positions = analyze_open_positions()
    print_deep_analysis(positions)
