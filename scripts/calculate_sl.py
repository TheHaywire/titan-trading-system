import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd

def calculate_optimal_sl():
    if not mt5.initialize():
        return
    
    symbol = "SILVER"
    
    # Get current price
    tick = mt5.symbol_info_tick(symbol)
    current = tick.bid
    
    # Get your positions
    positions = mt5.positions_get(symbol=symbol)
    
    if not positions:
        print("No Silver positions found")
        return
    
    # Calculate your exposure
    total_lots = 0
    weighted_entry = 0
    
    print("=" * 90)
    print(f"🎯 OPTIMAL STOP LOSS CALCULATOR - Silver @ ${current:.2f}")
    print("=" * 90)
    
    print(f"\n📊 YOUR CURRENT POSITIONS:")
    for pos in positions:
        if pos.type == 1:  # Short
            total_lots += pos.volume
            weighted_entry += pos.price_open * pos.volume
            print(f"  {pos.volume:6.2f} lots SHORT @ ${pos.price_open:.2f}")
    
    if total_lots == 0:
        print("No short positions")
        return
    
    avg_entry = weighted_entry / total_lots
    current_loss = (current - avg_entry) * total_lots * 5000
    
    print(f"\n  TOTAL: {total_lots:.2f} lots SHORT")
    print(f"  Avg Entry: ${avg_entry:.2f}")
    print(f"  Current: ${current:.2f}")
    print(f"  Current Loss: ${current_loss:,.0f}")
    
    # Get H1 data for technical levels
    h1_data = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
    
    if h1_data is None:
        print("Failed to get H1 data")
        return
    
    df = pd.DataFrame(h1_data)
    
    # Find recent swing highs
    recent_high = df['high'].tail(50).max()
    h4_high = df['high'].tail(20).max()
    daily_high = df['high'].max()
    
    # ATR for stop distance
    df['tr'] = df.apply(lambda row: max(
        row['high'] - row['low'],
        abs(row['high'] - row['close']),
        abs(row['low'] - row['close'])
    ), axis=1)
    atr = df['tr'].tail(14).mean()
    
    print(f"\n📐 TECHNICAL LEVELS:")
    print(f"  Recent High (50H): ${recent_high:.2f}")
    print(f"  H4 High: ${h4_high:.2f}")
    print(f"  Daily High: ${daily_high:.2f}")
    print(f"  ATR (14): ${atr:.2f}")
    
    # Calculate stop loss options
    print(f"\n🎯 STOP LOSS OPTIONS:")
    print(f"\n{'Level':<25} {'Stop $':<10} {'Distance':<12} {'Risk $':<15} {'Logic'}")
    print("-" * 90)
    
    options = [
        ("Tight (Current +0.5)", current + 0.50, "Very aggressive - likely to hit"),
        ("Recent High +0.2", recent_high + 0.20, "Logical resistance break"),
        ("H4 High +0.3", h4_high + 0.30, "Confirmed trend break"),
        ("1 ATR", current + atr, "Volatility-based"),
        ("1.5 ATR", current + (1.5 * atr), "Standard institutional"),
        ("2 ATR", current + (2 * atr), "Conservative"),
        ("Daily High +0.5", daily_high + 0.50, "Major resistance"),
        ("Round $92", 92.00, "Psychological level"),
        ("Round $95", 95.00, "Disaster prevention"),
        ("Round $100", 100.00, "Absolute max pain"),
    ]
    
    for name, stop_price, logic in options:
        distance = stop_price - current
        risk = (stop_price - avg_entry) * total_lots * 5000
        
        print(f"{name:<25} ${stop_price:<9.2f} ${distance:>5.2f} ({distance/current*100:>4.1f}%)  ${risk:>13,.0f}  {logic}")
    
    # RECOMMENDATION
    print(f"\n" + "=" * 90)
    print(f"💡 PROFESSIONAL RECOMMENDATION:")
    print(f"=" * 90)
    
    # Best stop calculation
    best_stop = h4_high + 0.30
    best_risk = (best_stop - avg_entry) * total_lots * 5000
    
    print(f"\n✅ OPTIMAL STOP: ${best_stop:.2f}")
    print(f"\nWhy:")
    print(f"  • This is H4 swing high + buffer")
    print(f"  • If Silver breaks THIS convincingly, your thesis is WRONG")
    print(f"  • Risk from current: ${best_risk - current_loss:,.0f}")
    print(f"  • Total risk from avg entry: ${best_risk:,.0f}")
    
    print(f"\n⚖️ RISK/REWARD AT THIS STOP:")
    print(f"  Risk (to SL): ${best_risk:,.0f}")
    print(f"  Reward (to $87): ${(avg_entry - 87) * total_lots * 5000:,.0f}")
    print(f"  Reward (to $85): ${(avg_entry - 85) * total_lots * 5000:,.0f}")
    print(f"  R:R Ratio (to $87): {((avg_entry - 87) * total_lots * 5000) / best_risk:.2f}:1")
    
    # Alternative scenarios
    print(f"\n📊 ALTERNATIVE SCENARIO:")
    print(f"\nIf you REDUCE position to 40 lots (close 40 lots):")
    reduced_lots = 40
    reduced_risk = (best_stop - avg_entry) * reduced_lots * 5000
    print(f"  Risk to ${best_stop:.2f}: ${reduced_risk:,.0f}")
    print(f"  Reward to $85: ${(avg_entry - 85) * reduced_lots * 5000:,.0f}")
    print(f"  R:R Ratio: {((avg_entry - 85) * reduced_lots * 5000) / reduced_risk:.2f}:1")
    print(f"  ✅ MUCH BETTER - this is the professional choice")
    
    mt5.shutdown()

if __name__ == "__main__":
    calculate_optimal_sl()
