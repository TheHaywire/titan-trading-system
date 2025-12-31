
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import settings
from titan_system.math_core.regression import LinearRegressionChannel
from titan_system.math_core.statistics import StatisticalMetrics

def visualize(symbol="GOLD"):
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    # Get Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
    df = pd.DataFrame(rates)
    
    closes = df['close'].values
    
    # Run Math
    reg = LinearRegressionChannel(period=100)
    stats = reg.calculate(closes)
    
    # Half Life Calc
    expected_prices = stats['slope'] * np.arange(len(closes)) + stats['intercept']
    # stats['slope'] calculated on last 100, we need to be careful matching lengths
    # Reg class uses last 100.
    y = closes[-100:]
    x = np.arange(100)
    line = stats['slope'] * x + stats['intercept']
    residuals = y - line
    
    half_life = StatisticalMetrics.calculate_half_life(residuals)
    
    current_price = closes[-1]
    
    print(f"\n📊 QUANTITATIVE ANALYSIS: {symbol} (H1 Frame)")
    print("="*50)
    print(f"Current Price    : {current_price:.2f}")
    print(f"Regression Mean  : {stats['expected_price']:.2f} (Fair Value)")
    print(f"Slope (Trend)    : {stats['slope']:.4f}")
    print(f"Volatility (Std) : {stats['std_dev']:.2f}")
    print("="*50)
    print(f"HALF-LIFE        : {half_life:.1f} Bars (Reversion Speed)")
    print(f"Z-SCORE          : {stats['z_score']:.2f} σ")
    print("="*50)
    
    # Ascii Plot
    print("\n   [Sell Zone > +2.0]")
    print(f"   +2.0 Sigma : {stats['upper_2std']:.2f}")
    
    # Where are we?
    scale = [" ", " ", " ", " ", " "]
    if stats['z_score'] > 2: pos = 0
    elif stats['z_score'] > 1: pos = 1
    elif stats['z_score'] > -1: pos = 2
    elif stats['z_score'] > -2: pos = 3
    else: pos = 4
    
    scale[pos] = "<-- YOU ARE HERE"
    
    print(f"   +1.0 Sigma : {stats['expected_price'] + stats['std_dev']:.2f}   {scale[1]}")
    print(f"   MEAN LINE  : {stats['expected_price']:.2f}   {scale[2]}")
    print(f"   -1.0 Sigma : {stats['expected_price'] - stats['std_dev']:.2f}   {scale[3]}")
    print(f"   -2.0 Sigma : {stats['lower_2std']:.2f}")
    print("   [Buy Zone < -2.0]")
    
    if pos == 0: print(f"\n🔴 SIGNAL: OVERBOUGHT (Z={stats['z_score']:.2f})")
    elif pos == 4: print(f"\n🟢 SIGNAL: OVERSOLD (Z={stats['z_score']:.2f})")
    else: print(f"\n⚪ SIGNAL: FAIR VALUE (Neutral)")

    mt5.shutdown()

if __name__ == "__main__":
    visualize("GOLD")
