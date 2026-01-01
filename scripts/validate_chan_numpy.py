"""
VALIDATE CHAN CONCEPTS ON LIVE MT5 DATA (No Statsmodels)
========================================================
Simplified validation script using pure Numpy to avoid environment issues.
Validates Transaction Costs, Stationarity (Hurst), and Half-Life.
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import math

mt5.initialize()

SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'US500', 'MTU', 'HGCOP-MAR26'] 

def find_symbol(base):
    all_syms = mt5.symbols_get()
    matches = [s.name for s in all_syms if base in s.name]
    if matches:
        if base in matches: return base
        return matches[0]
    return None

def get_data_df(symbol, timeframe=mt5.TIMEFRAME_D1, bars=2000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) < 100: return None
    df = pd.DataFrame(rates)
    return df

# --- METRIC 1: Transaction Costs vs Volatility ---
def check_costs(symbol):
    info = mt5.symbol_info(symbol)
    if not info: return None
    spread_pips = info.spread 
    point = info.point
    
    df = get_data_df(symbol, bars=14)
    if df is None: return None
    
    daily_range = (df['high'] - df['low']).mean()
    daily_range_pips = daily_range / point
    cost_impact = (spread_pips / daily_range_pips) * 100
    
    return {"Spread": spread_pips, "DailyRange": daily_range_pips, "Impact": cost_impact}

# --- METRIC 2: Hurst Exponent (Pure Numpy) ---
def get_hurst(ts):
    """Calculate the Hurst Exponent of the time series vector ts"""
    ts = np.array(ts)
    lags = range(2, 100)
    
    # Calculate the array of the variances of the lagged differences
    # variance(t) = avg|z(t+tau) - z(t)|^2
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    
    # Use a linear fit to estimate the Hurst Exponent
    # log(tau) = Hurst * log(lag) + C
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

# --- METRIC 3: Half Life (Manual OLS) ---
def get_half_life_manual(ts):
    """
    Calculate half-life via Ornstein-Uhlenbeck process using manual OLS.
    dy(t) = -lambda * y(t-1) * dt + ...
    """
    ts = np.array(ts)
    y_lag = ts[:-1]
    dy = ts[1:] - y_lag
    
    # Simple linear regression dy = alpha + beta * y_lag
    # beta is -lambda
    
    # Centering (optional but good for OLS) usually done by adding constant term
    A = np.vstack([y_lag, np.ones(len(y_lag))]).T
    beta, alpha = np.linalg.lstsq(A, dy, rcond=None)[0]
    
    lam = -beta
    if lam <= 0: return np.inf # Not mean reverting
    return np.log(2) / lam

def run_analysis():
    print(f"\n{'SYMBOL':<15} | {'COST%':<6} | {'HURST':<6} | {'HALF-LIFE':<10} | {'VERDICT':<20}")
    print("-" * 80)
    
    for base in SYMBOLS:
        sym = find_symbol(base)
        if not sym: continue
            
        costs = check_costs(sym)
        if not costs: continue
        
        df = get_data_df(sym, bars=2000)
        if df is None: continue
        log_prices = np.log(df['close'].values)
        
        hurst = get_hurst(log_prices)
        half_life = get_half_life_manual(log_prices)
        
        verdict = []
        if hurst > 0.5: verdict.append("TREND")
        else: verdict.append("MEAN-REV")
            
        if costs['Impact'] > 2.0: verdict.append("HIGH COST")
        
        # Chan's Profitability Rule: Cost% should be low, Trend/MR should be strong
        quality = "POOR"
        if verdict[0] == "TREND" and hurst > 0.52 and costs['Impact'] < 1.0: quality = "⭐⭐⭐"
        if verdict[0] == "MEAN-REV" and hurst < 0.48 and costs['Impact'] < 1.0: quality = "⭐⭐"
        
        final_v = f"{' '.join(verdict)} {quality}"
        
        print(f"{sym:<15} | {costs['Impact']:<6.2f} | {hurst:<6.2f} | {half_life:<10.1f} | {final_v}")

if __name__ == "__main__":
    run_analysis()
