
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from config.settings import settings

def find_levels(symbol="GOLD"):
    if not mt5.initialize():
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    # Get H4 Data for Structural Levels
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H4, 0, 500)
    df = pd.DataFrame(rates)
    
    # Simple fractal-based support/resistance
    # A low surrounded by higher lows is Support
    # A high surrounded by lower highs is Resistance
    
    window = 5
    df['is_low'] = df['low'].rolling(window=window*2+1, center=True).min() == df['low']
    df['is_high'] = df['high'].rolling(window=window*2+1, center=True).max() == df['high']
    
    supports = df[df['is_low']]['low'].values
    resistances = df[df['is_high']]['high'].values
    
    current_price = mt5.symbol_info_tick(symbol).bid
    
    # Find nearest
    valid_supports = supports[supports < current_price]
    valid_resistances = resistances[resistances > current_price]
    
    nearest_support = valid_supports[-1] if len(valid_supports) > 0 else 0
    nearest_resistance = valid_resistances[-1] if len(valid_resistances) > 0 else 0
    
    print(f"\n🔬 STRUCTURE ANALYSIS ({symbol})")
    print(f"   Current Price: {current_price:.2f}")
    print(f"   🧱 Nearest Support: {nearest_support:.2f} (Dist: {current_price - nearest_support:.2f})")
    print(f"   🧗 Nearest Resistance: {nearest_resistance:.2f} (Dist: {nearest_resistance - current_price:.2f})")
    
    # Suggest SL/TP
    # SL below Support
    # TP at Resistance
    
    suggested_sl = nearest_support - 5.0 # buffer
    suggested_tp = nearest_resistance - 2.0 # buffer
    
    print(f"\n🛡️ MANAGEMENT PLAN")
    print(f"   Suggested SL: {suggested_sl:.2f}")
    print(f"   Suggested TP: {suggested_tp:.2f}")

    mt5.shutdown()

if __name__ == "__main__":
    find_levels()
