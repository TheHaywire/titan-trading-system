"""
TITAN RISK: MONTE CARLO SIMULATOR
=================================
Performs 10,000 simulations per active position to determine
real-time win/loss probability based on current price, SL, TP, and volatility.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
import sys

def get_volatility(symbol, timeframe=mt5.TIMEFRAME_M15, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['tr'] = np.maximum(df['high'] - df['low'], 
                          np.maximum(abs(df['high'] - df['close'].shift()), 
                                     abs(df['low'] - df['close'].shift())))
    return df['tr'].mean()

def run_simulation(symbol, current_price, sl, tp, type_str, volatility, iterations=10000):
    if not sl or not tp:
        return {"win_prob": 50.0, "loss_prob": 50.0, "ev": 0.0, "status": "No SL/TP"}

    # Daily volatility scale to simulation step (assume 1-minute steps for 10,000 steps max)
    # This is a random walk simulation
    dt = 1 # step
    mu = 0 # drift assumed zero for risk sim
    sigma = volatility / np.sqrt(100) # scale volatility to step size (heuristic)
    
    wins = 0
    losses = 0
    
    # Vectorized simulation
    # Simulate 10k paths simultaneously
    # For speed, we simulate the 'first touch' of SL or TP
    # Generate 10k random walks
    # We use a drift-diffusion model: dS = sigma * dW
    # where dW is standard normal
    
    # Create 100 steps for each of the 10,000 paths
    steps = 200
    random_moves = np.random.normal(mu, sigma, (iterations, steps))
    paths = current_price + np.cumsum(random_moves, axis=1)
    
    if type_str == "BUY":
        # First check where each path hits SL or TP
        hit_tp = np.any(paths >= tp, axis=1)
        hit_sl = np.any(paths <= sl, axis=1)
        
        # Determine which was hit first (approximate by index of hit)
        for i in range(iterations):
            if hit_tp[i] and hit_sl[i]:
                tp_idx = np.where(paths[i] >= tp)[0][0]
                sl_idx = np.where(paths[i] <= sl)[0][0]
                if tp_idx < sl_idx: wins += 1
                else: losses += 1
            elif hit_tp[i]: wins += 1
            elif hit_sl[i]: losses += 1
            else:
                # Path didn't hit either in 200 steps, check final direction
                if paths[i][-1] > current_price: wins += 1
                else: losses += 1
    else: # SELL
        hit_tp = np.any(paths <= tp, axis=1)
        hit_sl = np.any(paths >= sl, axis=1)
        
        for i in range(iterations):
            if hit_tp[i] and hit_sl[i]:
                tp_idx = np.where(paths[i] <= tp)[0][0]
                sl_idx = np.where(paths[i] >= sl)[0][0]
                if tp_idx < sl_idx: wins += 1
                else: losses += 1
            elif hit_tp[i]: wins += 1
            elif hit_sl[i]: losses += 1
            else:
                if paths[i][-1] < current_price: wins += 1
                else: losses += 1
                
    win_prob = (wins / iterations) * 100
    loss_prob = (losses / iterations) * 100
    
    # Calculate Expected Value
    risk = abs(current_price - sl)
    reward = abs(current_price - tp)
    ev = (win_prob/100 * reward) - (loss_prob/100 * risk)
    
    return {
        "win_prob": round(win_prob, 1),
        "loss_prob": round(loss_prob, 1),
        "ev": round(ev, 4),
        "status": "Success"
    }

def get_monte_carlo_results(standalone=True):
    if standalone:
        if not mt5.initialize():
            return {"error": "MT5 Init Failed"}
    
    positions = mt5.positions_get()
    results = {}
    
    if positions:
        for p in positions:
            vol = get_volatility(p.symbol)
            if vol is None: continue
            
            type_str = "BUY" if p.type == 0 else "SELL"
            results[p.ticket] = run_simulation(
                p.symbol, p.price_current, p.sl, p.tp, type_str, vol
            )
            results[p.ticket]["symbol"] = p.symbol
        
    if standalone:
        mt5.shutdown()
    return results

if __name__ == "__main__":
    data = get_monte_carlo_results()
    print(json.dumps(data, indent=4))
