"""
PROFESSIONAL TRADE EXECUTOR
Executes high-probability setups identified by the scanner
"""

import MetaTrader5 as mt5
from datetime import datetime

def execute_professional_trades():
    if not mt5.initialize():
        print("MT5 initialization failed")
        return
    
    print("=" * 90)
    print("⚡ EXECUTING PROFESSIONAL TRADES")
    print("=" * 90)
    print(f"Time: {datetime.now().strftime('%H:%M:%S')}\n")
    
    # Get account info
    account = mt5.account_info()
    print(f"Account Balance: ${account.balance:,.2f}")
    print(f"Account Equity: ${account.equity:,.2f}\n")
    
    # Define trades to execute
    trades = [
        {
            'symbol': 'US500Cash',
            'direction': 'SELL',
            'lots': 10,
            'sl_distance': 12.92,  # From entry to SL
            'tp_distance': 43.17,  # From entry to TP
            'comment': 'HIGH_PROB_S&P_SHORT'
        },
        {
            'symbol': 'GBPJPY',
            'direction': 'SELL',
            'lots': 10,
            'sl_distance': 0.70,
            'tp_distance': 2.90,
            'comment': 'HIGH_RR_GBPJPY_SHORT'
        },
        {
            'symbol': 'BTCUSD',
            'direction': 'BUY',
            'lots': 5,
            'sl_distance': 1500,
            'tp_distance': 7500,
            'comment': 'EXTREME_RR_BTC_LONG'
        },
    ]
    
    executed_trades = []
    failed_trades = []
    
    for trade in trades:
        symbol = trade['symbol']
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"❌ {symbol}: Cannot get price data")
            failed_trades.append(symbol)
            continue
        
        # Get symbol info
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ {symbol}: Symbol not found")
            failed_trades.append(symbol)
            continue
        
        # Determine order type and price
        if trade['direction'] == 'BUY':
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
            sl = price - trade['sl_distance']
            tp = price + trade['tp_distance']
        else:  # SELL
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
            sl = price + trade['sl_distance']
            tp = price - trade['tp_distance']
        
        # Round prices to proper digits
        digits = symbol_info.digits
        sl = round(sl, digits)
        tp = round(tp, digits)
        
        # Prepare order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": trade['lots'],
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 999999,
            "comment": trade['comment'],
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Execute
        print(f"\n🎯 Executing: {symbol} {trade['direction']} {trade['lots']} lots")
        print(f"   Entry: {price:.{digits}f}")
        print(f"   SL: {sl:.{digits}f}")
        print(f"   TP: {tp:.{digits}f}")
        
        result = mt5.order_send(request)
        
        if result is None:
            print(f"   ❌ FAILED - No response from MT5")
            failed_trades.append(symbol)
            continue
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"   ✅ SUCCESS - Order #{result.order}")
            executed_trades.append({
                'symbol': symbol,
                'direction': trade['direction'],
                'lots': trade['lots'],
                'entry': result.price,
                'sl': sl,
                'tp': tp,
                'ticket': result.order
            })
        else:
            print(f"   ❌ FAILED - {result.comment}")
            failed_trades.append(symbol)
    
    # Summary
    print("\n" + "=" * 90)
    print("📊 EXECUTION SUMMARY")
    print("=" * 90)
    print(f"\n✅ Successfully Executed: {len(executed_trades)}")
    for t in executed_trades:
        print(f"   • {t['symbol']} {t['direction']} {t['lots']} lots @ {t['entry']}")
    
    if failed_trades:
        print(f"\n❌ Failed: {len(failed_trades)}")
        for symbol in failed_trades:
            print(f"   • {symbol}")
    
    print("\n" + "=" * 90)
    
    # Show new portfolio
    print("\n📋 YOUR CURRENT PORTFOLIO:")
    positions = mt5.positions_get()
    if positions:
        for pos in positions:
            direction = "LONG" if pos.type == 0 else "SHORT"
            print(f"   {pos.symbol:<12} {direction:<5} {pos.volume:6.2f} lots | P&L: ${pos.profit:>10,.0f}")
    else:
        print("   No positions")
    
    mt5.shutdown()

if __name__ == "__main__":
    print("\n🚨 PROFESSIONAL TRADE EXECUTOR")
    print("This will execute 3 trades:")
    print("  1. S&P 500 SHORT (10 lots)")
    print("  2. GBPJPY SHORT (10 lots)")
    print("  3. BTC LONG (5 lots)")
    print("\nPress Ctrl+C within 5 seconds to cancel...\n")
    
    import time
    try:
        for i in range(5, 0, -1):
            print(f"Executing in {i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n❌ Execution cancelled by user")
        exit()
    
    print("\n")
    execute_professional_trades()
