"""
Feature Engine Demo - Offline Mode
Shows what each feature means with example scenarios
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import pandas as pd
import numpy as np
from titan_system.features.quant_features import QuantFeatureEngine

# Create sample GOLD-like data
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=500, freq='H')
base_price = 2600

# Simulate a trending market (like current GOLD)
trend = np.linspace(0, 300, 500)
noise = np.random.randn(500) * 5
prices = base_price + trend + noise

df = pd.DataFrame({
    'time': dates,
    'open': prices + np.random.randn(500) * 2,
    'high': prices + abs(np.random.randn(500) * 3),
    'low': prices - abs(np.random.randn(500) * 3),
    'close': prices,
    'volume': np.random.randint(1000, 5000, 500)
})

print("="*70)
print("INSTITUTIONAL FEATURE ENGINE - DEMO")
print("="*70)
print(f"\nSimulated GOLD data: {len(df)} bars")
print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
print(f"Latest close: ${df['close'].iloc[-1]:.2f}")

# Compute features
print("\n[Computing features...]")
features_df = QuantFeatureEngine.compute_all(df)
latest = features_df.iloc[-1]
interp = QuantFeatureEngine.interpret(latest)
scores = QuantFeatureEngine.get_trading_score(latest)

print("\n" + "="*70)
print("MARKET CHARACTER - What type of market is this?")
print("="*70)
h = latest['hurst']
ac = latest['return_autocorr']
print(f"  Hurst Exponent:      {h:.3f}")
if h > 0.55:
    print(f"    → TRENDING market - Winners keep winning")
    print(f"    → USE: Breakouts, trend-following, trail stops")
elif h < 0.45:
    print(f"    → MEAN-REVERTING market - What goes up comes down")
    print(f"    → USE: Fade extremes, buy dips, sell rallies")
else:
    print(f"    → RANDOM market - No persistent pattern")
    print(f"    → USE: Reduce size, be selective")

print(f"\n  Return Autocorr:     {ac:.3f}")
if ac > 0.2:
    print(f"    → MOMENTUM REGIME - Trends persist")
    print(f"    → DON'T: Counter-trend trade")
elif ac < -0.2:
    print(f"    → REVERSION REGIME - Swings reverse")
    print(f"    → DON'T: Chase trends")
else:
    print(f"    → MIXED REGIME - No clear pattern")

print("\n" + "="*70)
print("MOMENTUM - Is price accelerating or decelerating?")
print("="*70)
print(f"  ROC 5-bar:           {latest['roc_5']:+.2f}%")
print(f"  ROC 10-bar:          {latest['roc_10']:+.2f}%")
print(f"  ROC 20-bar:          {latest['roc_20']:+.2f}%")
print(f"  Price Acceleration:  {latest['price_accel']:+.2f}")

if latest['roc_20'] > 0 and latest['price_accel'] > 0:
    print(f"\n  💡 TRADE ACTION: Momentum building → ADD to long positions")
elif latest['roc_20'] > 0 and latest['price_accel'] < 0:
    print(f"\n  💡 TRADE ACTION: Momentum fading → TAKE partial profits")
elif latest['roc_20'] < 0 and latest['price_accel'] < 0:
    print(f"\n  💡 TRADE ACTION: Downtrend accelerating → Stay short/out")
else:
    print(f"\n  💡 TRADE ACTION: Momentum shifting → Watch for reversal")

print("\n" + "="*70)
print("MEAN REVERSION - Is price stretched?")
print("="*70)
bbp = latest['bb_percentile']
rsi_pct = latest['rsi_percentile']
zscore = latest['zscore_to_ma']

print(f"  BB Percentile:       {bbp:.2f}")
print(f"    (0=lower band, 0.5=middle, 1=upper band)")
if bbp < 0.15:
    print(f"    → OVERSOLD - Price near lower band → Look for LONG entries")
elif bbp > 0.85:
    print(f"    → OVERBOUGHT - Price near upper band → Take profits/SHORT")
else:
    print(f"    → NEUTRAL - No extreme stretch")

print(f"\n  RSI Percentile:      {rsi_pct:.0f}th")
if rsi_pct < 20:
    print(f"    → Historically oversold for this symbol → STRONG long signal")
elif rsi_pct > 80:
    print(f"    → Historically overbought → STRONG short signal")
else:
    print(f"    → Normal range")

print(f"\n  Z-Score to MA(50):   {zscore:+.2f}σ")
if abs(zscore) > 2:
    print(f"    → Price is {abs(zscore):.1f} std devs from average")
    print(f"    → MEAN REVERSION trade opportunity")
    print(f"    → SIZE: Use SMALLER position (high snap-back risk)")

print("\n" + "="*70)
print("VOLATILITY & RISK - How dangerous is the market?")
print("="*70)
hv = latest['hist_volatility']
vov = latest['vol_of_vol']
regime = latest['vol_regime']
vol_pct = latest['vol_percentile']

print(f"  Historical Vol:      {hv:.1f}% annualized")
print(f"  Vol of Vol:          {vov:.2f}")
print(f"  Vol Regime:          {regime} ({vol_pct:.0f}th percentile)")

if regime == 'HIGH':
    print(f"\n  ⚠️  HIGH VOL → Reduce position size by 50%")
    print(f"      → Use WIDER stops (2x normal)")
    print(f"      → Market is whippy, expect false signals")
elif regime == 'LOW':
    print(f"\n  ✅ LOW VOL → Safe to size up positions")
    print(f"      → Can use TIGHTER stops")
    print(f"      → Mean-reversion strategies work well")
else:
    print(f"\n  ✓ NORMAL VOL → Standard position sizing OK")

print("\n" + "="*70)
print("ACTIONABLE SCORES - What should I do RIGHT NOW?")
print("="*70)
trend_score = scores['trend_strength']
rev_score = scores['reversion_opportunity']
risk_score = scores['risk_level']
size_mult = scores['size_multiplier']

print(f"  Trend Strength:         {trend_score:.0f}/100")
print(f"  Reversion Opportunity:  {rev_score:.0f}/100")
print(f"  Risk Level:             {risk_score:.0f}/100")
print(f"\n  🎯 Position Size Multiplier: {size_mult:.2f}x")
print(f"     Example: Base = 0.10 lots → Use {0.10 * size_mult:.3f} lots")

print("\n" + "="*70)
print("FINAL RECOMMENDATION")
print("="*70)

if trend_score > 60 and risk_score < 50:
    print("✅ TREND ENVIRONMENT")
    print("   → Use breakout entries")
    print("   → Trail stops, let winners run")
    print("   → Don't fade moves")
elif rev_score > 60 and risk_score < 50:
    print("🔄 REVERSION SETUP")
    print("   → Fade extremes (BBP > 0.85 or < 0.15)")
    print("   → Take QUICK profits")
    print("   → Tight stops")
elif risk_score > 70:
    print("⚠️  HIGH RISK")
    print("   → REDUCE size or sit out")
    print("   → Volatility too high")
else:
    print("◐ MIXED CONDITIONS")
    print("   → Be selective")
    print("   → Smaller positions")
    print("   → Wait for clearer setups")

print("\n" + "="*70)
print("HOW TO USE FOR MAXIMUM PROFIT")
print("="*70)
print("""
STEP 1: Check market character (Hurst)
  → Trending? Use breakouts
  → Mean-reverting? Fade extremes

STEP 2: Confirm with momentum (ROC, Acceleration)
  → Acceleration positive? Add to winners
  → Acceleration negative? Take profits

STEP 3: Size your position
  → Multiply your base lot by the size multiplier
  → High vol = smaller size, Low vol = larger size

STEP 4: Set your stops
  → High vol regime = 2x wider stops
  → Low vol regime = normal stops

STEP 5: Manage the trade
  → Watch BBP: If it hits extremes (>0.9), take partial profits
  → Watch acceleration: If it flips, tighten stops
  → Watch Hurst: If regime changes, exit
""")
