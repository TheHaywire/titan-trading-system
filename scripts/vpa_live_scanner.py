"""
VPA LIVE SCANNER (Anna Coulling Edition)
========================================
Scans your MT5 market for Basic -> Advanced VPA signals right now.

Concepts Checked:
1. Valid Move (Trend Confirmation)
2. Weak Move (Divergence)
3. The Trap (Fakeout)
4. Stopping Volume (Blocking/Reversal)
5. No Demand/Supply (Testing)

"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

# SYMBOLS TO SCAN (Mix of Futures, Crypto, Forex)
SYMBOLS = ['HGCOP-MAR26', 'MTU', 'SES', 'BTCUSD', 'ETHUSD', 'EURUSD', 'GBPUSD', 'USDJPY']

def get_vpa_status(symbol):
    # Try to find symbol if exact name fails
    if not mt5.symbol_info(symbol):
        found = [s.name for s in mt5.symbols_get() if symbol.split('-')[0] in s.name]
        if found: symbol = found[0]
        else: return None

    # Get Data (Daily)
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 50)
    if rates is None: return None
    df = pd.DataFrame(rates)
    
    # Volume Logic
    if 'real_volume' in df.columns and df['real_volume'].sum() > 0:
        vol_col = 'real_volume'
        vol_type = "REAL"
    else:
        vol_col = 'tick_volume'
        vol_type = "TICK"
        
    # Compute Metrics
    last = df.iloc[-2] # Last COMPLETE candle (yesterday)
    curr = df.iloc[-1] # Developing candle (today) 
    
    # We analyze the LAST COMPLETE candle for confirmation
    # But checking current developing volume is advanced "Live" read
    
    target = last # Focus on the closed candle for definitive signal
    
    # Averages
    avg_vol = df[vol_col].iloc[-22:-2].mean()
    avg_spread = (df['high'] - df['low']).iloc[-22:-2].mean()
    
    spread = target['high'] - target['low']
    vol = target[vol_col]
    
    rel_vol = vol / avg_vol
    rel_spread = spread / avg_spread
    
    # Candle Body / Wicks (Advanced VPA)
    body = abs(target['close'] - target['open'])
    upper_wick = target['high'] - max(target['close'], target['open'])
    lower_wick = min(target['close'], target['open']) - target['low']
    
    is_bullish = target['close'] > target['open']
    
    # CLASSIFICATION LOGIC (Basic to Advanced)
    signals = []
    trend = "FLAT"
    
    # 1. BASIC: Trend Confirmation
    if is_bullish:
        if rel_spread > 1.0 and rel_vol > 1.0:
            signals.append("✅ STRONG BUY (Valid)")
            trend = "BULLISH"
        elif rel_spread > 1.0 and rel_vol < 0.8:
            signals.append("⚠️ WEAK BUY (Trap/Divergence)")
            trend = "WEAK BULL"
    else: 
        if rel_spread > 1.0 and rel_vol > 1.0:
            signals.append("✅ STRONG SELL (Valid)")
            trend = "BEARISH"
        elif rel_spread > 1.0 and rel_vol < 0.8:
            signals.append("⚠️ WEAK SELL (Trap/Divergence)")
            trend = "WEAK BEAR"

    # 2. INTERMEDIATE: Anomalies
    # Buy Climax / Selling Climax
    if rel_vol > 1.5 and rel_spread < 0.8:
        signals.append("🛑 STOPPING VOLUME (Blocking)")
        signals.append("   -> Massive effort, no result. Reversal likely.")
        
    # 3. ADVANCED: Candle Shapes + Volume
    # Shooting Star / Hammer with High Volume
    if UpperWickLong(upper_wick, body) and rel_vol > 1.2:
        signals.append("💫 SHOOTING STAR + HIGH VOL (Supply entering)")
        
    if LowerWickLong(lower_wick, body) and rel_vol > 1.2:
        signals.append("🔨 HAMMER + HIGH VOL (Demand entering)")

    # No Demand (Low Vol Up-move)
    if is_bullish and rel_spread < 0.8 and rel_vol < 0.7:
        signals.append("🚫 NO DEMAND (Test)")
        
    return {
        "symbol": symbol,
        "price": target['close'],
        "vol_type": vol_type,
        "rel_vol": rel_vol,
        "rel_spread": rel_spread,
        "trend": trend,
        "signals": signals
    }

def UpperWickLong(wick, body):
    return wick > body * 2

def LowerWickLong(wick, body):
    return wick > body * 2

def main():
    print(f"{'SYMBOL':<15} | {'VOL TYPE':<5} | {'REL VOL':<7} | {'TREND':<10} | {'VPA ANALYSIS (BASIC -> ADVANCED)'}")
    print("="*100)
    
    for s in SYMBOLS:
        res = get_vpa_status(s)
        if res:
            sigs = ", ".join(res['signals']) if res['signals'] else "Normal"
            vol_str = f"{res['rel_vol']:.1f}x"
            print(f"{res['symbol']:<15} | {res['vol_type']:<5} | {vol_str:<7} | {res['trend']:<10} | {sigs}")
        else:
            print(f"{s:<15} | N/A   | N/A     | N/A        | Symbol Not Found")

    print("\nLEGEND:")
    print("✅ Valid: Wide Spread + High Vol (Trend Confirmation)")
    print("⚠️  Trap: Wide Spread + Low Vol (Fakeout)")
    print("🛑 Blocking: Narrow Spread + High Vol (Reversal)")
    print("💫/🔨 Advanced: Wick Rejection + High Vol (Supply/Demand Injection)")

    mt5.shutdown()

if __name__ == "__main__":
    main()
