"""
Feature Engine Demo - Clean ASCII Output
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import pandas as pd
import numpy as np
from titan_system.features.quant_features import QuantFeatureEngine

# Create sample GOLD-like trending data
np.random.seed(42)
dates = pd.date_range('2024-01-01', periods=500, freq='H')
base_price = 2600
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
print("INSTITUTIONAL FEATURE ENGINE - COMPLETE EXAMPLE")
print("="*70)
print(f"Simulated GOLD H1 data: {len(df)} bars")
print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
print(f"Latest close: ${df['close'].iloc[-1]:.2f}\n")

# Compute all features
features_df = QuantFeatureEngine.compute_all(df)
latest = features_df.iloc[-1]
interp = QuantFeatureEngine.interpret(latest)
scores = QuantFeatureEngine.get_trading_score(latest)

print("="*70)
print("1. MARKET CHARACTER - What type of market is this?")
print("="*70)
h = latest['hurst']
ac = latest['return_autocorr']

print(f"Hurst Exponent:      {h:.3f}")
if h > 0.55:
    print(f"  Status: TRENDING market")
    print(f"  Meaning: Winners keep winning, trends persist")
    print(f"  Action: Use BREAKOUTS, trail stops, let winners run")
    print(f"  Avoid: Fading moves, counter-trend trades")
elif h < 0.45:
    print(f"  Status: MEAN-REVERTING market")
    print(f"  Meaning: What goes up comes down")
    print(f"  Action: FADE extremes, buy dips, sell rallies")
    print(f"  Avoid: Chasing breakouts")
else:
    print(f"  Status: RANDOM market")
    print(f"  Meaning: No persistent pattern")
    print(f"  Action: REDUCE size, be very selective")

print(f"\nReturn Autocorr:     {ac:.3f}")
if ac > 0.2:
    print(f"  Status: MOMENTUM REGIME")
    print(f"  Meaning: Price moves tend to continue in same direction")
    print(f"  Action: Trend-following strategies work best")
    print(f"  Avoid: Counter-trend trades will get run over")
elif ac < -0.2:
    print(f"  Status: REVERSION REGIME")
    print(f"  Meaning: Price swings reverse frequently")
    print(f"  Action: Mean-reversion strategies work best")
    print(f"  Avoid: Holding for big trends")
else:
    print(f"  Status: MIXED REGIME")
    print(f"  Meaning: No clear autocorrelation")

print(f"\n  >> INTERPRETATION: {interp.get('market_character', '')}")
print(f"  >> STRATEGY FIT: {interp.get('strategy_fit', '')}")

print("\n" + "="*70)
print("2. MOMENTUM - Is price accelerating or decelerating?")
print("="*70)
roc5 = latest['roc_5']
roc10 = latest['roc_10']
roc20 = latest['roc_20']
accel = latest['price_accel']

print(f"ROC 5-bar:           {roc5:+.2f}%")
print(f"  Meaning: Price changed {abs(roc5):.2f}% over last 5 bars")

print(f"\nROC 10-bar:          {roc10:+.2f}%")
print(f"  Meaning: Price changed {abs(roc10):.2f}% over last 10 bars")

print(f"\nROC 20-bar:          {roc20:+.2f}%")
print(f"  Meaning: Main trend gauge - {abs(roc20):.2f}% move in 20 bars")

print(f"\nPrice Acceleration:  {accel:+.2f}")
if accel > 0:
    print(f"  Status: ACCELERATING")
    print(f"  Meaning: Momentum is building, trend strengthening")
else:
    print(f"  Status: DECELERATING")
    print(f"  Meaning: Momentum is fading, trend weakening")

print(f"\n  >> MOMENTUM ACTION: {interp.get('momentum_action', '')}")

# Trading decision based on momentum
if roc20 > 0 and accel > 0:
    print("\n  TRADE DECISION:")
    print("    - Trend is UP and ACCELERATING")
    print("    - You can ADD to existing long positions")
    print("    - New breakout entries look good")
    print("    - Trail your stop loss, let it run")
elif roc20 > 0 and accel < 0:
    print("\n  TRADE DECISION:")
    print("    - Trend is UP but DECELERATING")
    print("    - TAKE PARTIAL PROFITS (50%)")
    print("    - Tighten stops to breakeven + 1 tick")
    print("    - Don't add new positions")
elif roc20 < 0 and accel < 0:
    print("\n  TRADE DECISION:")
    print("    - Downtrend ACCELERATING")
    print("    - Stay short or flat")
    print("    - Don't try to catch falling knife")
else:
    print("\n  TRADE DECISION:")
    print("    - Momentum is SHIFTING")
    print("    - Watch for potential reversal")
    print("    - Reduce position size")

print("\n" + "="*70)
print("3. MEAN REVERSION - Is price stretched/overextended?")
print("="*70)
bbp = latest['bb_percentile']
rsi_pct = latest['rsi_percentile']
zscore = latest['zscore_to_ma']

print(f"BB Percentile:       {bbp:.3f}")
print(f"  Range: 0 = lower band, 0.5 = middle, 1 = upper band")
if bbp < 0.15:
    print(f"  Status: OVERSOLD - Price near lower Bollinger Band")
    print(f"  Action: Look for LONG entries (buy the dip)")
    print(f"  Example: If trending up, this is a pullback buy")
elif bbp > 0.85:
    print(f"  Status: OVERBOUGHT - Price near upper Bollinger Band")
    print(f"  Action: Take profits on longs, or SHORT if mean-reverting")
    print(f"  Example: If trending, take 50% profit and trail stop")
else:
    print(f"  Status: NEUTRAL - Price in middle of range")
    print(f"  Action: No extreme stretch, no edge")

print(f"\nRSI Percentile:      {rsi_pct:.0f}th")
print(f"  (Historical rank of RSI, not raw RSI value)")
if rsi_pct < 20:
    print(f"  Status: HISTORICALLY OVERSOLD")
    print(f"  Meaning: RSI is in bottom 20% of historical values")
    print(f"  Action: STRONG long signal for this specific symbol")
elif rsi_pct > 80:
    print(f"  Status: HISTORICALLY OVERBOUGHT")
    print(f"  Meaning: RSI is in top 20% of historical values")
    print(f"  Action: STRONG short/exit signal")
else:
    print(f"  Status: NORMAL")

print(f"\nZ-Score to MA(50):   {zscore:+.2f} sigma")
print(f"  Meaning: Price is {abs(zscore):.1f} std deviations from 50-bar average")
if abs(zscore) > 2:
    print(f"  Status: EXTREME DEVIATION")
    print(f"  Action: Mean-reversion trade opportunity")
    print(f"  Warning: Use SMALLER size (high snap-back risk)")
    if zscore > 2:
        print(f"  Direction: Price too high, expect pullback")
    else:
        print(f"  Direction: Price too low, expect bounce")
else:
    print(f"  Status: NORMAL DEVIATION")

print(f"\n  >> REVERSION SIGNAL: {interp.get('reversion_signal', '')}")

print("\n" + "="*70)
print("4. VOLATILITY & RISK - How dangerous is the market?")
print("="*70)
hv = latest['hist_volatility']
vov = latest['vol_of_vol']
regime = latest['vol_regime']
vol_pct = latest['vol_percentile']

print(f"Historical Vol:      {hv:.1f}% annualized")
print(f"  Meaning: This is the current volatility level")
print(f"  Use: Input for position sizing (higher vol = smaller size)")

print(f"\nVol of Vol:          {vov:.2f}")
print(f"  Meaning: Stability of volatility itself")
if vov > 0.5:
    print(f"  Status: UNSTABLE - Volatility is changing rapidly")
    print(f"  Action: Use WIDER stops, market is unpredictable")
else:
    print(f"  Status: STABLE - Volatility is steady")
    print(f"  Action: Can trust your normal stop distances")

print(f"\nVol Regime:          {regime} ({vol_pct:.0f}th percentile)")
if regime == 'HIGH':
    print(f"  Status: HIGH VOLATILITY ENVIRONMENT")
    print(f"  Action: REDUCE position size by 50%")
    print(f"  Stops: Use 2x wider stops than normal")
    print(f"  Why: Market is whippy, false signals common")
    print(f"  Example: If normal size = 0.10 lots, use 0.05 lots")
elif regime == 'LOW':
    print(f"  Status: LOW VOLATILITY ENVIRONMENT")
    print(f"  Action: Safe to SIZE UP positions (1.25x)")
    print(f"  Stops: Can use TIGHTER stops")
    print(f"  Why: Mean-reversion works well in low vol")
    print(f"  Example: If normal size = 0.10 lots, use 0.125 lots")
else:
    print(f"  Status: NORMAL VOLATILITY")
    print(f"  Action: Standard position sizing OK (1.0x)")

print(f"\n  >> VOL ACTION: {interp.get('vol_action', '')}")

print("\n" + "="*70)
print("5. ACTIONABLE SCORES - Combined intelligence")
print("="*70)
trend_score = scores['trend_strength']
rev_score = scores['reversion_opportunity']
risk_score = scores['risk_level']
size_mult = scores['size_multiplier']

print(f"Trend Strength:         {trend_score:.0f}/100")
if trend_score > 60:
    print(f"  Strong trending environment - breakouts work")
elif trend_score < 40:
    print(f"  Weak trend - avoid trend-following")
else:
    print(f"  Moderate trend")

print(f"\nReversion Opportunity:  {rev_score:.0f}/100")
if rev_score > 60:
    print(f"  Good mean-reversion setup available")
elif rev_score < 40:
    print(f"  Poor reversion opportunity")
else:
    print(f"  Moderate reversion setup")

print(f"\nRisk Level:             {risk_score:.0f}/100")
if risk_score > 60:
    print(f"  HIGH RISK - Market dangerous, reduce exposure")
elif risk_score < 40:
    print(f"  LOW RISK - Safe environment for trading")
else:
    print(f"  MODERATE RISK - Normal risk management")

print(f"\n>>> POSITION SIZE MULTIPLIER: {size_mult:.2f}x <<<")
print(f"\n  HOW TO USE:")
print(f"    Your base lot size:  0.10 lots")
print(f"    Multiplier:          {size_mult:.2f}x")
print(f"    >>> USE THIS SIZE:   {0.10 * size_mult:.3f} lots <<<")
print(f"\n  This multiplier accounts for:")
print(f"    - Current volatility regime")
print(f"    - Risk level")
print(f"    - Market stability")

print("\n" + "="*70)
print("FINAL TRADING RECOMMENDATION")
print("="*70)

if trend_score > 60 and risk_score < 50:
    print("STATUS: TREND ENVIRONMENT (Low Risk)")
    print("\nTRADE PLAN:")
    print("  Entry:  Use BREAKOUT entries above recent highs")
    print("  Stops:  Initial stop 1 ATR below entry")
    print("  Profit: TRAIL stops, let winners run")
    print("  Scale:  Add on acceleration (if accel > 0)")
    print("  Exit:   When acceleration flips negative")
elif rev_score > 60 and risk_score < 50:
    print("STATUS: REVERSION SETUP (Low Risk)")
    print("\nTRADE PLAN:")
    print("  Entry:  Fade extremes (BBP > 0.85 or < 0.15)")
    print("  Stops:  Tight stops (0.5 ATR)")
    print("  Profit: Take QUICK profits (50-75% at 1R)")
    print("  Scale:  Don't add, take partial profits")
    print("  Exit:   Fast - don't hold for big moves")
elif risk_score > 70:
    print("STATUS: HIGH RISK WARNING")
    print("\nTRADE PLAN:")
    print("  Entry:  AVOID new trades or reduce size 50%")
    print("  Stops:  Use 2x wider stops")
    print("  Profit: Take profits early")
    print("  Scale:  DO NOT add to positions")
    print("  Exit:   Consider closing existing trades")
else:
    print("STATUS: MIXED CONDITIONS")
    print("\nTRADE PLAN:")
    print("  Entry:  Be SELECTIVE, wait for clearer setups")
    print("  Stops:  Normal stops")
    print("  Profit: Standard targets")
    print("  Scale:  Small positions only")
    print("  Exit:   Standard exits")

print("\n" + "="*70)
print("COMPLETE 5-STEP TRADING PROCESS")
print("="*70)
print("""
STEP 1: Check Hurst Exponent
  Current: {:.3f}
  Action: {}

