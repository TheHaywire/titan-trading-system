"""
HEARTBEAT MONITOR
=================
Institutional connection watchdog.
Monitors RTT (Round Trip Time), connection state, and trade allowance.
"""

import MetaTrader5 as mt5
import time
import json
import socket
from datetime import datetime

def check_heartbeat():
    # 1. Connectivity Check
    start_time = time.perf_counter()
    if not mt5.initialize():
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "CRITICAL",
            "error": "MT5 Terminal Connection Failed",
            "latency_ms": -1
        }
    
    # 2. Latency (RTT) Check
    # We use terminal_info to verify responsiveness
    t_info = mt5.terminal_info()
    latency = (time.perf_counter() - start_time) * 1000
    
    # 3. Account Activity Check
    acc = mt5.account_info()
    acc_dict = acc._asdict() if acc else {}
    
    pulse = {
        "timestamp": datetime.now().isoformat(),
        "status": "HEALTHY" if t_info.connected and acc.trade_allowed else "DEGRADED",
        "latency_ms": round(latency, 2),
        "terminal": {
            "connected": getattr(t_info, 'connected', False),
            "trade_allowed": getattr(t_info, 'trade_allowed', False),
            "dll_allowed": getattr(t_info, 'dlls_allowed', False)
        },
        "account": {
            "server": acc_dict.get('server', "UNKNOWN"),
            "trade_allowed": acc_dict.get('trade_allowed', False),
            "margin_call": acc_dict.get('margin_so_call', 0),
            "margin_stopout": acc_dict.get('margin_so_out', 0)
        },
        "network": {
            "hostname": socket.gethostname(),
            "local_ip": socket.gethostbyname(socket.gethostname())
        }
    }
    
    # Alerting logic
    if latency > 200:
        pulse["status"] = "DEGRADED"
        pulse["warning"] = "High Latency Detected (>200ms)"
        
    if not t_info.connected:
        pulse["status"] = "CRITICAL"
        pulse["error"] = "Terminal Disconnected from Broker"

    return pulse

if __name__ == "__main__":
    result = check_heartbeat()
    print(json.dumps(result, indent=2))
    mt5.shutdown()
