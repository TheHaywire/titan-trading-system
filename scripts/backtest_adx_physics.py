import pandas as pd
import numpy as np

DATA_PATH = "data/general_market_scenarios_v2.csv"

def backtest_adx():
    print("="*60)
    print("🧪 BACKTEST: THE PHYSICS OF ADX")
    print("="*60)
    
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"❌ Error: Data file {DATA_PATH} not found.")
        return

    # De-normalize features to get raw values
    df['adx'] = df['adx_norm'] * 50
    df['rsi'] = df['rsi_norm'] * 100
    df['atr_pct'] = df['atr_pct']  # Already raw

    # Total Baseline
    base_wr = df['outcome'].mean()
    print(f"📊 Total Baseline Win Rate: {base_wr:.2%} (N={len(df)})")
    print("-" * 60)

    # 1. THE ZONES ANALYSIS
    print("\n🔍 1. ADX ZONES (Speedometer)")
    bins = [0, 15, 20, 25, 30, 40, 50, 100]
    labels = ['0-15 (Dead)', '15-20 (Waking)', '20-25 (Sweet)', '25-30 (Strong)', '30-40 (Fast)', '40-50 (Extreme)', '50+ (Cliff)']
    
    df['adx_zone'] = pd.cut(df['adx'], bins=bins, labels=labels)
    stats = df.groupby('adx_zone')['outcome'].agg(['mean', 'count'])
    stats['lift'] = stats['mean'] - base_wr
    
    # Format output
    print(f"{'Zone':<20} | {'Win Rate':<10} | {'Lift':<10} | {'Samples':<10}")
    print("-" * 60)
    for index, row in stats.iterrows():
        print(f"{index:<20} | {row['mean']:.2%}   | {row['lift']:+.2%}   | {row['count']:<10}")

    # 2. THE STEEL WALL HYPOTHESIS
    print("\n🧱 2. THE STEEL WALL (High RSI + High ADX)")
    
    # Filter: RSI > 70 AND ADX > 40
    steel_wall = df[(df['rsi'] > 70) & (df['adx'] > 40)]
    wall_wr = steel_wall['outcome'].mean()
    
    print(f"Scenario: RSI > 70 + ADX > 40")
    print(f"  > Win Rate: {wall_wr:.2%}")
    print(f"  > Samples:  {len(steel_wall)}")
    print(f"  > Safety:   {'⛔ DANGER' if wall_wr < 0.3 else '✅ SAFE'}")

    # 3. THE SWEET SPOT HYPOTHESIS
    print("\n🚀 3. THE BIRTH OF MOMENTUM (High Vol + Rising ADX)")
    
    # Filter: ADX 20-30 AND Volatility > Median
    vol_median = df['atr_pct'].median()
    sweet_spot = df[(df['adx'] >= 20) & (df['adx'] <= 30) & (df['atr_pct'] > vol_median)]
    spot_wr = sweet_spot['outcome'].mean()
    
    print(f"Scenario: ADX [20-30] + High Volatility")
    print(f"  > Win Rate: {spot_wr:.2%}")
    print(f"  > Samples:  {len(sweet_spot)}")
    print(f"  > Lift:     {spot_wr - base_wr:+.2%}")

    print("="*60)

if __name__ == "__main__":
    backtest_adx()
