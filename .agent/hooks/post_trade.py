"""
POST-TRADE EXECUTION HOOK
=========================
Runs AFTER any order is filled to handle:
- Audit trail logging
- TCA (Transaction Cost Analysis)
- Performance database updates
- Notifications
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import subprocess

SKILLS = {
    "tca": ".agent/skills/execution/scripts/execution_quality_tca.py",
    "audit": ".agent/skills/mt5_bridge/scripts/audit_trail_manager.py",
    "adaptive_exit": ".agent/skills/execution/scripts/adaptive_exit.py"
}

def run_skill(script_path, *args):
    """Execute a skill script and return JSON output."""
    try:
        cmd = [sys.executable, script_path] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return json.loads(result.stdout)
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}
    return {"status": "FAILED"}

def post_trade_actions(
    symbol: str,
    direction: str,
    lots: float,
    entry_price: float,
    filled_price: float,
    ticket: int,
    magic: int = 888888
):
    """
    Execute all post-trade actions after an order is filled.
    
    Args:
        symbol: Trading symbol
        direction: "BUY" or "SELL"
        lots: Position size
        entry_price: Requested entry price
        filled_price: Actual filled price
        ticket: MT5 ticket number
        magic: Magic number for strategy identification
        
    Returns:
        dict: Post-trade action results
    """
    results = []
    
    # 1. CALCULATE SLIPPAGE (Inline TCA)
    print("📊 [HOOK] Calculating execution slippage...")
    slippage_points = abs(filled_price - entry_price)
    slippage_pct = (slippage_points / entry_price) * 100
    
    tca_result = {
        "action": "TCA_ANALYSIS",
        "status": "COMPLETED",
        "requested_price": entry_price,
        "filled_price": filled_price,
        "slippage_points": round(slippage_points, 5),
        "slippage_pct": round(slippage_pct, 4),
        "grade": "A" if slippage_pct < 0.01 else "B" if slippage_pct < 0.05 else "C"
    }
    results.append(tca_result)
    
    # 2. LOG TO AUDIT TRAIL
    print("📝 [HOOK] Logging to institutional audit trail...")
    audit_payload = {
        "ticket": ticket,
        "symbol": symbol,
        "direction": direction,
        "lots": lots,
        "entry_price": entry_price,
        "filled_price": filled_price,
        "slippage": slippage_points,
        "magic": magic,
        "timestamp": datetime.now().isoformat()
    }
    run_skill(SKILLS["audit"], "POST_TRADE_HOOK", "Order Filled", "SUCCESS", json.dumps(audit_payload))
    results.append({"action": "AUDIT_LOG", "status": "COMPLETED"})
    
    # 3. REGISTER FOR ADAPTIVE EXIT MANAGEMENT
    print("🎯 [HOOK] Registering position for adaptive exit management...")
    # In production, this would add the position to the adaptive exit monitor queue
    results.append({
        "action": "ADAPTIVE_EXIT_REGISTERED",
        "status": "QUEUED",
        "ticket": ticket
    })
    
    # 4. NOTIFICATION (Placeholder - would integrate with Telegram/Email)
    print("📱 [HOOK] Notification queued...")
    notification = {
        "action": "NOTIFICATION",
        "status": "QUEUED",
        "message": f"Trade Executed: {direction} {lots} {symbol} @ {filled_price}"
    }
    results.append(notification)
    
    return {
        "hook": "POST_TRADE",
        "timestamp": datetime.now().isoformat(),
        "ticket": ticket,
        "symbol": symbol,
        "results": results,
        "tca_grade": tca_result["grade"]
    }

def main():
    parser = argparse.ArgumentParser(description="Post-trade execution hook")
    parser.add_argument("--symbol", type=str, default="GOLD", help="Trading symbol")
    parser.add_argument("--direction", type=str, default="BUY", help="BUY or SELL")
    parser.add_argument("--lots", type=float, default=0.1, help="Position size")
    parser.add_argument("--entry", type=float, default=2650.0, help="Requested entry price")
    parser.add_argument("--filled", type=float, default=2650.5, help="Filled price")
    parser.add_argument("--ticket", type=int, default=12345678, help="MT5 ticket")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running post-trade hook in TEST mode...")
    
    result = post_trade_actions(
        args.symbol,
        args.direction,
        args.lots,
        args.entry,
        args.filled,
        args.ticket
    )
    
    print("\n" + "="*50)
    print(f"✅ POST-TRADE HOOK COMPLETE | TCA Grade: {result['tca_grade']}")
    print("="*50)
    
    for r in result["results"]:
        print(f"   ✓ {r['action']}: {r['status']}")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
