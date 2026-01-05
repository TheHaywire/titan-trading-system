
import MetaTrader5 as mt5
import pandas as pd

if mt5.initialize():
    print("--- OPEN POSITIONS ---")
    positions = mt5.positions_get()
    if positions:
        df = pd.DataFrame(list(positions), columns=positions[0]._asdict().keys())
        print(df[['symbol', 'type', 'volume', 'price_open', 'profit', 'comment']])
    else:
        print("No open positions.")
        
    print("\n--- ORDER HISTORY (Last 10) ---")
    orders = mt5.history_orders_get(from_position=0, count=10)
    if orders:
         for o in orders:
             print(f"Ticket: {o.ticket}, Symbol: {o.symbol}, Type: {o.type}, State: {o.state}, Retcode: {o.state}")
    else:
        print("No order history.")

    mt5.shutdown()
else:
    print("MT5 Init Failed")