STEP 2: Confirm with Momentum
  ROC 20-bar: {:+.2f}%
  Acceleration: {:+.2f}
  Action: {}

STEP 3: Check Mean Reversion Signals
  BB Percentile: {:.2f}
  Action: {}

STEP 4: Assess Risk
  Vol Regime: {}
  Risk Level: {:.0f}/100
  Action: Use {:.2f}x size multiplier

STEP 5: Execute Trade
  If entering long breakout:
    - Entry: Above recent high
    - Size: 0.10 x {:.2f} = {:.3f} lots
    - Stop: {} below entry
    - Target: Trail stop based on acceleration
  
  Monitor:
    - If acceleration flips negative -> Take 50% profit
    - If BB Percentile > 0.90 -> Take 50% profit
    - If vol regime changes to HIGH -> Reduce size or exit
""".format(
    h, 
    "Use trend strategies" if h > 0.55 else ("Use reversion strategies" if h < 0.45 else "Be cautious"),
    roc20,
    accel,
    "Add to winners" if accel > 0 else "Take partial profits",
    bbp,
    "Oversold - look for longs" if bbp < 0.15 else ("Overbought - take profits" if bbp > 0.85 else "Neutral"),
    regime,
    risk_score,
    size_mult,
    size_mult,
    0.10 * size_mult,
    "1 ATR" if regime != "HIGH" else "2 ATR"
))

print("\n" + "="*70)
print("KEY TAKEAWAY")
print("="*70)
print(f"""
This market is currently: {regime} vol, {trend_score:.0f}/100 trend strength

Your edge: {'Trend-following' if trend_score > 60 else 'Mean-reversion' if rev_score > 60 else 'Wait for clearer setup'}

Position size: {size_mult:.2f}x your base size

The features tell you:
  1. WHEN to enter (market character + momentum)
  2. HOW MUCH to risk (size multiplier based on vol)
  3. WHEN to add (acceleration positive)
  4. WHEN to exit (acceleration negative or BBP extremes)
""")
