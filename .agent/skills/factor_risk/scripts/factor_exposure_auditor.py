"""
FACTOR EXPOSURE AUDITOR
=======================
Institutional risk decomposition.
Identifies "Hidden Factors" and cross-symbol correlations using PCA.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from sklearn.decomposition import PCA
from datetime import datetime, timedelta
import json
import os
import sys

# Import the MT5 Bridge
bridge_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../mt5_bridge/scripts"))
sys.path.append(bridge_path)
from connectivity_manager import get_system_health

def get_positions_data():
    health = get_system_health()
    if health['status'] != "CONNECTED":
        return None
    
    positions = mt5.positions_get()
    if not positions:
        mt5.shutdown()
        return None
    
    pos_list = []
    for p in positions:
        pos_list.append({
            "symbol": p.symbol,
            "type": "BUY" if p.type == 0 else "SELL",
            "volume": p.volume,
            "price_open": p.price_open
        })
    return pos_list

def perform_factor_audit(lookback_days=30):
    positions = get_positions_data()
    if not positions:
        return {"status": "No active positions to audit."}
    
    symbols = list(set([p['symbol'] for p in positions]))
    data = {}
    
    # Fetch returns data
    utc_from = datetime.now() - timedelta(days=lookback_days)
    for sym in symbols:
        rates = mt5.copy_rates_from(sym, mt5.TIMEFRAME_H1, datetime.now(), lookback_days * 24)
        if rates is not None:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)
            data[sym] = df['close'].pct_change().dropna()
    
    mt5.shutdown()
    
    if not data:
        return {"error": "Could not fetch historical returns for factor analysis."}
    
    returns_df = pd.concat(data.values(), axis=1, keys=data.keys()).dropna()
    
    if returns_df.empty or len(returns_df.columns) < 2:
        return {
            "status": "Insufficient overlap or symbol count for factor decomposition.",
            "symbols_active": symbols
        }
    
    # 1. Correlation Matrix
    corr = returns_df.corr()
    
    # 2. PCA (Factor Decomposition)
    pca = PCA(n_components=min(len(symbols), 3))
    pca.fit(returns_df)
    
    # Explain Variance (High variance in PC1 usually means a single macro driver like USD)
    explained_variance = pca.explained_variance_ratio_.tolist()
    
    # Identify which symbols contribute most to PC1
    loadings = pd.DataFrame(
        pca.components_[0], 
        index=returns_df.columns, 
        columns=['Factor1_Weight']
    )
    
    extreme_corrs = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            if abs(corr.iloc[i, j]) > 0.7:
                extreme_corrs.append({
                    "pair": f"{corr.columns[i]} / {corr.columns[j]}",
                    "correlation": round(corr.iloc[i, j], 2)
                })

    report = {
        "active_symbols": symbols,
        "pca_explained_variance": [round(v, 2) for v in explained_variance],
        "primary_factor_weights": loadings['Factor1_Weight'].round(2).to_dict(),
        "extreme_correlations": extreme_corrs,
        "verdict": "Concentrated Risk" if explained_variance[0] > 0.6 else "Well Diversified"
    }
    
    return report

if __name__ == "__main__":
    print(json.dumps(perform_factor_audit(), indent=2))
