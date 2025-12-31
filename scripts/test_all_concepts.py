"""
LIVE MARKET TEST - All 9 Books Concepts
========================================
Test every concept on real market data right now.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timezone

def initialize_mt5():
    """Connect to MT5"""
    if not mt5.initialize():
        print(f"❌ MT5 initialization failed: {mt5.last_error()}")
        return False
    
    account = mt5.account_info()
    print("="*60)
    print(f"✅ MT5 Connected: {account.login}")
    print(f"💰 Equity: ${account.equity:,.2f}")
    print("="*60)
    return True

def check_session():
    """Test: Session Filter (Daytrading book)"""
    print("\n📊 TEST 1: Session Filter")
    utc_hour = datetime.now(timezone.utc).hour
    
    if 7 <= utc_hour < 10:
        session = "LONDON_OPEN ✅"
    elif 12 <= utc_hour < 13:
        session = "OVERLAP ✅ (Best!)"
    elif 13 <= utc_hour < 16:
        session = "NY_OPEN ✅"
    elif 17 <= utc_hour < 20:
        session = "LUNCH_DEAD ❌"
    elif 21 <= utc_hour or utc_hour < 5:
        session = "AFTER_HOURS ❌"
    else:
        session = "OK"
    
    print(f"Current time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}")
    print(f"Session: {session}")
    
    return "DEAD" not in session and "AFTER" not in session

def analyze_vpa(symbol):
    """Test: Volume Price Analysis (VPA book)"""
    print(f"\n📊 TEST 2: Volume Price Analysis - {symbol}")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
    if rates is None:
        print("❌ No data")
        return None
    
    df = pd.DataFrame(rates)
    df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
    df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA']
    
    curr = df.iloc[-1]
    is_up = curr['close'] > curr['open']
    vol_ratio = curr['VOL_RATIO']
    
    print(f"Current bar: {'🟢 UP' if is_up else '🔴 DOWN'}")
    print(f"Volume ratio: {vol_ratio:.2f}x average")
    
    if is_up and vol_ratio > 1.5:
        signal = "BULLISH STRENGTH ✅ (Score: 95)"
    elif is_up and vol_ratio < 0.8:
        signal = "BULLISH WEAKNESS ❌ (Skip)"
    elif not is_up and vol_ratio > 1.5:
        signal = "BEARISH STRENGTH ✅ (Score: 95)"
    elif not is_up and vol_ratio < 0.8:
        signal = "BEARISH WEAKNESS ❌ (Skip)"
    else:
        signal = "NEUTRAL"
    
    print(f"VPA Signal: {signal}")
    return signal

def find_sr_levels(symbol):
    """Test: Support/Resistance (TA books)"""
    print(f"\n📊 TEST 3: Support/Resistance - {symbol}")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        print("❌ No data")
        return None, None
    
    df = pd.DataFrame(rates)
    
    # Find pivot highs/lows
    pivot_highs = []
    pivot_lows = []
    
    for i in range(5, len(df)-5):
        if df['high'].iloc[i] == df['high'].iloc[i-5:i+6].max():
            pivot_highs.append(df['high'].iloc[i])
        if df['low'].iloc[i] == df['low'].iloc[i-5:i+6].min():
            pivot_lows.append(df['low'].iloc[i])
    
    if pivot_highs:
        resistance = sorted(pivot_highs)[-3:]  # Top 3
        print(f"Resistance levels: {[f'{r:.5f}' for r in resistance]}")
    else:
        resistance = []
    
    if pivot_lows:
        support = sorted(pivot_lows)[:3]  # Bottom 3
        print(f"Support levels: {[f'{s:.5f}' for s in support]}")
    else:
        support = []
    
    current_price = df.iloc[-1]['close']
    print(f"Current price: {current_price:.5f}")
    
    # Check if near S/R
    for level in resistance + support:
        if abs(current_price - level) / current_price < 0.002:
            print(f"⚠️  NEAR S/R LEVEL: {level:.5f} (Skip trade)")
            return support, resistance
    
    print("✅ Clear of S/R zones")
    return support, resistance

def calculate_atr(symbol):
    """Test: ATR-based stops (Daytrading book)"""
    print(f"\n📊 TEST 4: ATR-Based Stops - {symbol}")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        print("❌ No data")
        return None
    
    df = pd.DataFrame(rates)
    
    # Calculate ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    
    current_atr = atr.iloc[-1]
    current_price = df.iloc[-1]['close']
    
    # Calculate dynamic stops
    sl_distance = current_atr * 2
    tp_distance = current_atr * 3
    
    print(f"ATR: {current_atr:.5f}")
    print(f"Recommended SL: {sl_distance:.5f} ({sl_distance/current_price*100:.2f}%)")
    print(f"Recommended TP: {tp_distance:.5f} ({tp_distance/current_price*100:.2f}%)")
    
    return current_atr

def check_adx(symbol):
    """Test: ADX trend filter (TA book)"""
    print(f"\n📊 TEST 5: ADX Trend Strength - {symbol}")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        print("❌ No data")
        return None
    
    df = pd.DataFrame(rates)
    
    # Calculate ADX
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(14).mean()
    
    current_adx = adx.iloc[-1]
    
    print(f"ADX: {current_adx:.1f}")
    
    if current_adx > 40:
        print("✅ VERY STRONG TREND (Boost score +10)")
    elif current_adx > 25:
        print("✅ STRONG TREND (Good to trade)")
    elif current_adx > 20:
        print("⚠️  WEAK TREND (Tradeable)")
    else:
        print("❌ NO TREND (Skip trade)")
    
    return current_adx

def detect_candlestick_patterns(symbol):
    """Test: Candlestick patterns (Candlestick book)"""
    print(f"\n📊 TEST 6: Candlestick Patterns - {symbol}")
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 10)
    if rates is None:
        print("❌ No data")
        return None
    
    df = pd.DataFrame(rates)
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    patterns_found = []
    
    # Hammer
    body = abs(curr['close'] - curr['open'])
    lower_wick = min(curr['open'], curr['close']) - curr['low']
    upper_wick = curr['high'] - max(curr['open'], curr['close'])
    
    if lower_wick > body * 2 and upper_wick < body * 0.5:
        patterns_found.append("🔨 HAMMER (Bullish, Score: 88)")
    
    # Shooting Star
    if upper_wick > body * 2 and lower_wick < body * 0.5:
        patterns_found.append("⭐ SHOOTING STAR (Bearish, Score: 88)")
    
    # Doji
    range_ = curr['high'] - curr['low']
    if body / range_ < 0.1:
        patterns_found.append("⚖️  DOJI (Reversal warning)")
    
    # Bullish Engulfing
    if (curr['close'] > curr['open'] and
        prev['close'] < prev['open'] and
        curr['open'] < prev['close'] and
        curr['close'] > prev['open']):
        patterns_found.append("📈 BULLISH ENGULFING (Strong buy, Score: 92)")
    
    if patterns_found:
        for pattern in patterns_found:
            print(f"✅ {pattern}")
    else:
        print("No patterns detected")
    
    return patterns_found

def scan_for_gaps(symbol):
    """Test: Gap trading (Gaps book)"""
    print(f"\n📊 TEST 7: Gap Detection - {symbol}")
    
    # Check if Monday
    day = datetime.now(timezone.utc).weekday()
    if day not in [0, 6]:  # Monday or Sunday
        print("⚠️  Gap trading only on Mondays/weekends")
        return None
    
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 5)
    if rates is None:
        print("❌ No data")
        return None
    
    df = pd.DataFrame(rates)
    prev_close = df.iloc[-2]['close']
    curr_open = df.iloc[-1]['open']
    
    gap_pct = (curr_open - prev_close) / prev_close * 100
    
    if abs(gap_pct) > 0.5:
        direction = "🔼 GAP UP" if gap_pct > 0 else "🔽 GAP DOWN"
        print(f"{direction}: {gap_pct:.2f}%")
        print(f"Expected: Gap fill to {prev_close:.5f} (80% probability)")
        print(f"Signal: {'SELL' if gap_pct > 0 else 'BUY'} (Score: 88)")
    else:
        print("No significant gap detected")
    
    return gap_pct

def test_symbol(symbol):
    """Test all concepts on one symbol"""
    print(f"\n{'='*60}")
    print(f"🎯 TESTING: {symbol}")
    print(f"{'='*60}")
    
    # 1. VPA
    vpa = analyze_vpa(symbol)
    
    # 2. S/R
    support, resistance = find_sr_levels(symbol)
    
    # 3. ATR
    atr = calculate_atr(symbol)
    
    # 4. ADX
    adx = check_adx(symbol)
    
    # 5. Candlestick
    patterns = detect_candlestick_patterns(symbol)
    
    # 6. Gaps
    gap = scan_for_gaps(symbol)
    
    # Final verdict
    print(f"\n{'='*60}")
    print("📊 FINAL VERDICT:")
    
    signals = []
    if vpa and "STRENGTH" in vpa:
        signals.append("VPA confirms")
    if adx and adx > 25:
        signals.append("Strong trend")
    if patterns:
        signals.append(f"{len(patterns)} patterns")
    
    if signals:
        print(f"✅ TRADEABLE: {', '.join(signals)}")
    else:
        print("❌ SKIP: No confluence")
    
    print(f"{'='*60}\n")

def main():
    """Test all concepts on live markets"""
    print("\n🚀 LIVE MARKET TEST - All 9 Books Concepts")
    print("Testing concepts on real-time MT5 data...\n")
    
    if not initialize_mt5():
        return
    
    # Check session
    is_good_session = check_session()
    
    if not is_good_session:
        print("\n⚠️  WARNING: Not a power hour session")
        print("Books recommend: Wait for London/NY open\n")
    
    # Test on multiple symbols
    symbols = ["EURUSD", "GBPUSD", "GOLD", "BTCUSD"]
    
    for symbol in symbols:
        # Check if symbol exists
        if mt5.symbol_info(symbol) is None:
            print(f"⚠️  {symbol} not available")
            continue
        
        test_symbol(symbol)
    
    print("\n✅ TEST COMPLETE")
    print("\nConcepts tested:")
    print("1. Session filters (Daytrading)")
    print("2. Volume Price Analysis (VPA)")
    print("3. Support/Resistance (TA)")
    print("4. ATR-based stops (Daytrading)")
    print("5. ADX trend filter (TA)")
    print("6. Candlestick patterns (Candlestick book)")
    print("7. Gap trading (Gaps book)")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
