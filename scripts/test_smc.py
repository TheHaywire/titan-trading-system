"""
Test the SMC modules on live GOLD data
"""

import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings
from titan_system.smc.market_structure import MarketStructure
from titan_system.smc.liquidity import LiquidityEngine
from titan_system.smc.fvg import FVGDetector

if not mt5.initialize():
    print("MT5 Init Failed")
    exit()

if settings.mt5_login:
    mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

# Get GOLD data
rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_H1, 0, 200)
df = pd.DataFrame(rates)

print("\n" + "="*60)
print("🏗️  INSTITUTIONAL MARKET STRUCTURE ANALYSIS: GOLD")
print("="*60)

# 1. Market Structure
ms = MarketStructure(swing_length=5)
structure = ms.analyze(df)

print(f"\n📊 MARKET STRUCTURE")
print(f"Trend: {structure['trend'].upper()}")
print(f"Swing Highs Detected: {len(structure['swing_highs'])}")
print(f"Swing Lows Detected: {len(structure['swing_lows'])}")

if structure['last_swing_high']:
    print(f"Last Swing High: {structure['last_swing_high']['price']:.2f}")
if structure['last_swing_low']:
    print(f"Last Swing Low: {structure['last_swing_low']['price']:.2f}")

if structure['bos']:
    for bos in structure['bos']:
        print(f"\n✅ BOS Detected: {bos['direction'].upper()} at {bos['price']:.2f}")
        
if structure['choch']:
    for choch in structure['choch']:
        print(f"\n🔄 CHoCH Detected: {choch['direction'].upper()} at {choch['price']:.2f}")

# 2. Liquidity
liq = LiquidityEngine(proximity_threshold=5.0)
liquidity = liq.analyze(df, symbol="GOLD")

print(f"\n💧 LIQUIDITY POOLS")
print(f"Prev Day High: {liquidity['sessions']['prev_day_high']:.2f}" if liquidity['sessions']['prev_day_high'] else "N/A")
print(f"Prev Day Low: {liquidity['sessions']['prev_day_low']:.2f}" if liquidity['sessions']['prev_day_low'] else "N/A")
print(f"\nRound Numbers: {[f'{r:.0f}' for r in liquidity['round_numbers']]}")
print(f"Equal Highs: {len(liquidity['equal_highs'])}")
print(f"Equal Lows: {len(liquidity['equal_lows'])}")

if liquidity['sweeps']:
    for sweep in liquidity['sweeps']:
        print(f"\n🎯 LIQUIDITY SWEEP: {sweep['sweep_type']} at {sweep['level']:.2f}")

# 3. Fair Value Gaps
fvg_detector = FVGDetector(min_gap_size=1.5)
fvg_analysis = fvg_detector.analyze(df)

print(f"\n📦 FAIR VALUE GAPS")
print(f"Total FVGs: {fvg_analysis['total_fvgs']}")
print(f"Unfilled FVGs: {fvg_analysis['unfilled_count']}")

if fvg_analysis['untested_fvgs']:
    print("\nUnfilled FVGs:")
    for fvg in fvg_analysis['untested_fvgs'][-5:]:  # Last 5
        print(f"  {fvg['type']}: {fvg['bottom']:.2f} - {fvg['top']:.2f} (size: {fvg['size']:.2f})")

if fvg_analysis['retest_opportunities']:
    print("\n🎯 FVG RETEST OPPORTUNITIES:")
    for opp in fvg_analysis['retest_opportunities']:
        print(f"  {opp['fvg']['type']} @ {opp['entry_price']:.2f}")

print("\n" + "="*60)

mt5.shutdown()
