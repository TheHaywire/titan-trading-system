import MetaTrader5 as mt5
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

def live_silver_management_analysis():
    if not mt5.initialize():
        print("MT5 failed")
        return
    
    symbol = "SILVER"
    
    # Get current tick
    tick = mt5.symbol_info_tick(symbol)
    current_bid = tick.bid
    current_ask = tick.ask
    spread = current_ask - current_bid
    
    print("=" * 90)
    print(f"⚡ LIVE SILVER POSITION MANAGEMENT - {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 90)
    
    print(f"\n💰 CURRENT PRICES:")
    print(f"  Bid: ${current_bid:.2f}")
    print(f"  Ask: ${current_ask:.2f}")
    print(f"  Spread: ${spread:.2f}")
    
    # Get your current positions
    positions = mt5.positions_get(symbol=symbol)
    
    if positions:
        print(f"\n📊 YOUR CURRENT SILVER POSITIONS:")
        total_lots = 0
        weighted_entry = 0
        total_unrealized = 0
        
        for pos in positions:
            direction = "SHORT" if pos.type == 1 else "LONG"
            if pos.type == 1:  # Short
                total_lots += pos.volume
                weighted_entry += pos.price_open * pos.volume
                total_unrealized += pos.profit
                print(f"  {pos.volume:6.2f} lots SHORT @ ${pos.price_open:.2f} | P&L: ${pos.profit:,.0f}")
        
        if total_lots > 0:
            avg_entry = weighted_entry / total_lots
            print(f"\n  📌 TOTAL: {total_lots:.2f} lots SHORT")
            print(f"  📌 Avg Entry: ${avg_entry:.2f}")
            print(f"  📌 Current: ${current_bid:.2f}")
            print(f"  📌 Unrealized P&L: ${total_unrealized:,.0f}")
            print(f"  📌 Distance from Entry: ${current_bid - avg_entry:+.2f} ({((current_bid - avg_entry)/avg_entry*100):+.2f}%)")
    
    # Price action analysis
    print(f"\n📈 PRICE ACTION (Last 2 Hours):")
    m1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 120)
    m5_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 24)
    
    if m1_data is not None and m5_data is not None:
        df_m1 = pd.DataFrame(m1_data)
        df_m5 = pd.DataFrame(m5_data)
        
        # Recent high/low
        high_2h = df_m1['high'].max()
        low_2h = df_m1['low'].min()
        
        print(f"  2H High: ${high_2h:.2f}")
        print(f"  2H Low:  ${low_2h:.2f}")
        print(f"  Current vs 2H High: ${current_bid - high_2h:.2f}")
        print(f"  Current vs 2H Low:  ${current_bid - low_2h:.2f}")
        
        # Momentum check
        last_10_closes = df_m1['close'].tail(10)
        momentum = "RISING" if last_10_closes.iloc[-1] > last_10_closes.iloc[0] else "FALLING"
        change_10m = last_10_closes.iloc[-1] - last_10_closes.iloc[0]
        
        print(f"\n  📊 10-Min Momentum: {momentum} (${change_10m:+.2f})")
        
        # Check if price is pulling back
        if current_bid < high_2h - 0.50:
            print(f"  ✅ PULLBACK DETECTED: Price ${(high_2h - current_bid):.2f} below recent high")
        
        # Volume analysis
        recent_vol = df_m1['tick_volume'].tail(10).mean()
        older_vol = df_m1['tick_volume'].head(30).mean()
        vol_change = ((recent_vol - older_vol) / older_vol * 100) if older_vol > 0 else 0
        
        print(f"\n  📈 Volume: {vol_change:+.1f}% vs 30min ago")
        if vol_change < -30:
            print(f"     💤 Volume declining = Exhaustion possible")
        elif vol_change > 30:
            print(f"     🔥 Volume increasing = Momentum strong")
    
    # Key levels
    print(f"\n🎯 KEY LEVELS (H1 Support/Resistance):")
    h1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    
    if h1_data is not None:
        df_h1 = pd.DataFrame(h1_data)
        
        # Find recent swing highs/lows
        highs = []
        lows = []
        
        for i in range(2, len(df_h1)-2):
            if df_h1['high'].iloc[i] > df_h1['high'].iloc[i-1] and df_h1['high'].iloc[i] > df_h1['high'].iloc[i+1]:
                highs.append(df_h1['high'].iloc[i])
            if df_h1['low'].iloc[i] < df_h1['low'].iloc[i-1] and df_h1['low'].iloc[i] < df_h1['low'].iloc[i+1]:
                lows.append(df_h1['low'].iloc[i])
        
        recent_highs = sorted(highs[-5:], reverse=True) if highs else []
        recent_lows = sorted(lows[-5:], reverse=True) if lows else []
        
        print(f"\n  Resistance Levels:")
        for i, r in enumerate(recent_highs[:3], 1):
            dist = r - current_bid
            print(f"    R{i}: ${r:.2f} ({'+' if dist > 0 else ''}{dist:.2f} away)")
        
        print(f"\n  Support Levels:")
        for i, s in enumerate(recent_lows[:3], 1):
            dist = current_bid - s
            print(f"    S{i}: ${s:.2f} ({'+' if dist > 0 else ''}{dist:.2f} away)")
    
    # Check order flow (if we can see it from recent trades)
    print(f"\n💹 RECENT ORDER FLOW (Last 5 minutes):")
    recent_time = datetime.now() - timedelta(minutes=5)
    recent_deals = mt5.history_deals_get(recent_time, datetime.now())
    
    if recent_deals:
        buys = sum(1 for d in recent_deals if d.type == 0)
        sells = sum(1 for d in recent_deals if d.type == 1)
        
        buy_vol = sum(d.volume for d in recent_deals if d.type == 0)
        sell_vol = sum(d.volume for d in recent_deals if d.type == 1)
        
        print(f"  Buy Orders: {buys} ({buy_vol:.2f} lots)")
        print(f"  Sell Orders: {sells} ({sell_vol:.2f} lots)")
        
        if buy_vol > sell_vol * 1.5:
            print(f"  ⚠️ STRONG BUYING PRESSURE")
        elif sell_vol > buy_vol * 1.5:
            print(f"  ✅ STRONG SELLING PRESSURE")
    
    mt5.shutdown()

if __name__ == "__main__":
    live_silver_management_analysis()
