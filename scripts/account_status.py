
import MetaTrader5 as mt5

if mt5.initialize():
    acct = mt5.account_info()
    positions = mt5.positions_get()
    
    print("=" * 50)
    print("ACCOUNT STATUS")
    print("=" * 50)
    print(f"Balance:    ${acct.balance:,.2f}")
    print(f"Equity:     ${acct.equity:,.2f}")
    print(f"Margin:     ${acct.margin:,.2f}")
    print(f"Free Margin: ${acct.margin_free:,.2f}")
    print("-" * 50)
    
    total_profit = 0
    if positions:
        print(f"Open Positions: {len(positions)}")
        print("-" * 50)
        for p in positions:
            total_profit += p.profit
            status = "🟢" if p.profit >= 0 else "🔴"
            print(f"{status} {p.symbol:12} | {p.volume} lots | P&L: ${p.profit:+.2f}")
        print("-" * 50)
        print(f"TOTAL FLOATING P&L: ${total_profit:+.2f}")
    else:
        print("No open positions.")
    
    print("=" * 50)
    mt5.shutdown()
else:
    print("MT5 Init Failed")
