"""
SENSITIVITY ANALYZER
====================
Detects 'fragile' strategies.
Analyzes how minor parameter changes affect Alpha.
"""

import pandas as pd
import numpy as np
import json
import matplotlib.pyplot as plt
import os

def analyze_sensitivity(strategy_id, current_params, variance=0.2):
    """
    Simulates parameter perturbations.
    """
    report = {
        "strategy": strategy_id,
        "base_params": current_params,
        "perturbations": []
    }
    
    base_perf = 100.0 # Normalized base
    stability_sum = 0
    
    for param, val in current_params.items():
        if not isinstance(val, (int, float)): continue
        
        # Perturb up/down
        p_up = val * (1 + variance)
        p_down = val * (1 - variance)
        
        # Mock performance impact
        # In production, this would re-run the backtest
        perf_up = base_perf * np.random.uniform(0.8, 1.1)
        perf_down = base_perf * np.random.uniform(0.7, 1.0)
        
        stability = (perf_up + perf_down) / (2 * base_perf)
        stability_sum += stability
        
        report["perturbations"].append({
            "parameter": param,
            "val_up": round(p_up, 2),
            "perf_up_index": round(perf_up, 2),
            "val_down": round(p_down, 2),
            "perf_down_index": round(perf_down, 2),
            "stability_index": round(stability, 2)
        })
        
    avg_stability = stability_sum / len(report["perturbations"]) if report["perturbations"] else 0
    
    report["avg_stability"] = round(avg_stability, 2)
    report["verdict"] = "STABLE" if avg_stability > 0.85 else "FRAGILE"
    
    return report

if __name__ == "__main__":
    # Test on a hypothetical Gold Breakout strategy
    params = {"ema_fast": 20, "ema_slow": 50, "atr_mult": 2.5}
    report = analyze_sensitivity("GOLD_BREAKOUT_V2", params)
    print(json.dumps(report, indent=2))
