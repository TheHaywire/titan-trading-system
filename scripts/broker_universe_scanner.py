"""
Broker Universe Scanner - Institutional Grade
Scans MT5 for all available symbols, identifies tradeable assets, 
and extracts critical institutional properties.
"""

import MetaTrader5 as mt5
import json
import os
import pandas as pd
from datetime import datetime

def scan_universe():
    if not mt5.initialize():
        print("MT5 initialization failed")
        return None

    print("🛰️  Scanning Broker Universe (XM Global)...")
    
    # Get all symbols
    symbols = mt5.symbols_get()
    print(f"Total symbols found: {len(symbols)}")

    universe = []
    
    for s in symbols:
        s_dict = s._asdict()
        info = {
            "name": s_dict.get("name"),
            "path": s_dict.get("path"),
            "description": s_dict.get("description"),
            "basis": s_dict.get("basis"),
            "currency_base": s_dict.get("currency_base"),
            "currency_profit": s_dict.get("currency_profit"),
            "currency_margin": s_dict.get("currency_margin"),
            "digits": s_dict.get("digits"),
            "point": s_dict.get("point"),
            "tick_size": s_dict.get("trade_tick_size"),
            "tick_value": s_dict.get("trade_tick_value"),
            "contract_size": s_dict.get("trade_contract_size"),
            "volume_min": s_dict.get("volume_min"),
            "volume_max": s_dict.get("volume_max"),
            "volume_step": s_dict.get("volume_step"),
            "spread": s_dict.get("spread"),
            "swap_long": s_dict.get("swap_long"),
            "swap_short": s_dict.get("swap_short"),
            "margin_initial": s_dict.get("margin_initial"),
            "margin_maintenance": s_dict.get("margin_maintenance"),
            "trade_mode": s_dict.get("trade_mode"),
            "execution_mode": s_dict.get("filling_mode")
        }
        universe.append(info)

    mt5.shutdown()
    return universe

def organize_by_asset_class(universe):
    """Groups symbols by their MT5 path/category"""
    df = pd.DataFrame(universe)
    
    # Extract asset class from path (e.g., "Forex\Majors\EURUSD" -> "Forex")
    df['asset_class'] = df['path'].apply(lambda x: x.split('\\')[0] if '\\' in x else "Other")
    
    summary = {}
    for ac in df['asset_class'].unique():
        symbols_in_class = df[df['asset_class'] == ac]
        summary[ac] = {
            "count": len(symbols_in_class),
            "examples": list(symbols_in_class['name'].head(5))
        }
    
    return df, summary

if __name__ == "__main__":
    data = scan_universe()
    if data:
        df, summary = organize_by_asset_class(data)
        
        # Save complete data
        if not os.path.exists('data'):
            os.makedirs('data')
        
        df.to_csv('data/broker_universe_raw.csv', index=False, encoding='utf-8')
        
        # Save a clean JSON of tradeable symbols
        # trade_mode: 0=Disabled, 1=Long, 2=Short, 3=Close, 4=Full
        tradeable = df[df['trade_mode'] != 0] 
        tradeable_list = tradeable.to_dict(orient='records')
        with open('data/tradeable_universe.json', 'w', encoding='utf-8') as f:
            json.dump(tradeable_list, f, indent=4)

        print("\nScan Complete.")
        print("Summary by Asset Class:")
        for ac, info in summary.items():
            print(f"- {ac}: {info['count']} symbols.")
        
        # Output for README generation
        print("\nSaving markdown summary...")
        with open('docs/institutional/BROKER_SYMBOL_CATALOG.md', 'w', encoding='utf-8') as f:
            f.write("# Broker Symbol Catalog (Institutional)\n\n")
            f.write(f"**Scan Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Universe Summary\n\n")
            f.write("| Asset Class | Count | Examples |\n")
            f.write("|-------------|-------|----------|\n")
            for ac, info in summary.items():
                examples_str = ", ".join(info['examples']).replace("|", "\\|")
                f.write(f"| {ac} | {info['count']} | {examples_str} |\n")
            
            f.write("\n## Top Tradeable Instruments (Properties)\n\n")
            # Select some representative majors
            majors = ["EURUSD", "GBPUSD", "USDJPY", "GOLD", "XAUUSD", "US100", "BTCUSD"]
            sample = df[df['name'].isin(majors)]
            
            f.write("| Symbol | Contract Size | Tick Size | Swap Long | Swap Short |\n")
            f.write("|--------|---------------|-----------|-----------|------------|\n")
            for _, row in sample.iterrows():
                f.write(f"| {row['name']} | {row['contract_size']} | {row['tick_size']} | {row['swap_long']} | {row['swap_short']} |\n")
            
            f.write("\n\n*Full catalog available in `data/broker_universe_raw.csv`*")
