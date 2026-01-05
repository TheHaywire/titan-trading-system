"""
Simple Feature Demo - Text Output
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
from titan_system.features.quant_features import QuantFeatureEngine

# Connect
mt5.initialize()
rates = mt5.copy_rates_from_pos('GOLD', mt5.TIMEFRAME_H1, 0, 500)
mt5.shutdown()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.rename(columns={'tick_volume': 'volume'}, inplace=True)

last_time = df['time'].iloc[-1]
last_close = df['close'].iloc[-1]
print(f"GOLD H1 | {len(df)} bars | Latest: {last_time} | Close: ${last_close:.2f}")
print("="*70)

# Compute features
features_df = QuantFeatureEngine.compute_all(df)
latest = features_df.iloc[-1]
interp = QuantFeatureEngine.interpret(latest)
scores = QuantFeatureEngine.get_trading_score(latest)

print("\n" + "="*70)
print("MARKET CHARACTER")
print("="*70)
h = latest.get('hurst', 0.5)
h_status = 'TRENDING' if h > 0.55 else ('MEAN-REVERTING' if h < 0.45 else 'RANDOM')
print(f"  Hurst Exponent:      {h:.3f}  --> {h_status}")
print(f"  Return Autocorr:     {latest.get('return_autocorr', 0):.3f}")
print(f"")
print(f"  --> {interp.get('market_character', '')}")
print(f"  --> {interp.get('strategy_fit', '')}")

print("\n" + "="*70)
print("MOMENTUM FEATURES")
print("="*70)
print(f"  ROC 5-bar:           {latest.get('roc_5', 0):+.2f}%")
print(f"  ROC 10-bar:          {latest.get('roc_10', 0):+.2f}%")
print(f"  ROC 20-bar:          {latest.get('roc_20', 0):+.2f}%")
print(f"  Price Acceleration:  {latest.get('price_accel', 0):+.2f}")
print(f"")
print(f"  --> {interp.get('momentum_action', '')}")

print("\n" + "="*70)
print("MEAN REVERSION FEATURES")
print("="*70)
print(f"  BB Percentile:       {latest.get('bb_percentile', 0.5):.2f}  (0=low band, 1=high band)")
print(f"  RSI Percentile:      {latest.get('rsi_percentile', 50):.0f}th")
print(f"  Z-Score to MA50:     {latest.get('zscore_to_ma', 0):+.2f} sigma")
print(f"")
print(f"  --> {interp.get('reversion_signal', '')}")

print("\n" + "="*70)
print("VOLATILITY & RISK")
print("="*70)
print(f"  Historical Vol:      {latest.get('hist_volatility', 0):.1f}% annualized")
print(f"  Vol of Vol:          {latest.get('vol_of_vol', 0):.2f}")
print(f"  Vol Regime:          {latest.get('vol_regime', 'MEDIUM')} ({latest.get('vol_percentile', 50):.0f}th pct)")
print(f"")
print(f"  --> {interp.get('vol_action', '')}")

print("\n" + "="*70)
print("ACTIONABLE TRADING SCORES")
print("="*70)
print(f"  Trend Strength:         {scores.get('trend_strength', 0):.0f}/100")
print(f"  Reversion Opportunity:  {scores.get('reversion_opportunity', 0):.0f}/100")
print(f"  Risk Level:             {scores.get('risk_level', 50):.0f}/100")
print(f"")
print(f"  >>> Position Size Multiplier: {scores.get('size_multiplier', 1.0):.2f}x <<<")

print("\n" + "="*70)
print("HOW TO USE THESE FOR PROFIT")
print("="*70)
print("""
1. ENTRY DECISIONS:
   - Hurst > 0.55 + Trend Score > 60 --> Use BREAKOUT entries
   - Hurst < 0.45 + BBP at extremes --> Use FADE/REVERSION entries
   - Autocorr positive --> Follow momentum, don't counter-trend

2. POSITION SIZING:
   - Apply the size multiplier to your base lot size
   - E.g., if base = 0.1 lots and multiplier = 0.75x --> use 0.075 lots
   
3. SCALING IN/OUT:
   - Acceleration POSITIVE --> You can ADD to winners
   - Acceleration flipping NEGATIVE --> TAKE partial profits
   - BBP hitting extremes (>0.9 or <0.1) --> Take profits on trends

4. STOP PLACEMENT:
   - HIGH vol regime --> Use WIDER stops (volatility will whipsaw you)
   - LOW vol regime --> Can use TIGHTER stops
   - HIGH Vol-of-Vol --> Market is unstable, be cautious
""")
