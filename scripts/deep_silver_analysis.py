import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

def calculate_rsi(prices, period=14):
    deltas = np.diff(prices)
    seed = deltas[:period+1]
    up = seed[seed >= 0].sum()/period
    down = -seed[seed < 0].sum()/period
    rs = up/down if down != 0 else 0
    rsi = np.zeros_like(prices)
    rsi[:period] = 100. - 100./(1. + rs)
    
    for i in range(period, len(prices)):
        delta = deltas[i-1]
        if delta > 0:
            upval = delta
            downval = 0.
        else:
            upval = 0.
            downval = -delta
        up = (up*(period-1) + upval)/period
        down = (down*(period-1) + downval)/period
        rs = up/down if down != 0 else 0
        rsi[i] = 100. - 100./(1. + rs)
    return rsi

def analyze_silver_complete():
    if not mt5.initialize():
        print("MT5 failed")
        return
    
    symbol = "SILVER"
    current_price = mt5.symbol_info_tick(symbol).bid
    
    print("=" * 80)
    print(f"🔬 COMPLETE SILVER ANALYSIS - {datetime.now().strftime('%H:%M:%S')}")
    print(f"Current Price: ${current_price:.2f}")
    print("=" * 80)
    
    timeframes = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1
    }
    
    print("\n📊 MULTI-TIMEFRAME TECHNICAL ANALYSIS")
    print("-" * 80)
    print(f"{'TF':<6} {'Trend':<8} {'RSI':<8} {'MACD':<10} {'Stoch':<10} {'Verdict':<20}")
    print("-" * 80)
    
    for tf_name, tf in timeframes.items():
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, 100)
            if rates is None or len(rates) < 50:
                continue
            
            df = pd.DataFrame(rates)
            
            # Trend
            ema20 = df['close'].ewm(span=20).mean().iloc[-1]
            ema50 = df['close'].ewm(span=50).mean().iloc[-1]
            trend = "BULL" if current_price > ema20 > ema50 else "BEAR" if current_price < ema20 < ema50 else "MIXED"
            
            # RSI
            rsi = calculate_rsi(df['close'].values)[-1]
            rsi_signal = "OVER" if rsi > 70 else "UNDER" if rsi < 30 else "MID"
            
            # MACD
            ema12 = df['close'].ewm(span=12).mean()
            ema26 = df['close'].ewm(span=26).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9).mean()
            macd_value = macd.iloc[-1]
            signal_value = signal.iloc[-1]
            macd_signal = "BULL" if macd_value > signal_value else "BEAR"
            
            # Stochastic
            low14 = df['low'].rolling(14).min()
            high14 = df['high'].rolling(14).max()
            k = 100 * (df['close'] - low14) / (high14 - low14)
            k_value = k.iloc[-1]
            stoch_signal = "OVER" if k_value > 80 else "UNDER" if k_value < 20 else "MID"
            
            # Verdict
            if rsi > 70 or k_value > 80:
                verdict = "🔴 OVERBOUGHT"
            elif rsi < 30 or k_value < 20:
                verdict = "🟢 OVERSOLD"
            elif trend == "BULL" and macd_signal == "BULL":
                verdict = "⚠️ STRONG BULL"
            elif trend == "BEAR" and macd_signal == "BEAR":
                verdict = "✅ STRONG BEAR"
            else:
                verdict = "⚪ NEUTRAL"
            
            print(f"{tf_name:<6} {trend:<8} {rsi:>6.1f} {macd_signal:<10} {stoch_signal:<10} {verdict:<20}")
            
        except Exception as e:
            print(f"{tf_name:<6} ERROR: {e}")
    
    # Key Levels Analysis
    print("\n🎯 KEY LEVELS & SUPPORT/RESISTANCE")
    print("-" * 80)
    
    # Get daily data for S/R
    daily = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
    if daily is not None:
        df_daily = pd.DataFrame(daily)
        
        # Recent highs/lows
        recent_high = df_daily['high'].tail(20).max()
        recent_low = df_daily['low'].tail(20).min()
        
        # Pivot points
        pivot = (df_daily['high'].iloc[-1] + df_daily['low'].iloc[-1] + df_daily['close'].iloc[-1]) / 3
        r1 = 2 * pivot - df_daily['low'].iloc[-1]
        s1 = 2 * pivot - df_daily['high'].iloc[-1]
        
        print(f"Recent High (20D): ${recent_high:.2f}")
        print(f"Recent Low (20D): ${recent_low:.2f}")
        print(f"Daily Pivot: ${pivot:.2f}")
        print(f"Resistance 1: ${r1:.2f}")
        print(f"Support 1: ${s1:.2f}")
        print(f"\nCurrent vs Pivot: {'+' if current_price > pivot else '-'}${abs(current_price - pivot):.2f}")
        
        if current_price > recent_high * 0.98:
            print("⚠️ NEAR RESISTANCE - Possible reversal zone")
        elif current_price < recent_low * 1.02:
            print("✅ NEAR SUPPORT - Possible bounce zone")
    
    # Volume Analysis
    print("\n📈 VOLUME ANALYSIS")
    print("-" * 80)
    
    h1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
    if h1_data is not None:
        df_h1 = pd.DataFrame(h1_data)
        avg_vol = df_h1['tick_volume'].mean()
        last_vol = df_h1['tick_volume'].iloc[-1]
        vol_ratio = last_vol / avg_vol
        
        print(f"Average H1 Volume: {avg_vol:.0f}")
        print(f"Current H1 Volume: {last_vol:.0f}")
        print(f"Volume Ratio: {vol_ratio:.2f}x")
        
        if vol_ratio > 1.5:
            print("🔥 HIGH VOLUME - Strong move in progress")
        elif vol_ratio < 0.5:
            print("💤 LOW VOLUME - Weak commitment")
    
    mt5.shutdown()

if __name__ == "__main__":
    analyze_silver_complete()
