"""Test comprehensive intel integration"""
import sys
sys.path.insert(0, '.')
from titan_system.core.comprehensive_intel import ComprehensiveIntel

intel = ComprehensiveIntel()

for symbol in ['GOLD', 'BTCUSD', 'EURUSD', 'US100Cash']:
    print(f"\n{'='*50}")
    print(f"INTEL: {symbol}")
    print('='*50)
    
    data = intel.get_symbol_intelligence(symbol)
    master = data.get('master', {})
    sessions = data.get('sessions', [])
    
    if master:
        print(f"  Category: {master.get('category')}")
        print(f"  Spread Ratio: {master.get('spread_ratio', 0):.2f}%")
        print(f"  Adrenaline Score: {master.get('adrenaline_score', 0):.2f}")
        print(f"  Swap Long: {master.get('swap_long', 0)}")
        print(f"  Swap Short: {master.get('swap_short', 0)}")
        print(f"  Is Tradeable: {'YES' if master.get('is_tradeable') else 'NO'}")
        print(f"  Contract Size: {master.get('contract_size')}")
    else:
        print(f"  No master data found")
    
    if sessions:
        print(f"\n  Sessions ({len(sessions)}):")
        for s in sessions[:3]:
            print(f"    {s.get('session')}: Spread={s.get('avg_spread')}, ATR={s.get('avg_range')}")
