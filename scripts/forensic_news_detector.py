import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime

def run_forensic_audit():
    print("🕵️ STARTING FORENSIC NEWS DETECTOR...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    # Fetch 6 years of H1 data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 40000)
    mt5.shutdown()
    
    if rates is None:
        print("No data found.")
        return
        
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df['range'] = df['high'] - df['low']
    df['range_pips'] = df['range'] * 10 # Approx 
    
    # Sort by Volatility (Range)
    top_moves = df.sort_values(by='range', ascending=False).head(20)
    
    print(f"\n🚨 TOP 20 VOLATILITY EVENTS (2020-2026) for {symbol}:")
    print("These are the 'Explosions' that blow up accounts.\n")
    print(f"{'Date':<12} | {'Time (UTC)':<10} | {'Range ($)':<10} | {'Likely Cause'}")
    print("-" * 60)
    
    for i, row in top_moves.iterrows():
        date_str = row['time'].strftime('%Y-%m-%d')
        time_str = row['time'].strftime('%H:%M')
        range_val = f"${row['range']:.2f}"
        
        # Heuristic for Likely Cause based on Time
        hour = row['time'].hour
        minute = row['time'].minute
        
        cause = "Unknown"
        if hour in [12, 13, 14, 15]: 
            cause = "🇺🇸 NFP / CPI / FOMC"
        elif hour in [0, 1]: 
            cause = "🌏 War / Asian Open"
        elif hour in [7, 8, 9]:
            cause = "🇪🇺 ECB / London Open"
            
        print(f"{date_str:<12} | {time_str:<10} | {range_val:<10} | {cause}")

    print("\n💡 VERDICT:")
    print("If these events cluster around 13:00-15:00, our 'News Proxy' is valid.")
    print("The Market *Price* tells us when the news happened.")

if __name__ == "__main__":
    run_forensic_audit()
