"""
DYNAMIC KELLY ALLOCATOR
=======================
Institutional position sizing.
Calculates optimal volume based on Edge and Correlation.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json

def calculate_optimal_size(symbol, win_rate, reward_to_risk):
    # 1. Standard Kelly Criterion
    # Kelly % = (W - (1-W)/R)
    edge = (win_rate - (1 - win_rate) / reward_to_risk)
    fractional_kelly = edge * 0.25 # Half-Kelly for safety
    
    # 2. Correlation Multiplier (Simulated)
    # In production, we'd check current positions vs 'symbol'
    correlation_penalty = 1.0
    
    # Mock check
    if symbol in ["GOLD", "SILVER"]: 
        correlation_penalty = 0.5 # High correlation penalty
        
    final_allocation = max(0, fractional_kelly * correlation_penalty)
    
    # 3. Convert to Lots (Simulated)
    # Assume 100k account, 1% risk = 0.1 lots approximately
    suggested_lots = round(final_allocation * 5.0, 2) # Scaled lots
    
    return {
        "symbol": symbol,
        "win_rate": win_rate,
        "rr_ratio": reward_to_risk,
        "edge_index": round(edge, 3),
        "suggested_allocation_pct": round(final_allocation * 100, 2),
        "suggested_lots": max(0.01, suggested_lots)
    }

if __name__ == "__main__":
    # Test on GOLD with 40% win rate and 3:1 RR
    res = calculate_optimal_size("GOLD", 0.40, 3.0)
    print(json.dumps(res, indent=2))
