import pandas as pd
import numpy as np

DATA_PATH = "data/true_pnl_training_data.csv"

def deep_dive_analysis():
    if not pd.io.common.file_exists(DATA_PATH):
        print(f"Error: Data file {DATA_PATH} not found.")
        return

    df = pd.read_csv(DATA_PATH)
    
    print("="*60)
    print("🚀 DEEP INTELLIGENCE EXPANSION: QUANTITATIVE LESSONS")
    print("="*60)
    
    # 1. Volatility (ATR%) Bins
    print("\n--- Volatility Win-Rate Distribution (ATR%) ---")
    df['atr_bin'] = pd.qcut(df['atr_pct'], 5, labels=["Very Low", "Low", "Mid", "High", "Extreme"])
    vol_stats = df.groupby('atr_bin')['outcome'].agg(['count', 'mean']).rename(columns={'mean': 'win_rate'})
    print(vol_stats)
    
    # 2. RSI (Exhaustion) Bins
    print("\n--- RSI Win-Rate Distribution ---")
    df['rsi_bin'] = pd.cut(df['rsi_norm'] * 100, bins=[0, 30, 45, 55, 70, 100], labels=["Oversold", "Weak Bear", "Neutral", "Weak Bull", "Overbought"])
    rsi_stats = df.groupby('rsi_bin')['outcome'].agg(['count', 'mean']).rename(columns={'mean': 'win_rate'})
    print(rsi_stats)
    
    # 3. Momentum (ADX) Bins
    print("\n--- Momentum Win-Rate Distribution (ADX) ---")
    df['adx_bin'] = pd.cut(df['adx_norm'] * 50, bins=[0, 15, 25, 40, 100], labels=["No Trend", "Forming", "Strong", "Extreme"])
    adx_stats = df.groupby('adx_bin')['outcome'].agg(['count', 'mean']).rename(columns={'mean': 'win_rate'})
    print(adx_stats)

    # 4. Session/Hour Analysis
    print("\n--- Hourly Performance Heatmap (UTC Hour) ---")
    hour_stats = df.groupby('hour_sin')['outcome'].mean() # Using sin/cos is harder to read here, let's use the 'hour' if we had it, but we can infer from session
    # Actually let's just look at NY/London flags
    session_stats = {
        'London': df[df['session_london'] == 1]['outcome'].mean(),
        'NY': df[df['session_ny'] == 1]['outcome'].mean(),
        'Overlap': df[(df['session_london'] == 1) & (df['session_ny'] == 1)]['outcome'].mean(),
        'Asian/Other': df[(df['session_london'] == 0) & (df['session_ny'] == 0)]['outcome'].mean()
    }
    for session, wr in session_stats.items():
        print(f"{session:12} Win Rate: {wr:.2%}")

    # 5. Directional Bias
    print("\n--- Directional Efficiency ---")
    dir_stats = df.groupby('direction_buy')['outcome'].mean()
    print(f"BUY Signals win rate:  {dir_stats.get(1, 0):.2%}")
    print(f"SELL Signals win rate: {dir_stats.get(0, 0):.2%}")

if __name__ == "__main__":
    deep_dive_analysis()
