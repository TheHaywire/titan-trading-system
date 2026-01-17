"""
HISTORY CLEANER
===============
Isolates institutional trades from account "noise".
"""

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timedelta

# Institutional Magic Number Ranges
INSTITUTIONAL_IDS = {
    888888: "Fleet Orchestrator",
    999000: "Titan Alpha (Factory)",
    123456: "Titan Genesis"
}

def get_cleaned_history(days=30, include_manual=False):
    if not mt5.initialize():
        return None
        
    from_date = datetime.now() - timedelta(days=days)
    deals = mt5.history_deals_get(from_date, datetime.now())
    
    if not deals:
        return pd.DataFrame()
        
    df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
    
    # Filter for Trades only (Type 0/1)
    df = df[df['type'].isin([0, 1])].copy()
    
    if not include_manual:
        # Keep only institutional IDs or known ranges
        df = df[
            (df['magic'].isin(INSTITUTIONAL_IDS.keys())) | 
            ((df['magic'] >= 999000) & (df['magic'] <= 999999))
        ]
        
    def label_source(magic):
        if magic == 0: return "Manual"
        if magic in INSTITUTIONAL_IDS: return INSTITUTIONAL_IDS[magic]
        if 999000 <= magic <= 999999: return "Titan Alpha"
        return "Unknown Bot"

    df['source'] = df['magic'].apply(label_source)
    return df

if __name__ == "__main__":
    df = get_cleaned_history(days=7)
    if not df.empty:
        print(f"--- CLEANED HISTORY (7 Days) ---")
        print(f"Total Inst. Trades: {len(df)}")
        print(df[['symbol', 'magic', 'source', 'profit']].tail(10).to_string(index=False))
    else:
        print("No institutional trades found in the last 7 days.")
    mt5.shutdown()
