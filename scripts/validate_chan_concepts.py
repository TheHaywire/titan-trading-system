"""
VALIDATE CHAN CONCEPTS ON LIVE MT5 DATA
=======================================
Validating core concepts from 'Algorithmic Trading' book against 
the user's specific MT5 environment.

Tests:
1. Transaction Cost Analysis (Spread vs Volatility)
2. Stationarity (ADF Test) - Can we trade Mean Reversion?
3. Hurst Exponent - Is it Trending or Mean Reverting?
4. Half-Life - What is the optimal lookback?
5. Cointegration - Do Gold/Silver move together?

"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller

mt5.initialize()

SYMBOLS = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 'US500', 'MTU', 'HGCOP-MAR26'] 
# Note: Using generic XAUUSD/BTCUSD for broader checks, plus specific futures if found

def find_symbol(base):
    # Helper to find the best matching symbol in user's terminal
    all_syms = mt5.symbols_get()
    matches = [s.name for s in all_syms if base in s.name]
    # Prefer exact or close matches
    if matches:
        # If precise match exists (e.g. 'EURUSD'), take it
        if base in matches: return base
        return matches[0]
    return None

def get_log_prices(symbol, bars=2000):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, bars)
    if rates is None or len(rates) < 100: return None
    df = pd.DataFrame(rates)
    return np.log(df['close'])

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
    
    # Calculate Daily Volatility (ATR-like)
    df = get_data_df(symbol, bars=14)
    if df is None: return None
    
    daily_range = (df['high'] - df['low']).mean()
    daily_range_pips = daily_range / point
    
    cost_impact = (spread_pips / daily_range_pips) * 100
    
    return {
        "Spread": spread_pips,
        "DailyRange": daily_range_pips,
        "Impact": cost_impact
    }

# --- METRIC 2: Hurst Exponent ---
def get_hurst(time_series):
    """Returns the Hurst Exponent of the time series vector ts"""
    # Create the range of lag values
    lags = range(2, 100)
    
    # Calculate the array of the variances of the lagged differences
    tau = [np.sqrt(np.std(np.subtract(time_series[lag:], time_series[:-lag]))) for lag in lags]
    
    # Use a linear fit to estimate the Hurst Exponent
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    
    return poly[0]*2.0 

# --- METRIC 3: Half Life ---
def get_half_life(time_series):
    # Delta price
    ts = pd.Series(time_series)
    delta_ts = ts.diff().dropna()
    ts_lag = ts.shift(1).dropna()
    
    # Align
    ts_lag = ts_lag.iloc[-len(delta_ts):]
    
    # Regress delta vs lag
    res = sm.OLS(delta_ts, sm.add_constant(ts_lag)).fit()
    lam = res.params.iloc[1]
    
    if lam >= 0: return np.inf # Not mean reverting
    return -np.log(2) / lam

# --- METRIC 4: ADF Test ---
def check_stationarity(time_series):
    result = adfuller(time_series)
    return result[1] # p-value

def run_analysis():
    print(f"{'SYMBOL':<10} | {'COST%':<6} | {'HURST':<6} | {'ADF(p)':<6} | {'HALF-LIFE':<10} | {'VERDICT':<20}")
    print("-" * 80)
    
    for base in SYMBOLS:
        sym = find_symbol(base)
        if not sym: 
            # Try finding related
            continue
            
        # Costs
        costs = check_costs(sym)
        if not costs: continue
        
        # Math checks
        log_prices = get_log_prices(sym)
        if log_prices is None: continue
        
        hurst = get_hurst(log_prices.values)
        adf_p = check_stationarity(log_prices.values)
        half_life = get_half_life(log_prices.values)
        
        # Verdict Logic per Chan
        verdict = []
        if hurst > 0.55: verdict.append("TREND")
        if hurst < 0.45: verdict.append(f"MR (HL={int(half_life)})")
        if costs['Impact'] > 5.0: verdict.append("EXPENSIVE")
        
        final_v = "+".join(verdict) if verdict else "RANDOM WALK"
        
        print(f"{sym:<10} | {costs['Impact']:<5.2f}% | {hurst:<6.2f} | {adf_p:<6.2f} | {half_life:<10.1f} | {final_v}")

if __name__ == "__main__":
    run_analysis()
