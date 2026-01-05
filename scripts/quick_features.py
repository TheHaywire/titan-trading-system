"""Quick feature output demo"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')
import MetaTrader5 as mt5
import pandas as pd
from titan_system.features.quant_features import QuantFeatureEngine

mt5.initialize()
rates = mt5.copy_rates_from_pos('GOLD', mt5.TIMEFRAME_H1, 0, 500)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.rename(columns={'tick_volume': 'volume'}, inplace=True)

features_df = QuantFeatureEngine.compute_all(df)
latest = features_df.iloc[-1]
interp = QuantFeatureEngine.interpret(latest)
scores = QuantFeatureEngine.get_trading_score(latest)

print("GOLD LIVE INSTITUTIONAL FEATURES")
print("="*50)
print()
print("MARKET CHARACTER:")
print(f"  Hurst: {latest['hurst']:.3f}")
print(f"  Autocorr: {latest['return_autocorr']:.3f}")
print()
print("MOMENTUM:")
print(f"  ROC5: {latest['roc_5']:+.2f}%")
print(f"  ROC20: {latest['roc_20']:+.2f}%")
print(f"  Accel: {latest['price_accel']:+.2f}")
print()
print("MEAN REVERSION:")
print(f"  BB Pct: {latest['bb_percentile']:.2f}")
print(f"  RSI Pct: {latest['rsi_percentile']:.0f}")
print(f"  Z-Score: {latest['zscore_to_ma']:+.2f}")
print()
print("VOLATILITY:")
print(f"  HV: {latest['hist_volatility']:.1f}%")
print(f"  VoV: {latest['vol_of_vol']:.2f}")
print(f"  Regime: {latest['vol_regime']}")
print()
print("SCORES:")
print(f"  Trend: {scores['trend_strength']:.0f}/100")
print(f"  Reversion: {scores['reversion_opportunity']:.0f}/100")
print(f"  Risk: {scores['risk_level']:.0f}/100")
print(f"  Size Mult: {scores['size_multiplier']:.2f}x")
print()
print("INTERPRETATIONS:")
for k, v in interp.items():
    print(f"  {v}")
