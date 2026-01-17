import pandas as pd
import numpy as np

DATA_PATH = "data/general_market_scenarios_v2.csv"

def backtest_volatility():
    print("="*60)
    print("🧪 BACKTEST: THE PHYSICS OF VOLATILITY (ATR%)")
    print("="*60)
    
    try:
        df = pd.read_csv(DATA_PATH)
    except FileNotFoundError:
        print(f"❌ Error: Data file {DATA_PATH} not found.")
        return

    # De-normalize
    base_wr = df['outcome'].mean()
    print(f"📊 Total Baseline Win Rate: {base_wr:.2%} (N={len(df)})")
    
    # ATR is usually small float, like 0.001 (0.1%). Let's maintain raw values.
    # Convert to % for readability
    df['vol_readable'] = df['atr_pct'] * 100

    print("-" * 60)

    # 1. THE VOLATILITY ZONES
    print("\n🔍 1. VOLATILITY ZONES (The Gas Pedal)")
    # Zones: Dead, Low, Medium, High, Extreme
    # Based on rough ATR% distributions for Forex/Gold
    bins = [0, 0.05, 0.1, 0.2, 0.3, 0.5, 5.0]
    labels = ['Dead (<0.05%)', 'Low (0.05-0.1%)', 'Normal (0.1-0.2%)', 'High (0.2-0.3%)', 'Extreme (0.3-0.5%)', 'Crisis (>0.5%)']
    
    df['vol_zone'] = pd.cut(df['vol_readable'], bins=bins, labels=labels)
    stats = df.groupby('vol_zone')['outcome'].agg(['mean', 'count'])
    stats['lift'] = stats['mean'] - base_wr
    
    # Format output
    print(f"{'Zone':<20} | {'Win Rate':<10} | {'Lift':<10} | {'Samples':<10}")
    print("-" * 60)
    for index, row in stats.iterrows():
        print(f"{index:<20} | {row['mean']:.2%}   | {row['lift']:+.2%}   | {row['count']:<10}")
        
    # 2. THE DEAD MARKET HYPOTHESIS
    print("\n☠️ 2. THE DEAD MARKET (ATR < 0.05%)")
    dead_market = df[df['vol_readable'] < 0.05]
    dead_wr = dead_market['outcome'].mean()
    
    print(f"Scenario: ATR% < 0.05%")
    print(f"  > Win Rate: {dead_wr:.2%}")
    print(f"  > Lift:     {dead_wr - base_wr:+.2%}")
    print(f"  > Status:   {'⛔ AVOID' if dead_wr < base_wr else '✅ SAFE'}")
    
    # 3. THE HIGH OCTANE HYPOTHESIS
    print("\n🚀 3. THE HIGH OCTANE (ATR > 0.2%)")
    high_vol = df[df['vol_readable'] > 0.2]
    high_wr = high_vol['outcome'].mean()
    
    print(f"Scenario: ATR% > 0.2%")
    print(f"  > Win Rate: {high_wr:.2%}")
    print(f"  > Lift:     {high_wr - base_wr:+.2%}")
    print(f"  > Status:   {'✅ TARGET' if high_wr > base_wr else '⛔ AVOID'}")

    print("="*60)

if __name__ == "__main__":
    backtest_volatility()
