import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime
import sys

# --- CONFIGURATION ---
SYMBOL = "GOLD"
TIMEFRAMES = {
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1
}

def get_hurst_exponent(time_series, max_lag=20):
    """Returns the Hurst Exponent of the time series"""
    lags = range(2, max_lag)
    tau = [np.sqrt(np.std(np.subtract(time_series[lag:], time_series[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

def analyze_seasonality(df):
    """Analyzes Hour and Day performance"""
    df['hour'] = df['time'].dt.hour
    df['day_of_week'] = df['time'].dt.day_name()
    df['return'] = df['close'].pct_change()
    df['volatility'] = (df['high'] - df['low'])

    # Hourly Volatility (Where is the action?)
    hourly_vol = df.groupby('hour')['volatility'].mean()
    
    # Daily Returns (Which day is Bullish?)
    daily_ret = df.groupby('day_of_week')['return'].mean() * 100 # In percent
    
    return hourly_vol, daily_ret

def analyze_candle_physics(df):
    """Analyzes Probability of Continuation vs Reversal"""
    df['color'] = np.where(df['close'] > df['open'], 1, -1) # 1=Green, -1=Red
    
    # What is the probability of a Green after a Green?
    df['prev_color'] = df['color'].shift(1)
    
    green_after_green = len(df[(df['color'] == 1) & (df['prev_color'] == 1)])
    green_after_red = len(df[(df['color'] == 1) & (df['prev_color'] == -1)])
    total_greens = len(df[df['prev_color'] == 1])
    total_reds = len(df[df['prev_color'] == -1])
    
    prob_gg = (green_after_green / total_greens) * 100 if total_greens > 0 else 0
    prob_gr = (green_after_red / total_reds) * 100 if total_reds > 0 else 0
    
    return prob_gg, prob_gr


def analyze_streaks(df):
    """Analyzes Probability of Streaks (3 consecutive candles)"""
    df['color'] = np.where(df['close'] > df['open'], 1, -1)
    
    # Shift to get previous 1, 2, 3 candles
    c1 = df['color'].shift(1)
    c2 = df['color'].shift(2)
    c3 = df['color'].shift(3)
    
    # Pattern: 3 Greens in a row
    three_greens = (c1 == 1) & (c2 == 1) & (c3 == 1)
    total_3g = len(df[three_greens])
    # Outcome: 4th is Green
    four_greens = len(df[three_greens & (df['color'] == 1)])
    
    prob_4g = (four_greens / total_3g) * 100 if total_3g > 0 else 0
    
    # Pattern: 3 Reds in a row
    three_reds = (c1 == -1) & (c2 == -1) & (c3 == -1)
    total_3r = len(df[three_reds])
    # Outcome: 4th is Red
    four_reds = len(df[three_reds & (df['color'] == -1)])
    
    prob_4r = (four_reds / total_3r) * 100 if total_3r > 0 else 0
    
    return prob_4g, prob_4r

def analyze_wick_physics(df):
    """Analyzes if Long Upper Wicks actually predict Reversals"""
    body_size = abs(df['close'] - df['open'])
    upper_wick = df['high'] - df[['open', 'close']].max(axis=1)
    long_wick_candle = (upper_wick > body_size) & (body_size > 0.0001)
    prev_long_wick = long_wick_candle.shift(1).fillna(False)
    after_wick_df = df[prev_long_wick]
    if len(after_wick_df) == 0: return 0.0
    reversals = after_wick_df[after_wick_df['close'] < after_wick_df['open']]
    prob_reversal = (len(reversals) / len(after_wick_df)) * 100
    return prob_reversal

def analyze_mtf_correlation(symbol):
    """Check how D1 Color influences H1 Probabilities"""
    # Fetch D1 and H1
    d1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1000))
    h1 = pd.DataFrame(mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 24000))
    
    if d1.empty or h1.empty: return "No Data"
    
    d1['time'] = pd.to_datetime(d1['time'], unit='s')
    h1['time'] = pd.to_datetime(h1['time'], unit='s')
    
    d1['date'] = d1['time'].dt.date
    h1['date'] = h1['time'].dt.date
    
    d1['bias'] = np.where(d1['close'] > d1['open'], 1, -1)
    
    # Join H1 with D1 Bias
    merged = pd.merge(h1, d1[['date', 'bias']], on='date', how='left')
    merged.dropna(inplace=True)
    
    # If D1 is Green (1), what brings H1 Green probability?
    h1_green_on_green_day = merged[(merged['bias'] == 1) & (merged['close'] > merged['open'])]
    total_h1_on_green_day = merged[merged['bias'] == 1]
    
    prob_alignment = (len(h1_green_on_green_day) / len(total_h1_on_green_day)) * 100
    
    return prob_alignment

def analyze_fundamentals_proxy(df):
    """News Volatility: Check Spikes at typical News Hours"""
    df['hour'] = df['time'].dt.hour
    df['range'] = df['high'] - df['low']
    
    # 13:00 / 14:00 / 15:00 UTC (US Open / News Windows)
    news_hours = [13, 14, 15] 
    other_hours = [h for h in range(24) if h not in news_hours]
    
    news_vol = df[df['hour'].isin(news_hours)]['range'].mean()
    normal_vol = df[df['hour'].isin(other_hours)]['range'].mean()
    
    impact_ratio = news_vol / normal_vol if normal_vol > 0 else 1
    return impact_ratio

def analyze_mean_reversion_failure(df):
    """Why Mean Reversion Fails: Continuation after 2-Sigma limit"""
    # BB Calculation
    df['sma'] = df['close'].rolling(20).mean()
    df['std'] = df['close'].rolling(20).std()
    df['upper'] = df['sma'] + (2 * df['std'])
    
    # Condition: Price closes ABOVE Bollinger Upper Band (Overbought)
    overbought = df['close'] > df['upper']
    
    # Next Candle Outcome?
    # Mean Reversion hypothesis: Next candle RED (Close < Open)
    # Momentum hypothesis: Next candle GREEN (Close > Open)
    
    prev_ob = overbought.shift(1).fillna(False)
    after_ob = df[prev_ob]
    
    if len(after_ob) == 0: return 0.0
    
    # Count Reversals (Red candle after Overbought)
    reversals = after_ob[after_ob['close'] < after_ob['open']]
    success_rate = (len(reversals) / len(after_ob)) * 100
    
    return success_rate

def run_pattern_miner():
    print(f"TITAN DEEP PATTERN MINER | Scanning {SYMBOL}...")
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    insights = []

    # --- MTF ANALYSIS ---
    print("\n--- Scanning MTF Correlation ---")
    mtf_align = analyze_mtf_correlation(SYMBOL)
    insights.append(f"MTF Physics: When D1 is Green, H1 is Green {mtf_align:.1f}% of the time (The Tide Effect)")

    for tf_name, tf_val in TIMEFRAMES.items():
        print(f"\n--- Scanning {tf_name} ---")
        rates = mt5.copy_rates_from_pos(SYMBOL, tf_val, 0, 99999) 
        if rates is None: continue
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # 1. Hurst
        try:
            h = get_hurst_exponent(df['close'].values)
            h_type = "Trending" if h > 0.5 else "Mean Reverting"
            insights.append(f"{tf_name} Hurst: {h:.2f} ({h_type})")
        except Exception: pass

        # 2. Seasonality (H1 Only)
        if tf_name == "H1":
            # Fundamental Proxy
            news_factor = analyze_fundamentals_proxy(df)
            insights.append(f"Fundamental Impact: News Hours are {news_factor:.1f}x more volatile than average")

        # 3. Candle Physics
        prob_gg, prob_gr = analyze_candle_physics(df)
        insights.append(f"{tf_name} Momentum: {prob_gg:.1f}%")
        
        # 4. Streak Physics
        p4g, p4r = analyze_streaks(df)
        insights.append(f"{tf_name} 4th Candle Streak: {p4g:.1f}%")

        # 5. Wick Physics
        wick_rev = analyze_wick_physics(df)
        insights.append(f"{tf_name} Wick Trap: {wick_rev:.1f}% Reversal Rate")
        
        # 6. Mean Reversion Autopsy
        mr_rate = analyze_mean_reversion_failure(df)
        insights.append(f"{tf_name} Bollinger Reversion Success: {mr_rate:.1f}% (Buying Overbought fails)")

    mt5.shutdown()
    
    print("\nMINER RESULTS:")
    final_report = "# TITAN HOLOGRAPHIC MARKET REPORT (PHASE 3)\n\n"
    for line in insights:
        print(line)
        final_report += f"- {line}\n"
        
    with open("TITAN_DEEP_INSIGHTS.md", "w") as f:
        f.write(final_report)
