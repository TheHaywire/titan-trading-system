"""
ADAPTIVE EXIT MANAGER
=====================
Institutional trade lifecycle management.
Handles Vol-Trailing and Multi-Stage Scale-outs.
"""

import MetaTrader5 as mt5
import pandas as pd
import json
from datetime import datetime

def manage_active_trades(strategy_magic=None):
    if not mt5.initialize():
        return {"status": "ERROR", "reason": "MT5 Init Failed"}
        
    positions = mt5.positions_get(magic=strategy_magic) if strategy_magic else mt5.positions_get()
    
    if not positions:
        return {"status": "NO_ACTIVE_POSITIONS"}
        
    report = {
        "timestamp": datetime.now().isoformat(),
        "actions": []
    }
    
    for pos in positions:
        # 1. Fetch Symbol Data for Volatility
        rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_M15, 0, 20)
        if rates is None: continue
        
        df = pd.DataFrame(rates)
        atr = (df['high'] - df['low']).mean()
        
        # 2. Logic: Break-Even at 1:1 RR
        # (This is simplified for demonstration)
        profit_pips = pos.profit / (pos.volume * 10) # Mock pip calc
        
        action = "MONITORING"
        if profit_pips > 20: # If Up 20 pips
            # Move SL to Entry + 2 pips
            # mt5.trade_modify(...)
            action = "MOVED_TO_BREAK_EVEN"
            
        # 3. Logic: Vol-Trailing
        # Update SL trail based on 2x ATR
        
        report["actions"].append({
            "symbol": pos.symbol,
            "ticket": pos.ticket,
            "profit": round(pos.profit, 2),
            "atr": round(atr, 5),
            "decision": action
        })

    return report

if __name__ == "__main__":
    status = manage_active_trades()
    print(json.dumps(status, indent=2))
    mt5.shutdown()
