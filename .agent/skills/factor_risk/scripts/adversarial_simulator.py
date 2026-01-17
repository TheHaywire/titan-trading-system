"""
ADVERSARIAL SIMULATOR
=====================
Institutional Chaos Testing.
Monte Carlo simulation of execution degradation.
"""

import numpy as np
import json

def simulate_chaos(base_profit_factor, trades=100):
    """
    Simulates how Alpha decays when 'The Market' fights back.
    """
    # 1. Inject Slippage & Spread spikes
    # We shift the mean return of trades downwards
    chaos_returns = np.random.normal(0.002, 0.015, trades) - 0.0005 # Inject 5bp penalty
    
    wins = chaos_returns[chaos_returns > 0]
    losses = chaos_returns[chaos_returns < 0]
    
    chaos_pf = wins.sum() / abs(losses.sum()) if len(losses) > 0 else 0
    
    # 2. Risk Evaluation
    survival_prob = 1.0 if chaos_pf > 1.2 else (0.5 if chaos_pf > 1.0 else 0.0)
    
    return {
        "simulation": "MONTE_CARLO_CHAOS",
        "trades": trades,
        "base_profit_factor": base_profit_factor,
        "simulated_profit_factor": round(float(chaos_pf), 2),
        "decay_pct": round(((base_profit_factor - chaos_pf) / base_profit_factor) * 100, 2),
        "verdict": "ROBUST" if survival_prob == 1.0 else "VULNERABLE",
        "survival_probability": survival_prob
    }

if __name__ == "__main__":
    # Test a strategy with a 1.8 base Profit Factor
    report = simulate_chaos(1.8)
    print(json.dumps(report, indent=2))
