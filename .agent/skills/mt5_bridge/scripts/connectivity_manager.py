"""
CONNECTIVITY MANAGER
====================
The foundation layer for MT5 Agent Skills.
Ensures correct account identity and environment (Demo vs Live).
"""

import MetaTrader5 as mt5
import json
import os

def get_system_health():
    if not mt5.initialize():
        return {
            "status": "OFFLINE",
            "error": "Terminal not found or connection failed."
        }
    
    acc = mt5.account_info()
    terminal = mt5.terminal_info()
    
    # 0 = Demo, 1 = Contest, 2 = Real
    mode_map = {0: "DEMO", 1: "CONTEST", 2: "REAL/LIVE"}
    
    health = {
        "status": "CONNECTED",
        "account": {
            "login": acc.login,
            "server": acc.server,
            "name": acc.name,
            "mode": mode_map.get(acc.trade_mode, "UNKNOWN"),
            "is_live": acc.trade_mode == 2
        },
        "terminal": {
            "path": terminal.path,
            "connected": terminal.connected,
            "dll_allowed": terminal.dlls_allowed
        },
        "risks": {
            "is_hedging": acc.margin_mode == 1,
            "leverage": acc.leverage
        }
    }
    
    # mt5.shutdown() # We keep it open if called as a bridge
    return health

if __name__ == "__main__":
    health = get_system_health()
    print(json.dumps(health, indent=2))
    mt5.shutdown()
