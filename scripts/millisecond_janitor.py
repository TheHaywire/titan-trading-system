"""
THE MILLISECOND JANITOR
=======================
Institutional-grade real-time position enforcer.
Scans all open positions and closes any that violate core risk rules.
Rules are non-negotiable.
"""

import MetaTrader5 as mt5
import time
import json
import os
from datetime import datetime

# HARD CONSTRAINTS
MAX_LOTS_PER_POSITION = 0.5
REQUIRE_STOP_LOSS = True
MAX_DAILY_LOSS = 500.0
POLL_INTERVAL_MS = 500  # Scan every 500ms

def close_position(pos):
    """Instant market close for a violating position."""
    symbol = pos.symbol
    ticket = pos.ticket
    volume = pos.volume
    
    # Determine close direction
    close_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(symbol).bid if pos.type == 0 else mt5.symbol_info_tick(symbol).ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": 20,
        "magic": 900900,  # Janitor Magic Number
        "comment": "JANITOR: RULE VIOLATION",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result

def run_janitor():
    print(f"🚀 JANITOR ACTIVE | Interval: {POLL_INTERVAL_MS}ms")
    print(f"Constraints: Max Lots={MAX_LOTS_PER_POSITION}, SL Required={REQUIRE_STOP_LOSS}")
    
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    try:
        while True:
            positions = mt5.positions_get()
            if positions:
                for pos in positions:
                    violations = []
                    
                    # Rule 1: Max Lot Size
                    if pos.volume > MAX_LOTS_PER_POSITION:
                        violations.append(f"Oversized: {pos.volume} > {MAX_LOTS_PER_POSITION}")
                    
                    # Rule 2: Missing SL
                    if REQUIRE_STOP_LOSS and pos.sl == 0:
                        violations.append("Missing Stop Loss")
                    
                    # Action if violated
                    if violations:
                        print(f"⚠️ VIOLATION detected in {pos.symbol} #{pos.ticket}: {', '.join(violations)}")
                        print("🗑️ Closing position instantly...")
                        res = close_position(pos)
                        if res.retcode == mt5.TRADE_RETCODE_DONE:
                            print(f"✅ Position #{pos.ticket} CLOSED successfully.")
                        else:
                            print(f"❌ Failed to close: {res.comment}")
            
            time.sleep(POLL_INTERVAL_MS / 1000.0)
            
    except KeyboardInterrupt:
        print("Janitor shutting down...")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    run_janitor()
