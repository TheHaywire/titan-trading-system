import polars as pl
import numpy as np
from titan_system.backtest.indicators import (
    compute_rsi, compute_cci, compute_williams_r, 
    compute_stoch, compute_adx
)

def compute_features(df: pl.DataFrame, version="v2"):
    """
    Converts raw OHLCV data into a normalized feature matrix for the AI.
    Features (v2):
    1-4. Original (RSI, Trend, Vol, ROC)
    5. CCI - Normalized [0, 1] (Clipped at +/- 200)
    6. Williams %R - Normalized [0, 1]
    7. Stochastic %K - Normalized [0, 1]
    8. ADX - Normalized [0, 1]
    9. True Range (Volatility) - Log Normalized
    10. Distance from High (Pullback indicator)
    
    Returns:
        pl.DataFrame including feature columns
        np.ndarray: The feature matrix (Rows x Features)
    """
    
    # 1. Base Indicators
    rsi = compute_rsi(df['close'], period=14) / 100.0
    
    ema_200 = df['close'].ewm_mean(span=200, adjust=False)
    trend_dist = (df['close'] / ema_200).log().fill_null(0).clip(-0.05, 0.05) * 20.0
    
    volatility = (df['high'] - df['low']) / df['close']
    vol_norm = volatility.rolling_mean(14).fill_null(0) * 100
    
    roc = df['close'].pct_change(n=5).fill_null(0) * 100
    
    # NEW v2 FEATURES
    # 5. CCI (Normalized -200 to 200 -> 0 to 1)
    cci = compute_cci(df['high'], df['low'], df['close'], period=20)
    cci_norm = ((cci.clip(-200, 200) + 200) / 400.0).fill_null(0.5)
    
    # 6. Williams %R (-100 to 0 -> 0 to 1)
    wr = compute_williams_r(df['high'], df['low'], df['close'], period=14)
    wr_norm = ((wr + 100) / 100.0).fill_null(0.5)
    
    # 7. Stochastic %K (0 to 100 -> 0 to 1)
    stoch_k, _ = compute_stoch(df['high'], df['low'], df['close'], k_period=14)
    stoch_norm = (stoch_k / 100.0).fill_null(0.5)
    
    # 8. ADX (0 to 100 -> 0 to 1)
    adx = compute_adx(df['high'], df['low'], df['close'], period=14)
    adx_norm = (adx / 100.0).fill_null(0)
    
    # 9. Pullback (Distance from 20-period High)
    hi_20 = df['high'].rolling_max(window_size=20)
    pullback = (df['close'] / hi_20).log().fill_null(0).clip(-0.05, 0) * -20.0
    
    # Construct Feature DataFrame
    df_features = df.with_columns([
        rsi.alias("f_rsi"),
        trend_dist.alias("f_trend"),
        vol_norm.alias("f_vol"),
        roc.alias("f_roc"),
        cci_norm.alias("f_cci"),
        wr_norm.alias("f_wr"),
        stoch_norm.alias("f_stoch"),
        adx_norm.alias("f_adx"),
        pullback.alias("f_pullback")
    ])
    
    # Clean NaNs (Drop initial warming period)
    df_clean = df_features.drop_nulls()
    
    # Selective Columns based on version (Backward Compatibility)
    if version == "v1":
        feature_cols = ["f_rsi", "f_trend", "f_vol", "f_roc"]
    else:
        feature_cols = ["f_rsi", "f_trend", "f_vol", "f_roc", "f_cci", "f_wr", "f_stoch", "f_adx", "f_pullback"]
    
    # Convert to Numpy Matrix
    matrix = df_clean.select(feature_cols).to_numpy()
    
    return df_clean, matrix
