import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd

def live_tape_reading():
    if not mt5.initialize():
        print("MT5 failed")
        return
    
    print("=" * 90)
    print(f"📊 LIVE TAPE READING - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 90)
    
    # Silver analysis
    symbol = "SILVER"
    tick = mt5.symbol_info_tick(symbol)
    
    print(f"\n💎 SILVER:")
    print(f"  Bid: ${tick.bid:.2f}")
    print(f"  Ask: ${tick.ask:.2f}")
    print(f"  Last: ${tick.last:.2f}")
    print(f"  Volume (tick): {tick.volume}")
    
    # Get M1 data for immediate price action
    m1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 30)
    
    if m1 is not None:
        df_m1 = pd.DataFrame(m1)
        
        # Last 5 candles
        print(f"\n  📈 LAST 5 CANDLES (M1):")
        print(f"  {'Time':<8} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8} {'Vol':<8} {'Direction'}")
        print(f"  {'-'*70}")
        
        for i in range(-5, 0):
            time = datetime.fromtimestamp(df_m1['time'].iloc[i])
            o = df_m1['open'].iloc[i]
            h = df_m1['high'].iloc[i]
            l = df_m1['low'].iloc[i]
            c = df_m1['close'].iloc[i]
            v = df_m1['tick_volume'].iloc[i]
            direction = "🟢 BULL" if c > o else "🔴 BEAR" if c < o else "⚪ DOJI"
            body_size = abs(c - o)
            
            print(f"  {time.strftime('%H:%M'):<8} {o:<8.2f} {h:<8.2f} {l:<8.2f} {c:<8.2f} {int(v):<8} {direction}")
        
        # Immediate momentum
        last_5_closes = df_m1['close'].tail(5).values
        momentum = "RISING" if last_5_closes[-1] > last_5_closes[0] else "FALLING"
        change_5m = last_5_closes[-1] - last_5_closes[0]
        
        print(f"\n  ⚡ 5-Min Momentum: {momentum} (${change_5m:+.2f})")
        
        # Volume spike check
        avg_vol = df_m1['tick_volume'].tail(10).mean()
        last_vol = df_m1['tick_volume'].iloc[-1]
        vol_ratio = last_vol / avg_vol if avg_vol > 0 else 1
        
        print(f"\n  📊 Volume Analysis:")
        print(f"    Current bar volume: {int(last_vol)}")
        print(f"    Average (10-bar): {int(avg_vol)}")
        print(f"    Volume ratio: {vol_ratio:.2f}x")
        
        if vol_ratio > 1.5:
            print(f"    🔥 HIGH VOLUME - Strong conviction")
        elif vol_ratio < 0.5:
            print(f"    💤 LOW VOLUME - Weak commitment")
        else:
            print(f"    ⚪ NORMAL VOLUME")
        
        # Wick analysis
        last_candle = df_m1.iloc[-1]
        body = abs(last_candle['close'] - last_candle['open'])
        upper_wick = last_candle['high'] - max(last_candle['open'], last_candle['close'])
        lower_wick = min(last_candle['open'], last_candle['close']) - last_candle['low']
        
        print(f"\n  🕯️ Current Candle Anatomy:")
        print(f"    Body: ${body:.2f}")
        print(f"    Upper wick: ${upper_wick:.2f}")
        print(f"    Lower wick: ${lower_wick:.2f}")
        
        if upper_wick > body * 2 and last_candle['close'] < last_candle['open']:
            print(f"    🚨 SHOOTING STAR - Rejection signal")
        elif lower_wick > body * 2 and last_candle['close'] > last_candle['open']:
            print(f"    ✅ HAMMER - Reversal signal")
    
    # Gold check
    print(f"\n" + "=" * 90)
    gold_symbol = "GOLD"
    gold_tick = mt5.symbol_info_tick(gold_symbol)
    
    print(f"\n🥇 GOLD:")
    print(f"  Bid: ${gold_tick.bid:.2f}")
    print(f"  Ask: ${gold_tick.ask:.2f}")
    
    gold_m1 = mt5.copy_rates_from_pos(gold_symbol, mt5.TIMEFRAME_M1, 0, 30)
    
    if gold_m1 is not None:
        df_gold = pd.DataFrame(gold_m1)
        
        last_5_closes_gold = df_gold['close'].tail(5).values
        gold_momentum = "RISING" if last_5_closes_gold[-1] > last_5_closes_gold[0] else "FALLING"
        gold_change = last_5_closes_gold[-1] - last_5_closes_gold[0]
        
        print(f"  ⚡ 5-Min Momentum: {gold_momentum} (${gold_change:+.2f})")
        
        gold_vol = df_gold['tick_volume'].iloc[-1]
        gold_avg_vol = df_gold['tick_volume'].tail(10).mean()
        gold_vol_ratio = gold_vol / gold_avg_vol if gold_avg_vol > 0 else 1
        
        print(f"  📊 Volume ratio: {gold_vol_ratio:.2f}x")
    
    mt5.shutdown()

if __name__ == "__main__":
    live_tape_reading()
