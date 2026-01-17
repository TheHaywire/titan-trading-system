"""
PRE-TRADE EXECUTION HOOK
========================
Institutional risk gate that runs BEFORE any order is sent to MT5.
All checks must PASS for the trade to proceed.
"""

import sys
import os
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Skill imports via subprocess for isolation
import subprocess

SKILLS = {
    "heartbeat": ".agent/skills/mt5_bridge/scripts/heartbeat_monitor.py",
    "macro": ".agent/skills/data_intelligence/scripts/macro_context.py",
    "kelly": ".agent/skills/factor_risk/scripts/dynamic_kelly_allocator.py",
    "audit": ".agent/skills/mt5_bridge/scripts/audit_trail_manager.py"
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

def pre_trade_gate(symbol: str, direction: str, lots: float, entry_price: float = None):
    """
    Run all pre-trade checks. Returns gate status.
    
    Args:
        symbol: Trading symbol (e.g., "GOLD")
        direction: "BUY" or "SELL"
        lots: Proposed position size
        entry_price: Optional entry price
        
    Returns:
        dict: {"gate": "PASS"/"BLOCKED", "checks": [...], "reason": "..."}
    """
    checks = []
    blocked_reason = None
    
    # 1. HEARTBEAT CHECK (Bridge Health)
    print("🔍 [HOOK] Checking system pulse...")
    hb = run_skill(SKILLS["heartbeat"])
    hb_status = hb.get("status", "UNKNOWN")
    checks.append({
        "name": "HEARTBEAT",
        "status": "PASS" if hb_status == "HEALTHY" else "FAIL",
        "value": hb_status
    })
    if hb_status != "HEALTHY":
        blocked_reason = f"System pulse is {hb_status}, not HEALTHY"
    
    # 2. MACRO FILTER CHECK
    print("🔍 [HOOK] Checking macro environment...")
    macro = run_skill(SKILLS["macro"], symbol)
    macro_verdict = macro.get("verdict", "UNKNOWN")
    checks.append({
        "name": "MACRO_FILTER",
        "status": "PASS" if macro_verdict != "BLOCK" else "FAIL",
        "value": macro_verdict,
        "threats": macro.get("active_threats", [])
    })
    if macro_verdict == "BLOCK":
        blocked_reason = f"Macro environment is BLOCKED: {macro.get('active_threats')}"
    
    # 3. DYNAMIC POSITION LIMITS (Based on Equity)
    print("🔍 [HOOK] Checking dynamic position limits...")
    import subprocess
    cmd = [sys.executable, "position_enforcer.py", "--symbol", symbol, "--lots", str(lots), "--json-only"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    
    try:
        data = json.loads(res.stdout)
        
        if not data.get("allowed"):
            checks.append({
                "name": "POSITION_SIZE",
                "status": "FAIL",
                "proposed": lots,
                "reason": data.get("reason"),
                "suggested": data.get("suggested_lots")
            })
            blocked_reason = data.get("reason")
        else:
            checks.append({
                "name": "POSITION_SIZE",
                "status": "PASS",
                "proposed": lots,
                "equity": data.get("equity")
            })
    except Exception as e:
        print(f"⚠️ PILOT: Error parsing enforcer output: {e}")
        # Default to pass but log error
        checks.append({"name": "POSITION_SIZE", "status": "ERROR", "msg": str(e)})
    
    # 4. KELLY SIZING CHECK (Advisory)
    print("🔍 [HOOK] Validating Kelly sizing...")
    kelly = run_skill(SKILLS["kelly"])
    suggested_lots = kelly.get("suggested_lots", 0.1)
    checks.append({
        "name": "KELLY_SIZING",
        "status": "PASS" if lots <= suggested_lots else "WARN",
        "proposed": lots,
        "kelly_suggested": suggested_lots
    })
    
    # 4. TRADING HOURS CHECK (Basic)
    now = datetime.now()
    weekend = now.weekday() >= 5
    checks.append({
        "name": "TRADING_HOURS",
        "status": "FAIL" if weekend else "PASS",
        "day": now.strftime("%A")
    })
    if weekend and not blocked_reason:
        blocked_reason = "Markets are closed (weekend)"
    
    # Determine final gate status
    all_passed = all(c["status"] == "PASS" for c in checks)
    gate_status = "PASS" if all_passed else "BLOCKED"
    
    result = {
        "gate": gate_status,
        "timestamp": datetime.now().isoformat(),
        "symbol": symbol,
        "direction": direction,
        "lots": lots,
        "checks": checks,
        "reason": blocked_reason
    }
    
    # Log to audit trail
    run_skill(SKILLS["audit"], "PRE_TRADE_HOOK", "Gate Check", gate_status, json.dumps(result))
    
    return result

def main():
    parser = argparse.ArgumentParser(description="Pre-trade execution hook")
    parser.add_argument("--symbol", type=str, default="GOLD", help="Trading symbol")
    parser.add_argument("--direction", type=str, default="BUY", help="BUY or SELL")
    parser.add_argument("--lots", type=float, default=0.1, help="Position size")
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Running pre-trade hook in TEST mode...")
        args.symbol = "GOLD"
        args.direction = "BUY"
        args.lots = 0.1
    
    result = pre_trade_gate(args.symbol, args.direction, args.lots)
    
    print("\n" + "="*50)
    if result["gate"] == "PASS":
        print("✅ PRE-TRADE GATE: PASS")
    else:
        print(f"🛑 PRE-TRADE GATE: BLOCKED")
        print(f"   Reason: {result['reason']}")
    print("="*50)
    
    for check in result["checks"]:
        status_emoji = "✅" if check["status"] == "PASS" else "❌"
        print(f"   {status_emoji} {check['name']}: {check.get('value', check.get('status'))}")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
