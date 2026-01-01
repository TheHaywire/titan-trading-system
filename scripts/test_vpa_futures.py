"""
VALIDATE VPA ON FUTURES (Real Volume)
=====================================
Testing Anna Coulling's concepts on GC, TU, ES.

Hypothesis: 
1. Valid Move (Wide Spread + High Vol) -> Trends
2. Fake Move (Wide Spread + Low Vol) -> Reverts
3. Blocking (Narrow Spread + High Vol) -> Reverts
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

def get_data(symbol, bars=3000):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, bars)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Check if we have volume
    if df['real_volume'].sum() == 0:
        print(f"⚠️  {symbol} has NO Real Volume. Using Tick Volume (Suboptimal).")
        df['vol'] = df['tick_volume']
    else:
        print(f"✅ {symbol} has REAL Volume.")
        df['vol'] = df['real_volume']
        
    return df

def analyze_symbol(name, mt5_symbol):
    print(f"\n📊 TESTING VPA: {name} ({mt5_symbol})")
    df = get_data(mt5_symbol)
    if df is None:
        print("❌ No Data")
        return

    # 1. Calc Metrics
    df['spread'] = df['high'] - df['low']
    df['spread_ma'] = df['spread'].rolling(20).mean()
    df['vol_ma'] = df['vol'].rolling(20).mean()
    
    df['rel_spread'] = df['spread'] / df['spread_ma']
    df['rel_vol'] = df['vol'] / df['vol_ma']
    
    # 2. Future Returns (Next 1 Day, Next 3 Days)
    # We want to see if the direction continues. 
    # Direction of candle: Close > Open (1) or Close < Open (-1)
    df['dir'] = np.where(df['close'] > df['open'], 1, -1)
    
    # Next return (in direction of candle)
    # If candle was UP, does price go HIGHER?
    # If candle was DOWN, does price go LOWER?
    df['ret_1d'] = df['close'].shift(-1) - df['close']
    df['ret_3d'] = df['close'].shift(-3) - df['close']
    
    # Align return with candle direction
    df['cont_1d'] = df['ret_1d'] * df['dir'] # Positive = Continuation
    df['cont_3d'] = df['ret_3d'] * df['dir'] # Positive = Continuation

    # 3. Categorize Candles
    
    # A) VALIDATION: Wide Spread (>1.2) + High Vol (>1.2)
    valid_mask = (df['rel_spread'] > 1.2) & (df['rel_vol'] > 1.2)
    
    # B) ANOMALY 1 (TRAP): Wide Spread (>1.2) + Low Vol (<0.8)
    trap_mask = (df['rel_spread'] > 1.2) & (df['rel_vol'] < 0.8)
    
    # C) ANOMALY 2 (BLOCKING): Narrow Spread (<0.8) + High Vol (>1.2)
    block_mask = (df['rel_spread'] < 0.8) & (df['rel_vol'] > 1.2)
    
    # D) BASELINE (All candles)
    base_1d = df['cont_1d'].mean()
    base_3d = df['cont_3d'].mean()
    
    print(f"   Baseline Continuation (1-day): {base_1d:.2f}")
    
    # 4. Results
    
    # Validation
    v_1d = df.loc[valid_mask, 'cont_1d'].mean()
    v_count = valid_mask.sum()
    print(f"   [VALIDATION] Wide+HighVol (n={v_count}):")
    print(f"     -> 1-Day Cont: {v_1d:.2f} (vs {base_1d:.2f})")
    print(f"     -> Verdict: {'✅ STRONG' if v_1d > base_1d else '❌ WEAK'}")

    # Trap
    t_1d = df.loc[trap_mask, 'cont_1d'].mean()
    t_count = trap_mask.sum()
    print(f"   [TRAP] Wide+LowVol (n={t_count}):")
    print(f"     -> 1-Day Cont: {t_1d:.2f} (vs {base_1d:.2f})")
    print(f"     -> Verdict: {'✅ REVERSAL' if t_1d < base_1d else '❌ FAILED'}")
    
    # Blocking (Reversal signal usually)
    # For blocking, we expect LOW continuation (or negative)
    b_1d = df.loc[block_mask, 'cont_1d'].mean()
    b_count = block_mask.sum()
    print(f"   [BLOCKING] Narrow+HighVol (n={b_count}):")
    print(f"     -> 1-Day Cont: {b_1d:.2f} (vs {base_1d:.2f})")
    print(f"     -> Verdict: {'✅ REVERSAL/STOP' if b_1d < base_1d else '❌ FAILED'}")

    return {
        "valid_edge": v_1d - base_1d,
        "trap_edge": base_1d - t_1d
    }

def main():
    # Use mapped symbols from before
    # GC -> HGCOP, TU -> MTU, ES -> SES
    # Adjust as needed if they changed
    targets = [
        ('Gold', 'HGCOP-MAR26'),
        ('Treasury', 'MTU'),
        ('S&P500', 'SES')
    ]
    
    print("ANALYZING VPA PREDICTIVE POWER")
    print("==============================")
    
    for name, sym in targets:
        # Resolve dynamic symbol looking (optional safety)
        if not mt5.symbol_info(sym):
            # Try to find it loosely
            found = [s.name for s in mt5.symbols_get() if sym.split('-')[0] in s.name]
            if found: sym = found[0]
            
        if mt5.symbol_info(sym):
            analyze_symbol(name, sym)
        else:
            print(f"❌ Could not find {sym}")

    mt5.shutdown()

if __name__ == "__main__":
    main()
