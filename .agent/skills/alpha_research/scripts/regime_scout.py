"""
REGIME SCOUT
============
Institutional market state classification.
Detects Trending vs Mean-Reverting vs Volatile regimes.
"""

import pandas as pd
import numpy as np
import json
import MetaTrader5 as mt5
from datetime import datetime

def classify_regime(df):
    if df.empty or len(df) < 100:
        return {"status": "INSUFFICIENT_DATA"}
        
    df = df.copy()
    
    # 1. Trend Factor (ADX + EMA Alignment)
    # Using simple proxies for speed
    df['returns'] = df['close'].pct_change()
    volatility = df['returns'].std() * np.sqrt(252)
    
    # 2. Hurst Exponent (Trendiness)
    def get_hurst(ts):
        lags = range(2, 20)
        tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
        poly = np.polyfit(np.log(lags), np.log(tau), 1)
        return poly[0] * 2.0
        
    hurst = get_hurst(df['close'].values[-100:])
    
    # 3. Decision Matrix
    regime = "CHOP"
    color = "yellow"
    
    if hurst > 0.58:
        regime = "TRENDING"
        color = "green"
    elif hurst < 0.42:
        regime = "MEAN_REVERTING"
        color = "blue"
    
    # Volatility Check
    if volatility > 0.25: # High Vol
        regime = f"VOLATILE_{regime}"
        color = "red"

    return {
        "timestamp": datetime.now().isoformat(),
        "hurst_exponent": round(float(hurst), 2),
        "annualized_vol": round(float(volatility), 4),
        "regime": regime,
        "color_code": color,
        "action": "FAVORS_BREAKOUTS" if "TRENDING" in regime else "FAVORS_SCALPING"
    }

if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Not Connected")
    else:
        # Test on BTCUSD
        rates = mt5.copy_rates_from_pos("BTCUSD", mt5.TIMEFRAME_H1, 0, 500)
        if rates is not None:
            df = pd.DataFrame(rates)
            report = classify_regime(df)
            print(json.dumps(report, indent=2))
        mt5.shutdown()
