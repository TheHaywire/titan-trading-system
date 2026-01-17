import MetaTrader5 as mt5
import pandas as pd
import json
from datetime import datetime

def find_high_alpha_symbols(limit=20):
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    all_symbols = mt5.symbols_get()
    print(f"Scanning {len(all_symbols)} symbols...")
    
    opportunities = []
    
    # Selection criteria: 
    # 1. Must have H1 data available
    # 2. Volatility (H1 Range) must be high relative to Spread
    # 3. Spread must not be 'toxic' (too wide)
    
    for i, sym_info in enumerate(all_symbols):
        if i % 100 == 0: print(f"  Processed {i}/{len(all_symbols)}...")
        
        symbol = sym_info.name
        
        # Quick check: Is it tradeable?
        if not sym_info.visible:
            mt5.symbol_select(symbol, True)
            
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 24)
        if rates is None or len(rates) < 24:
            continue
            
        df = pd.DataFrame(rates)
        point = sym_info.point
        avg_h1_range = ((df['high'] - df['low'])).mean() / (point if point > 0 else 1)
        
        # Get live spread
        tick = mt5.symbol_info_tick(symbol)
        if tick is None: continue
        spread = (tick.ask - tick.bid) / (point if point > 0 else 1)
        
        if spread <= 0: continue
        
        adrenaline_score = avg_h1_range / spread
        
        opportunities.append({
            'symbol': symbol,
            'description': sym_info.description,
            'avg_h1_range_pips': round(avg_h1_range, 2),
            'spread_pips': round(spread, 2),
            'adrenaline_score': round(adrenaline_score, 2),
            'currency': sym_info.currency_base
        })
        
    # Sort by adrenaline score
    discovered = sorted(opportunities, key=lambda x: x['adrenaline_score'], reverse=True)
    
    # Save top 20
    top_20 = discovered[:limit]
    
    with open('data/discovered_high_alpha.json', 'w') as f:
        json.dump(top_20, f, indent=4)
        
    print("\n" + "="*70)
    print(f"TITAN DISCOVERY: TOP {limit} HIGH-ALPHA OUTLIERS")
    print("="*70)
    for s in top_20:
        print(f"{s['symbol']:12} | Adrenaline: {s['adrenaline_score']:6} | Range: {s['avg_h1_range_pips']:8} | Spread: {s['spread_pips']}")
    print("="*70)
    print(f"Results saved to data/discovered_high_alpha.json")
    
    mt5.shutdown()

if __name__ == "__main__":
    find_high_alpha_symbols()
