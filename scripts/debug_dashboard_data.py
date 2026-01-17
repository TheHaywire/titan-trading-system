import MetaTrader5 as mt5
import pandas as pd

def debug():
    print("--- TITAN DASHBOARD DEBUG ---")
    if not mt5.initialize():
        print("❌ MT5 Initialization FAILED")
        return
    
    print("✅ MT5 Connected")
    
    acct = mt5.account_info()
    if acct:
        print(f"✅ Account Info: Equity=${acct.equity}, Profit=${acct.profit}")
    else:
        print("❌ Account Info is NONE")
        
    positions = mt5.positions_get()
    if positions:
        print(f"✅ Found {len(positions)} active positions")
        for p in positions:
            print(f"   - {p.symbol} (Ticket: {p.ticket})")
    else:
        print("ℹ️ No active positions found")
        
    WATCHLIST = ["ETHUSD", "SILVER", "GOLD", "US100Cash", "BTCUSD"]
    print("\n--- Testing Watchlist Symbols ---")
    for sym in WATCHLIST:
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 10)
        if rates is not None:
            print(f"✅ {sym}: Data OK ({len(rates)} bars)")
        else:
            print(f"❌ {sym}: FAILED to get data. Check symbol name mapping.")
            # Check if US100 exists vs US100Cash
            info = mt5.symbol_info(sym)
            if info is None:
                print(f"   (Symbol '{sym}' does not exist in MT5)")

    mt5.shutdown()

if __name__ == "__main__":
    debug()
