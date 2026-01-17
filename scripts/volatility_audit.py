import MetaTrader5 as mt5
import pandas as pd
import numpy as np

def audit_volatility(symbols):
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    results = []
    for symbol in symbols:
        # Get last 1000 M1 bars for high-fidelity volatility
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
        if rates is None:
            continue
            
        df = pd.DataFrame(rates)
        df['range_pips'] = (df['high'] - df['low']) / mt5.symbol_info(symbol).point
        df['pct_change'] = df['close'].pct_change().abs()
        
        info = mt5.symbol_info(symbol)
        spread_pips = (info.ask - info.bid) / info.point
        
        results.append({
            'symbol': symbol,
            'avg_daily_range_pips': df['range_pips'].mean(),
            'volatility_std': df['pct_change'].std() * 100,
            'spread_pips': spread_pips,
            'adrenaline_score': (df['range_pips'].mean() / (spread_pips if spread_pips > 0 else 1))
        })
        
    mt5.shutdown()
    
    df_results = pd.DataFrame(results).sort_values(by='adrenaline_score', ascending=False)
    print("\n" + "="*70)
    print("TITAN FORENSICS :: SYMBOL VOLATILITY AUDIT")
    print("="*70)
    print(df_results.to_string(index=False))
    print("="*70)

if __name__ == "__main__":
    audit_volatility(["GOLD", "SILVER", "EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "US100"])
