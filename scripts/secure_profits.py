"""
Secure Profits - Move SL to Break-Even
======================================
Moves stop loss to entry price for all profitable positions
"""
import MetaTrader5 as mt5
mt5.initialize()

positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    exit()

print("SECURING PROFITS - Moving SL to Break-Even")
print("="*60)

secured = 0
failed = 0

for p in positions:
    # Only secure positions with >$50 profit
    if p.profit < 50:
        continue
    
    entry = p.price_open
    sl = p.sl
    tp = p.tp
    
    # Check if already secured
    if p.type == 0:  # BUY
        if sl >= entry:
            print(f"{p.symbol} BUY: Already secured")
            continue
        new_sl = entry + 0.00001  # Slightly above entry for buffer
    else:  # SELL
        if sl <= entry and sl > 0:
            print(f"{p.symbol} SELL: Already secured")
            continue
        new_sl = entry - 0.00001  # Slightly below entry
    
    # Modify position
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": p.symbol,
        "position": p.ticket,
        "sl": new_sl,
        "tp": tp,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"SECURED: {p.symbol} (${p.profit:.0f}) - SL moved to {new_sl:.5f}")
        secured += 1
    else:
        print(f"FAILED: {p.symbol} - {result.comment}")
        failed += 1

print()
print("="*60)
print(f"Secured: {secured} | Failed: {failed}")

mt5.shutdown()
