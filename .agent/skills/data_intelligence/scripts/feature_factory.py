"""
FEATURE FACTORY
===============
Institutional feature engineering.
Automates TA-Lib integration and Fractal Quant metrics.
"""

import pandas as pd
import numpy as np
import ta
import json
import MetaTrader5 as mt5
from datetime import datetime

def calculate_hurst_exponent(ts):
    """Calculates the Hurst Exponent of a time series to determine its regime."""
    lags = range(2, 20)
    tau = [np.sqrt(np.std(np.subtract(ts[lag:], ts[:-lag]))) for lag in lags]
    poly = np.polyfit(np.log(lags), np.log(tau), 1)
    return poly[0] * 2.0

def build_feature_set(df):
    if df.empty or len(df) < 50:
        return df, {"status": "INSUFFICIENT_DATA"}
        
    df = df.copy()
    
    # 1. Momentum Indicators
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['stoch_k'] = ta.momentum.stoch(df['high'], df['low'], df['close'], window=14)
    
    # 2. Trend Indicators
    df['ema_fast'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema_slow'] = ta.trend.ema_indicator(df['close'], window=50)
    df['adx'] = ta.trend.adx(df['high'], df['low'], df['close'], window=14)
    
    # 3. Volatility Indicators
    bb = ta.volatility.BollingerBands(df['close'], window=20)
    df['bb_h'] = bb.bollinger_hband()
    df['bb_l'] = bb.bollinger_lband()
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)
    
    # 4. Fractal Quant (Hurst Exponent) - Calculated over rolling windows
    # Since Hurst is expensive, we do it for the last N candles
    hurst = calculate_hurst_exponent(df['close'].values[-100:])
    
    report = {
        "status": "COMPLETED",
        "features_generated": len(df.columns) - 8, # OHLCV + Time + TickVol + Spread = 8
        "latest_rsi": round(df['rsi'].iloc[-1], 2),
        "latest_adx": round(df['adx'].iloc[-1], 2),
        "hurst_exponent": round(hurst, 2),
        "regime_guess": "TRENDING" if hurst > 0.55 else ("MEAN_REVERTING" if hurst < 0.45 else "CHOP")
    }
    
    return df, report

if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Not Connected")
    else:
        rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_H1, 0, 500)
        if rates is not None:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df_feat, report = build_feature_set(df)
            print(json.dumps(report, indent=2))
        mt5.shutdown()
