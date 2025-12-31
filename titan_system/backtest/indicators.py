import polars as pl
import numpy as np

def compute_rsi(expr, period=14):
    """
    Computes RSI using Polars expressions.
    Input: Polars Expression (pl.col("close"))
    Output: Polars Expression
    """
    delta = expr.diff()
    up = delta.clip(lower_bound=0)
    down = delta.clip(upper_bound=0).abs()

    # Exponential Moving Average for RSI
    # Note: Polars ewm_mean is available in newer versions
    roll_up = up.ewm_mean(span=period, adjust=False, min_periods=period)
    roll_down = down.ewm_mean(span=period, adjust=False, min_periods=period)
    
    rs = roll_up / roll_down
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi

def compute_sma(expr, period):
    return expr.rolling_mean(window_size=period)

def compute_ema(expr, period):
    return expr.ewm_mean(span=period, adjust=False)

def compute_cci(high, low, close, period=20):
    """Commodity Channel Index"""
    tp = (high + low + close) / 3
    sma_tp = tp.rolling_mean(window_size=period)
    # Mean Absolute Deviation
    mad = tp.rolling_map(lambda s: np.abs(s - s.mean()).mean(), window_size=period)
    cci = (tp - sma_tp) / (0.015 * mad)
    return cci

def compute_williams_r(high, low, close, period=14):
    """Williams %R"""
    hh = high.rolling_max(window_size=period)
    ll = low.rolling_min(window_size=period)
    wr = (hh - close) / (hh - ll) * -100
    return wr

def compute_stoch(high, low, close, k_period=14, d_period=3):
    """Stochastic Oscillator (%K and %D)"""
    ll = low.rolling_min(window_size=k_period)
    hh = high.rolling_max(window_size=k_period)
    k = (close - ll) / (hh - ll) * 100
    d = k.rolling_mean(window_size=d_period)
    return k, d

def compute_adx(high, low, close, period=14):
    """Average Directional Index (Simplified Polars)"""
    # True Range
    tr1 = high - low
    tr2 = (high - close.shift(1)).abs()
    tr3 = (low - close.shift(1)).abs()
    tr = pl.max_horizontal([tr1, tr2, tr3])
    
    # DM
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    
    pos_dm = pl.when((up_move > down_move) & (up_move > 0)).then(up_move).otherwise(0)
    neg_dm = pl.when((down_move > up_move) & (down_move > 0)).then(down_move).otherwise(0)
    
    # Smoothed
    atr = tr.ewm_mean(span=period, adjust=False)
    pos_di = 100 * (pos_dm.ewm_mean(span=period, adjust=False) / atr)
    neg_di = 100 * (neg_dm.ewm_mean(span=period, adjust=False) / atr)
    
    denom = pos_di + neg_di
    dx = pl.when(denom > 0).then(100 * (pos_di - neg_di).abs() / denom).otherwise(0)
    adx = dx.ewm_mean(span=period, adjust=False).fill_null(0)
    return adx
