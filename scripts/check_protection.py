"""Check if profits are protected"""
import MetaTrader5 as mt5
mt5.initialize()

positions = mt5.positions_get()
if not positions:
    print("No positions")
    mt5.shutdown()
    exit()

print("PROFIT PROTECTION STATUS")
print("="*60)

need_protection = []

for p in positions:
    entry = p.price_open
    current = p.price_current
    sl = p.sl
    profit = p.profit
    
    direction = "BUY" if p.type == 0 else "SELL"
    
    # Check if SL is at break-even or better
    if p.type == 0:  # BUY
        protected = sl >= entry if sl > 0 else False
    else:  # SELL
        protected = sl <= entry if sl > 0 else False
    
    status = "PROTECTED" if protected else "AT RISK"
    
    print(f"{p.symbol} {direction}: ${profit:.0f} | {status}")
    
    if profit > 100 and not protected:
        need_protection.append(p)

print()
print("="*60)
if need_protection:
    print(f"WARNING: {len(need_protection)} positions with >$100 profit NEED PROTECTION!")
    for p in need_protection:
        print(f"  - {p.symbol}: ${p.profit:.0f}")
else:
    print("All profitable positions are protected!")

mt5.shutdown()
