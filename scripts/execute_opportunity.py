
import sys
import os
import MetaTrader5 as mt5
from datetime import datetime
import time
import pandas as pd

# Path Setup
sys.path.append(os.getcwd())
from titan_system.core.execution import MT5Execution
from config.settings import settings
from scripts.scan_opportunities import scan_market

def execute_best_opportunity():
    while True:
        print(f"\n⏰ Auto-Scan Cycle Started at {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
        
        # 1. Scan (Turbo Mode)
        try:
            best_op = scan_market()
        except KeyboardInterrupt:
            print("🛑 Scalper stopped by user.")
            break
        except Exception as e:
            print(f"❌ Scan failed: {e}")
            best_op = None
            
        if best_op:
            print(f"\n💎 Best Setup Found: {best_op['Symbol']} ({best_op['Strategy']}) {best_op['Type']}")
            
            # 2. Execution
            execution = MT5Execution(settings)
            
             # Re-connect check
            if not execution.connect():
                 print("❌ Execution Connect Failed. Retrying...")
            else:
                 symbol = best_op['Symbol']
                 
                 # IDEMPOTENCY CHECK
                 positions = execution.get_positions()
                 
                 # Check if specific symbol is already traded
                 already_open = False
                 for pos in positions:
                     if pos.get('symbol') == symbol:
                         already_open = True
                         break
                         
                 if already_open:
                     print(f"⚠️ Position already open for {symbol}. Managing risk...")
                     # We skip execution but stay in loop
                 else:
                     order_type = best_op['Type']
                     
                     # DYNAMIC RISK MANAGEMENT
                     account = execution.get_account_info()
                     equity = account.get('equity', 10000)
                     
                     # Get current ATR for the symbol
                     tick = mt5.symbol_info_tick(symbol)
                     if not tick:
                         print(f"⚠️ No tick data for {symbol}")
                         continue
                         
                     # Fetch last 20 M1 candles to calculate volatility
                     rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 20)
                     if rates is not None and len(rates) >= 14:
                         df_atr = pd.DataFrame(rates)
                         atr = (df_atr['high'] - df_atr['low']).rolling(14).mean().iloc[-1]
                         
                         # Dynamic Position Sizing based on volatility
                         # Lower volatility = bigger position, Higher volatility = smaller position
                         base_risk = equity * 0.02  # 2% risk
                         
                         # Calculate lot size
                         # For Gold: 1 lot = $100 per $1 move
                         # For Forex: 1 lot = $10 per pip
                         if "XAU" in symbol or "GOLD" in symbol:
                             # Gold volatility in dollars
                             risk_per_lot = atr * 100
                         else:
                             # Forex (approximate)
                             risk_per_lot = (atr / 0.0001) * 10
                         
                         if risk_per_lot > 0:
                             volume = base_risk / risk_per_lot
                             volume = max(0.01, min(volume, 1.0))  # Cap between 0.01 and 1.0
                             volume = round(volume, 2)
                         else:
                             volume = 0.05
                         
                         # Dynamic Stops (ATR-based, not fixed pips)
                         sl_distance = atr * 1.5
                         tp_distance = atr * 2.5
                         
                         print(f"📊 ATR: {atr:.5f} | Dynamic Lot: {volume} | Risk: ${base_risk:.2f}")
                     else:
                         # Fallback
                         volume = 0.05
                         sl_distance = None
                         tp_distance = None
                     
                     print(f"⚡ Executing {order_type} on {symbol}...")
                     
                     # Use dynamic stops if available, otherwise fallback to pips
                     if sl_distance and tp_distance:
                         # Calculate SL/TP as actual prices
                         price = tick.ask if order_type == 'BUY' else tick.bid
                         if order_type == 'BUY':
                             sl_price = price - sl_distance
                             tp_price = price + tp_distance
                         else:
                             sl_price = price + sl_distance
                             tp_price = price - tp_distance
                         
                         # For now, convert back to pips for execute_order (TODO: refactor execute_order)
                         point = mt5.symbol_info(symbol).point
                         sl_pips = int(abs(price - sl_price) / (point * 10))
                         tp_pips = int(abs(tp_price - price) / (point * 10))
                     else:
                         sl_pips = 50
                         tp_pips = 100
                     
                     
                     result = execution.execute_order(
                         symbol=symbol,
                         order_type=order_type,
                         volume=volume,
                         sl_pips=sl_pips,
                         tp_pips=tp_pips,
                         comment=f"Scalp/{best_op['Strategy'][:5]}"
                     )
                     
                     if result:
                         print(f"✅ Trade Executed! Ticket: {result['ticket']}")
                         
                         # Log to Google Sheets
                         try:
                              from titan_system.integrations.google_sheets import TitanSheets
                              sheets = TitanSheets() 
                              if sheets.enabled:
                                  sheets.log_trade({
                                      "ticket": result['ticket'],
                                      "symbol": symbol,
                                      "type": order_type,
                                      "volume": result['volume'],
                                      "open_price": result['open_price'],
                                      "sl": result['sl'],
                                      "tp": result['tp'],
                                      "pnl": 0.0,
                                      "comment": f"Scalp/{best_op['Strategy'][:5]}"
                                  })
                                  print("📝 Logged.")
                         except Exception as e:
                              print(f"⚠️ Sheet Log Error: {e}")
                     else:
                         print("❌ Execution Failed.")
        else:
            print("💤 No setups. Brief pause...")
            
        print("\n⏳ Next scan in 5 minutes...")
        time.sleep(300) # 5 Minute Loop for Scalping Speed

if __name__ == "__main__":
    execute_best_opportunity()
