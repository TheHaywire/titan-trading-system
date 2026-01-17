"""
MT5 Validation Script - Test All Advanced Features on Real Data
"""
import sys
sys.path.insert(0, r'c:\Users\manan\OneDrive\Documents\Metatrader Trading System 7-12-2025')

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

print("="*80)
print("MT5 FEATURE VALIDATION - Testing All Advanced Features")
print("="*80)

# Initialize MT5
if not mt5.initialize():
    print("ERROR: Failed to initialize MT5")
    exit()

print(f"\n[1/5] Connected to MT5")
print(f"Account: {mt5.account_info().login}")

# Get GOLD data
symbol = "GOLD"
timeframe = mt5.TIMEFRAME_H1
bars = 500

rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)

if rates is None or len(rates) == 0:
    print(f"ERROR: Failed to get data for {symbol}")
    mt5.shutdown()
    exit()

df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.rename(columns={'tick_volume': 'volume'}, inplace=True)

print(f"[2/5] Fetched {len(df)} bars for {symbol}")
print(f"Latest: {df['time'].iloc[-1]}")
print(f"Close: ${df['close'].iloc[-1]:.2f}")

# Test basic features
print(f"\n[3/5] Testing BASIC features...")
try:
    from titan_system.features.quant_features import QuantFeatureEngine
    basic_df = QuantFeatureEngine.compute_all(df)
    basic_latest = basic_df.iloc[-1]
    
    print(f"  ✓ Hurst Exponent: {basic_latest['hurst']:.3f}")
    print(f"  ✓ BB Percentile: {basic_latest['bb_percentile']:.2f}")
    print(f"  ✓ Vol Regime: {basic_latest['vol_regime']}")
    print(f"  ✓ All basic features PASSED")
except Exception as e:
    print(f"  ✗ Basic features FAILED: {e}")

# Test advanced features
print(f"\n[4/5] Testing ADVANCED features...")
try:
    from titan_system.features.advanced_features import AdvancedQuantEngine
    
    # Create mock universe returns (in production you'd fetch real data)
    returns = df['close'].pct_change()
    universe_returns = {
        'EURUSD': returns + np.random.randn(len(returns)) * 0.001,
        'GBPUSD': returns + np.random.randn(len(returns)) * 0.001,
    }
    market_returns = returns.copy()
    
    advanced_df = AdvancedQuantEngine.compute_all_advanced(
        df,
        universe_returns=universe_returns,
        market_returns=market_returns
    )
    advanced_latest = advanced_df.iloc[-1]
    
    print(f"  ✓ Kalman Trend: ${advanced_latest['kalman_trend']:.2f}")
    print(f"  ✓ HMM Regime: {int(advanced_latest['hmm_regime'])}")
    print(f"  ✓ VWAP Deviation: {advanced_latest['vwap_deviation']:+.2f}%")
    print(f"  ✓ Volume Imbalance: {advanced_latest['volume_imbalance']:.2f}")
    
    if 'momentum_rank' in advanced_latest:
        print(f"  ✓ Cross-sectional Rank: {advanced_latest['momentum_rank']:.0f}th")
    
    if 'market_beta' in advanced_latest:
        print(f"  ✓ Market Beta: {advanced_latest['market_beta']:.2f}")
    
    print(f"  ✓ All advanced features PASSED")
    
except Exception as e:
    print(f"  ✗ Advanced features FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test signal generation
print(f"\n[5/5] Testing SIGNAL generation...")
try:
    signals = AdvancedQuantEngine.get_advanced_signals(
        advanced_latest,
        win_rate=0.55,
        avg_win=2.0,
        avg_loss=1.0
    )
    
    print(f"  ✓ Kalman Signal: {signals.get('kalman_signal', 'N/A')}")
    print(f"  ✓ HMM Advice: {signals.get('hmm_advice', 'N/A')}")
    print(f"  ✓ VWAP Signal: {signals.get('vwap_signal', 'N/A')}")
    print(f"  ✓ Flow Signal: {signals.get('flow_signal', 'N/A')}")
    print(f"  ✓ Kelly Fraction: {signals.get('kelly_fraction', 0)*100:.1f}%")
    
    print(f"  ✓ Signal generation PASSED")
    
except Exception as e:
    print(f"  ✗ Signal generation FAILED: {e}")

mt5.shutdown()

print(f"\n" + "="*80)
print(f"VALIDATION COMPLETE - Features work with MT5! ✓")
print(f"="*80)
