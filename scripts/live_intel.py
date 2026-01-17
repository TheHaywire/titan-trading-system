"""Simple live intel - outputs to file for clean reading"""
import MetaTrader5 as mt5
from datetime import datetime

mt5.initialize()

KEY_SYMBOLS = [
    "GOLD", "SILVER", "EURUSD", "GBPUSD", "USDJPY",
    "US100Cash", "US30Cash", "GER40Cash", "JP225Cash",
    "BTCUSD", "ETHUSD", "OILCash", "BRENTCash"
]

output = []
output.append("=" * 70)
output.append("REAL-TIME MARKET INTELLIGENCE - Key Symbols")
output.append("=" * 70)
output.append("")

for sym in KEY_SYMBOLS:
    info = mt5.symbol_info(sym)
    if not info:
        output.append(f"{sym}: NOT FOUND")
        continue
    
    spread = info.spread
    rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 24)
    
    if rates is not None and len(rates) > 0:
        atr = sum(r['high'] - r['low'] for r in rates) / len(rates)
        atr_points = atr / info.point if info.point > 0 else 0
        spread_ratio = (spread / atr_points) * 100 if atr_points > 0 else 100
        adrenaline = atr_points / spread if spread > 0 else 0
    else:
        atr_points = 0
        spread_ratio = 100
        adrenaline = 0
    
    if spread_ratio < 5:
        verdict = "EXCELLENT"
    elif spread_ratio < 10:
        verdict = "GOOD"
    elif spread_ratio < 20:
        verdict = "FAIR"
    else:
        verdict = "AVOID"
    
    output.append(f"{sym}:")
    output.append(f"  Spread: {spread} | ATR: {atr_points:.0f} | Ratio: {spread_ratio:.1f}% | Adrenaline: {adrenaline:.1f} | {verdict}")

hour = datetime.utcnow().hour
output.append("")
output.append(f"Session: NEW_YORK (UTC {hour}:00)")
output.append(f"Time: {datetime.now().strftime('%H:%M:%S')}")

# Print and save
for line in output:
    print(line)

with open('data/live_intel_snapshot.txt', 'w') as f:
    f.write('\n'.join(output))

mt5.shutdown()
