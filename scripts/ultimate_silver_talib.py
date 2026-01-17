import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib
from datetime import datetime

def ultimate_silver_analysis():
    if not mt5.initialize():
        print("MT5 failed")
        return
    
    symbol = "SILVER"
    
    print("=" * 90)
    print(f"🔬 ULTIMATE SILVER ANALYSIS - TA-LIB FULL ARSENAL")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    
    # Get multi-timeframe data
    h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    h4_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 200)
    d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 200)
    
    if h1_rates is None or h4_rates is None or d1_rates is None:
        print("Failed to fetch data")
        return
    
    # Convert to DataFrames
    df_h1 = pd.DataFrame(h1_rates)
    df_h4 = pd.DataFrame(h4_rates)
    df_d1 = pd.DataFrame(d1_rates)
    
    current_price = df_h1['close'].iloc[-1]
    
    print(f"\n💰 CURRENT PRICE: ${current_price:.2f}")
    print("\n" + "=" * 90)
    
    # === TREND STRENGTH INDICATORS ===
    print("\n📊 TREND STRENGTH & MOMENTUM")
    print("-" * 90)
    
    # ADX (Average Directional Index) - Trend Strength
    adx_h1 = talib.ADX(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=14)
    adx_h4 = talib.ADX(df_h4['high'], df_h4['low'], df_h4['close'], timeperiod=14)
    adx_d1 = talib.ADX(df_d1['high'], df_d1['low'], df_d1['close'], timeperiod=14)
    
    plus_di_h1 = talib.PLUS_DI(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=14)
    minus_di_h1 = talib.MINUS_DI(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=14)
    
    print(f"ADX (Trend Strength):")
    print(f"  H1:  {adx_h1.iloc[-1]:.1f} {'🔥 VERY STRONG' if adx_h1.iloc[-1] > 50 else '✅ STRONG' if adx_h1.iloc[-1] > 25 else '⚪ WEAK'}")
    print(f"  H4:  {adx_h4.iloc[-1]:.1f} {'🔥 VERY STRONG' if adx_h4.iloc[-1] > 50 else '✅ STRONG' if adx_h4.iloc[-1] > 25 else '⚪ WEAK'}")
    print(f"  D1:  {adx_d1.iloc[-1]:.1f} {'🔥 VERY STRONG' if adx_d1.iloc[-1] > 50 else '✅ STRONG' if adx_d1.iloc[-1] > 25 else '⚪ WEAK'}")
    print(f"  Direction: {'+DI' if plus_di_h1.iloc[-1] > minus_di_h1.iloc[-1] else '-DI'} (+DI: {plus_di_h1.iloc[-1]:.1f}, -DI: {minus_di_h1.iloc[-1]:.1f})")
    
    # CCI (Commodity Channel Index)
    cci_h1 = talib.CCI(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=20)
    cci_h4 = talib.CCI(df_h4['high'], df_h4['low'], df_h4['close'], timeperiod=20)
    
    print(f"\nCCI (Commodity Channel Index):")
    print(f"  H1:  {cci_h1.iloc[-1]:.1f} {'🔴 EXTREME OVERBOUGHT' if cci_h1.iloc[-1] > 200 else '⚠️ OVERBOUGHT' if cci_h1.iloc[-1] > 100 else 'NEUTRAL'}")
    print(f"  H4:  {cci_h4.iloc[-1]:.1f} {'🔴 EXTREME OVERBOUGHT' if cci_h4.iloc[-1] > 200 else '⚠️ OVERBOUGHT' if cci_h4.iloc[-1] > 100 else 'NEUTRAL'}")
    
    # Williams %R
    willr_h1 = talib.WILLR(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=14)
    willr_h4 = talib.WILLR(df_h4['high'], df_h4['low'], df_h4['close'], timeperiod=14)
    
    print(f"\nWilliams %R:")
    print(f"  H1:  {willr_h1.iloc[-1]:.1f} {'🔴 OVERBOUGHT' if willr_h1.iloc[-1] > -20 else '🟢 OVERSOLD' if willr_h1.iloc[-1] < -80 else 'NEUTRAL'}")
    print(f"  H4:  {willr_h4.iloc[-1]:.1f} {'🔴 OVERBOUGHT' if willr_h4.iloc[-1] > -20 else '🟢 OVERSOLD' if willr_h4.iloc[-1] < -80 else 'NEUTRAL'}")
    
    # === VOLATILITY INDICATORS ===
    print("\n\n🌊 VOLATILITY & RANGE")
    print("-" * 90)
    
    # ATR (Average True Range)
    atr_h1 = talib.ATR(df_h1['high'], df_h1['low'], df_h1['close'], timeperiod=14)
    atr_h4 = talib.ATR(df_h4['high'], df_h4['low'], df_h4['close'], timeperiod=14)
    
    print(f"ATR (Volatility):")
    print(f"  H1:  ${atr_h1.iloc[-1]:.2f}")
    print(f"  H4:  ${atr_h4.iloc[-1]:.2f}")
    
    # Bollinger Bands
    upper_h1, middle_h1, lower_h1 = talib.BBANDS(df_h1['close'], timeperiod=20, nbdevup=2, nbdevdn=2)
    bb_position = ((current_price - lower_h1.iloc[-1]) / (upper_h1.iloc[-1] - lower_h1.iloc[-1])) * 100
    
    print(f"\nBollinger Bands (H1):")
    print(f"  Upper:  ${upper_h1.iloc[-1]:.2f}")
    print(f"  Middle: ${middle_h1.iloc[-1]:.2f}")
    print(f"  Lower:  ${lower_h1.iloc[-1]:.2f}")
    print(f"  Position: {bb_position:.1f}% {'🔴 EXTREME HIGH' if bb_position > 90 else '⚠️ HIGH' if bb_position > 70 else 'MID'}")
    
    # === PATTERN RECOGNITION ===
    print("\n\n🎯 CANDLESTICK PATTERNS (Last 10 bars)")
    print("-" * 90)
    
    patterns = {
        'Doji': talib.CDLDOJI(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Hammer': talib.CDLHAMMER(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Shooting Star': talib.CDLSHOOTINGSTAR(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Engulfing': talib.CDLENGULFING(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Evening Star': talib.CDLEVENINGSTAR(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Morning Star': talib.CDLMORNINGSTAR(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Hanging Man': talib.CDLHANGINGMAN(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
        'Dark Cloud': talib.CDLDARKCLOUDCOVER(df_h1['open'], df_h1['high'], df_h1['low'], df_h1['close']),
    }
    
    patterns_found = []
    for name, pattern in patterns.items():
        recent = pattern.tail(10)
        if (recent != 0).any():
            last_signal = recent[recent != 0].iloc[-1] if len(recent[recent != 0]) > 0 else 0
            if last_signal != 0:
                signal_type = "BEARISH" if last_signal < 0 else "BULLISH"
                patterns_found.append(f"  {name}: {signal_type} ({'🔴' if signal_type == 'BEARISH' else '🟢'})")
    
    if patterns_found:
        for p in patterns_found:
            print(p)
    else:
        print("  No significant patterns detected")
    
    # === MOMENTUM OSCILLATORS ===
    print("\n\n⚡ MOMENTUM OSCILLATORS")
    print("-" * 90)
    
    # RSI
    rsi_h1 = talib.RSI(df_h1['close'], timeperiod=14)
    rsi_h4 = talib.RSI(df_h4['close'], timeperiod=14)
    rsi_d1 = talib.RSI(df_d1['close'], timeperiod=14)
    
    print(f"RSI:")
    print(f"  H1:  {rsi_h1.iloc[-1]:.1f} {'🔴 EXTREME' if rsi_h1.iloc[-1] > 80 else '⚠️ OVERBOUGHT' if rsi_h1.iloc[-1] > 70 else 'NEUTRAL'}")
    print(f"  H4:  {rsi_h4.iloc[-1]:.1f} {'🔴 EXTREME' if rsi_h4.iloc[-1] > 80 else '⚠️ OVERBOUGHT' if rsi_h4.iloc[-1] > 70 else 'NEUTRAL'}")
    print(f"  D1:  {rsi_d1.iloc[-1]:.1f} {'🔴 EXTREME' if rsi_d1.iloc[-1] > 80 else '⚠️ OVERBOUGHT' if rsi_d1.iloc[-1] > 70 else 'NEUTRAL'}")
    
    # Stochastic
    slowk, slowd = talib.STOCH(df_h1['high'], df_h1['low'], df_h1['close'], 
                                fastk_period=14, slowk_period=3, slowd_period=3)
    
    print(f"\nStochastic:")
    print(f"  %K: {slowk.iloc[-1]:.1f}")
    print(f"  %D: {slowd.iloc[-1]:.1f}")
    print(f"  Signal: {'🔴 OVERBOUGHT' if slowk.iloc[-1] > 80 else '🟢 OVERSOLD' if slowk.iloc[-1] < 20 else 'NEUTRAL'}")
    
    # MFI (Money Flow Index)
    mfi = talib.MFI(df_h1['high'], df_h1['low'], df_h1['close'], df_h1['tick_volume'], timeperiod=14)
    print(f"\nMoney Flow Index:")
    print(f"  MFI: {mfi.iloc[-1]:.1f} {'🔴 OVERBOUGHT' if mfi.iloc[-1] > 80 else '🟢 OVERSOLD' if mfi.iloc[-1] < 20 else 'NEUTRAL'}")
    
    # === DIVERGENCE DETECTION ===
    print("\n\n🔍 DIVERGENCE ANALYSIS (H1)")
    print("-" * 90)
    
    # Check for RSI divergence
    recent_highs_price = []
    recent_highs_rsi = []
    
    for i in range(-20, -1):
        if i > -len(df_h1) and i < -2:
            if df_h1['high'].iloc[i] > df_h1['high'].iloc[i-1] and df_h1['high'].iloc[i] > df_h1['high'].iloc[i+1]:
                recent_highs_price.append(df_h1['high'].iloc[i])
                recent_highs_rsi.append(rsi_h1.iloc[i])
    
    if len(recent_highs_price) >= 2:
        if recent_highs_price[-1] > recent_highs_price[-2] and recent_highs_rsi[-1] < recent_highs_rsi[-2]:
            print("  🚨 BEARISH DIVERGENCE DETECTED!")
            print(f"     Price: ${recent_highs_price[-2]:.2f} → ${recent_highs_price[-1]:.2f} (Higher)")
            print(f"     RSI:   {recent_highs_rsi[-2]:.1f} → {recent_highs_rsi[-1]:.1f} (Lower)")
        else:
            print("  ✅ No bearish divergence")
    else:
        print("  ⚪ Insufficient data for divergence analysis")
    
    # === FIBONACCI RETRACEMENT ===
    print("\n\n📐 FIBONACCI RETRACEMENT (Based on recent swing)")
    print("-" * 90)
    
    recent_low = df_d1['low'].tail(50).min()
    recent_high = df_d1['high'].tail(50).max()
    diff = recent_high - recent_low
    
    fib_levels = {
        '0%': recent_high,
        '23.6%': recent_high - (diff * 0.236),
        '38.2%': recent_high - (diff * 0.382),
        '50%': recent_high - (diff * 0.5),
        '61.8%': recent_high - (diff * 0.618),
        '78.6%': recent_high - (diff * 0.786),
        '100%': recent_low
    }
    
    print(f"Swing High: ${recent_high:.2f}")
    print(f"Swing Low:  ${recent_low:.2f}")
    print(f"\nFibonacci Levels:")
    for level, price in fib_levels.items():
        proximity = "← CURRENT" if abs(current_price - price) < 1.0 else ""
        print(f"  {level:>6}: ${price:.2f} {proximity}")
    
    # === FINAL VERDICT ===
    print("\n\n" + "=" * 90)
    print("🎯 THE ULTIMATE VERDICT")
    print("=" * 90)
    
    bull_signals = 0
    bear_signals = 0
    
    # Count signals
    if adx_h1.iloc[-1] > 25 and plus_di_h1.iloc[-1] > minus_di_h1.iloc[-1]:
        bull_signals += 1
    if rsi_h1.iloc[-1] > 70:
        bear_signals += 1  # Overbought = potential reversal
    if cci_h1.iloc[-1] > 100:
        bear_signals += 1
    if willr_h1.iloc[-1] > -20:
        bear_signals += 1
    if bb_position > 80:
        bear_signals += 1
    if slowk.iloc[-1] > 80:
        bear_signals += 1
    
    print(f"\n📊 SIGNAL COUNT:")
    print(f"  Bullish Signals: {bull_signals}")
    print(f"  Bearish Signals: {bear_signals} (Reversal)")
    
    print(f"\n🔥 TREND VERDICT:")
    if adx_h1.iloc[-1] > 50:
        print(f"  PARABOLIC TREND in progress")
    elif adx_h1.iloc[-1] > 25:
        print(f"  STRONG TREND in progress")
    else:
        print(f"  WEAK TREND / RANGING")
    
    print(f"\n⚖️ SHORT POSITION VERDICT:")
    if bear_signals >= 4:
        print(f"  ✅ JUSTIFIED - Multiple reversal signals")
    elif bear_signals >= 2:
        print(f"  ⚠️ RISKY - Some reversal signals but trend still strong")
    else:
        print(f"  ❌ DANGEROUS - Fighting a strong trend with few reversal signals")
    
    mt5.shutdown()

if __name__ == "__main__":
    ultimate_silver_analysis()
