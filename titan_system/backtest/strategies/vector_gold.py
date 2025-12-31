import polars as pl
from titan_system.backtest.indicators import compute_rsi

def institutional_gold_vector_strategy(df):
    """
    Vectorized implementation of Institutional Gold Strategy.
    
    Logic:
    1. Trend Filter: Use EMA 200 (M1) as proxy for higher timeframe bias.
       - Price > EMA 200 -> BULLISH Bias
       - Price < EMA 200 -> BEARISH Bias
    
    2. Execution Trigger: RSI (14)
       - BUY: Bullish Bias AND RSI < 25 (Oversold Dip)
       - SELL: Bearish Bias AND RSI > 75 (Overbought Rip)
    """
    
    # 1. Calculate Indicators
    # EMA 200 for Trend
    ema_200 = df['close'].ewm_mean(span=200, adjust=False)
    
    # RSI 14 for Momentum
    rsi = compute_rsi(df['close'], period=14)
    
    # 2. Define Logic Conditions
    bullish_bias = df['close'] > ema_200
    bearish_bias = df['close'] < ema_200
    
    oversold = rsi < 25.0
    overbought = rsi > 75.0
    
    # 3. Generate Signals
    # Polars `when` logic
    signal = pl.when(bullish_bias & oversold).then(1)\
               .when(bearish_bias & overbought).then(-1)\
               .otherwise(0)
               
    # 4. Filter Rapid Signals (Optional Cooldown)
    # For now, we accept every signal. The engine handles "one position at a time" implicitly
    # by how it calculates returns (shift logic).
    
    return df.with_columns(signal.alias("signal"))
