"""
Advanced Feature Engine Demo
Shows hedge fund-grade features in action
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import pandas as pd
import numpy as np
from titan_system.features.quant_features import QuantFeatureEngine
from titan_system.features.advanced_features import (
    AdvancedQuantEngine,
    AdvancedTimeSeriesFeatures,
    PortfolioFeatures
)

# Create sample data
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

# Simulate market returns for beta calculation
market_returns = pd.Series(np.random.randn(500) * 0.01, index=dates)

# Simulate universe returns for cross-sectional ranking
universe_returns = {
    'EURUSD': pd.Series(np.random.randn(500) * 0.008, index=dates),
    'GBPUSD': pd.Series(np.random.randn(500) * 0.009, index=dates),
    'USDJPY': pd.Series(np.random.randn(500) * 0.007, index=dates),
}

print("="*80)
print("ADVANCED INSTITUTIONAL FEATURE ENGINE")
print("="*80)
print(f"Symbol: GOLD (Simulated)")
print(f"Bars: {len(df)} | Latest: {df['time'].iloc[-1]}")
print(f"Price: ${df['close'].iloc[-1]:.2f}\n")

# Compute basic features first
print("[1/3] Computing basic features...")
basic_features_df = QuantFeatureEngine.compute_all(df)
basic_latest = basic_features_df.iloc[-1]

# Compute advanced features
print("[2/3] Computing advanced features...")
advanced_df = AdvancedQuantEngine.compute_all_advanced(
    df,
    universe_returns=universe_returns,
    market_returns=market_returns
)
advanced_latest = advanced_df.iloc[-1]

# Generate signals
print("[3/3] Generating institutional signals...\n")

# Calculate historical metrics for Kelly
returns = df['close'].pct_change().dropna()
win_rate = 0.58  # Example: 58% win rate
avg_win = 2.5    # Average winner is 2.5R
avg_loss = 1.0   # Average loser is 1R

advanced_signals = AdvancedQuantEngine.get_advanced_signals(
    advanced_latest,
    win_rate=win_rate,
    avg_win=avg_win,
    avg_loss=avg_loss,
    current_positions=['GOLD', 'EURUSD', 'GBPUSD'],
    returns_dict={'GOLD': returns, **universe_returns}
)

print("="*80)
print("ADVANCED FEATURES - HEDGE FUND GRADE")
print("="*80)

# Kalman Filter
print("\n1. KALMAN FILTER (Adaptive Trend)")
print("-" * 80)
kalman_trend = advanced_latest['kalman_trend']
kalman_unc = advanced_latest['kalman_uncertainty']
current_price = advanced_latest['close']
print(f"Current Price:       ${current_price:.2f}")
print(f"Kalman Trend:        ${kalman_trend:.2f}")
print(f"Distance:            {((current_price - kalman_trend)/kalman_trend*100):+.2f}%")
print(f"Uncertainty:         {kalman_unc:.4f}")

if current_price > kalman_trend:
    print(f"\nSignal: LONG BIAS")
    print(f"  -> Price above adaptive trend")
    print(f"  -> Stay long, trail stop at Kalman line")
else:
    print(f"\nSignal: SHORT BIAS")
    print(f"  -> Price below adaptive trend")
    print(f"  -> Stay short or wait for cross above")

# HMM Regime
print("\n2. HMM REGIME DETECTION (Hidden Markov Model)")
print("-" * 80)
hmm_state = int(advanced_latest['hmm_regime'])
regime_names = {0: 'LOW VOL', 1: 'NORMAL', 2: 'HIGH VOL'}
print(f"Detected Regime:     {regime_names.get(hmm_state, 'UNKNOWN')}")

if hmm_state == 0:
    print(f"Regime Characteristics:")
    print(f"  - Low volatility environment")
    print(f"  - Mean-reversion dominant")
    print(f"Strategy: Fade extremes, buy dips, sell rallies")
elif hmm_state == 2:
    print(f"Regime Characteristics:")
    print(f"  - High volatility environment")
    print(f"  - Trending behavior")
    print(f"Strategy: Trend-following, breakouts, wide stops")
else:
    print(f"Regime Characteristics:")
    print(f"  - Normal volatility")
    print(f"  - Mixed strategies work")
    print(f"Strategy: Balanced approach")

# Cross-sectional momentum
print("\n3. CROSS-SECTIONAL MOMENTUM (Relative Strength)")
print("-" * 80)
if 'momentum_rank' in advanced_latest:
    mom_rank = advanced_latest['momentum_rank']
    print(f"Momentum Rank:       {mom_rank:.0f}th percentile")
    
    if mom_rank > 80:
        print(f"Status: LEADER")
        print(f"  -> Outperforming universe")
        print(f"  -> OVERWEIGHT this symbol")
    elif mom_rank < 20:
        print(f"Status: LAGGARD")
        print(f"  -> Underperforming universe")
        print(f"  -> UNDERWEIGHT or avoid")
    else:
        print(f"Status: IN-LINE")
        print(f"  -> Normal relative performance")

# Market Beta
print("\n4. MARKET BETA (Systematic Risk)")
print("-" * 80)
if 'market_beta' in advanced_latest:
    beta = advanced_latest['market_beta']
    print(f"Rolling Beta (60-bar): {beta:.2f}")
    
    if beta > 1.3:
        print(f"High Beta Asset:")
        print(f"  -> Amplifies market moves {beta:.1f}x")
        print(f"  -> REDUCE size in uncertain markets")
        print(f"  -> Good for bull markets")
    elif beta < 0.7:
        print(f"Low Beta Asset:")
        print(f"  -> Defensive, muted market sensitivity")
        print(f"  -> Can SIZE UP in volatile markets")
        print(f"  -> Good for bear markets")
    else:
        print(f"Normal Beta:")
        print(f"  -> Moves in-line with market")

# VWAP Deviation
print("\n5. VWAP DEVIATION (Intraday Fair Value)")
print("-" * 80)
vwap_dev = advanced_latest['vwap_deviation']
print(f"VWAP Deviation:      {vwap_dev:+.2f}%")

if abs(vwap_dev) < 0.3:
    print(f"Status: AT FAIR VALUE")
    print(f"  -> Price near VWAP")
    print(f"  -> No intraday edge")
elif vwap_dev > 0.5:
    print(f"Status: ABOVE VWAP (Expensive)")
    print(f"  -> Price {vwap_dev:.2f}% above fair value")
    print(f"  -> Consider fading or taking profits")
    print(f"  -> Intraday resistance likely")
elif vwap_dev < -0.5:
    print(f"Status: BELOW VWAP (Cheap)")
    print(f"  -> Price {abs(vwap_dev):.2f}% below fair value")
    print(f"  -> Consider long entries")
    print(f"  -> Intraday support likely")

# Volume Imbalance
print("\n6. VOLUME IMBALANCE (Order Flow)")
print("-" * 80)
vol_imb = advanced_latest['volume_imbalance']
print(f"Buy/Sell Imbalance:  {vol_imb:.2f}")
print(f"  (0.5 = balanced, >0.5 = buying, <0.5 = selling)")

if vol_imb > 0.6:
    print(f"\nStatus: STRONG BUYING PRESSURE")
    print(f"  -> {vol_imb*100:.0f}% of volume is buying")
    print(f"  -> Expect UPSIDE continuation")
    print(f"  -> Don't fight the tape")
elif vol_imb < 0.4:
    print(f"\nStatus: STRONG SELLING PRESSURE")
    print(f"  -> {(1-vol_imb)*100:.0f}% of volume is selling")
    print(f"  -> Expect DOWNSIDE continuation")
    print(f"  -> Avoid longs")
else:
    print(f"\nStatus: BALANCED FLOW")
    print(f"  -> No clear order flow edge")

# Kelly Criterion
print("\n7. KELLY CRITERION (Optimal Position Sizing)")
print("-" * 80)
kelly_frac = advanced_signals['kelly_fraction']
print(f"Historical Stats:")
print(f"  Win Rate:          {win_rate*100:.1f}%")
print(f"  Avg Win:           {avg_win:.1f}R")
print(f"  Avg Loss:          {avg_loss:.1f}R")
print(f"\nKelly Fraction:      {kelly_frac*100:.1f}% of capital")
print(f"Half-Kelly (Safe):   {kelly_frac*0.5*100:.1f}% of capital")
print(f"\nExample:")
print(f"  Account: $100,000")
print(f"  Full Kelly: ${100000 * kelly_frac:,.0f}")
print(f"  Half-Kelly: ${100000 * kelly_frac * 0.5:,.0f} ← RECOMMEND")

# Portfolio Correlation
print("\n8. PORTFOLIO CORRELATION RISK")
print("-" * 80)
if 'portfolio_risk' in advanced_signals:
    prisk = advanced_signals['portfolio_risk']
    print(f"Current Positions: GOLD, EURUSD, GBPUSD")
    print(f"Max Pairwise Corr: {prisk['max_corr']:.2f}")
    print(f"Avg Correlation:   {prisk['avg_corr']:.2f}")
    print(f"Risk Score:        {prisk['risk_score']:.0f}/100")
    print(f"\nAction: {prisk['action']}")
    
    if prisk['max_corr'] > 0.7:
        print(f"\nWARNING: High correlation detected!")
        print(f"  -> Portfolio too concentrated")
        print(f"  -> DIVERSIFY or reduce size")
    else:
        print(f"\nOK: Acceptable diversification")

# Final Recommendation
print("\n" + "="*80)
recommendation = AdvancedQuantEngine.get_institutional_recommendation(
    basic_latest,
    advanced_signals
)
print(recommendation)

print("\n" + "="*80)
print("HOW TO USE THESE ADVANCED FEATURES")
print("="*80)
print("""
1. KALMAN FILTER → Better than moving averages
   - Dynamic trend that adapts to market changes
   - Use as trailing stop line

2. HMM REGIME → Automatic strategy selection
   - System tells you which strategy to use
   - No guessing about market state

3. CROSS-SECTIONAL RANKING → Focus on leaders
   - Trade the strongest symbols
   - Avoid laggards

4. MARKET BETA → Risk management
   - Size down high-beta assets in uncertain times
   - Size up low-beta assets for stability

5. VWAP DEVIATION → Intraday edge
   - Fade when >1 std from VWAP
   - Buy when <1 std from VWAP

6. ORDER FLOW → Confirm direction
   - Don't fight strong imbalances
   - Wait for balance before reversals

7. KELLY CRITERION → Optimal sizing
   - Mathematically optimal position size
   - Use half-Kelly for safety margin

8. CORRELATION RISK → Portfolio defense
   - Prevents over-concentration
   - Maintains true diversification
""")
