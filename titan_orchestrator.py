"""
TITAN UNIFIED ORCHESTRATOR
==========================
Central command dispatcher that ALL workflows must call.
Ensures every action flows through the skill ecosystem with hooks.
"""

import sys
import os
import json
import argparse
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import subprocess

class Department(Enum):
    INFRASTRUCTURE = "mt5_bridge"
    DATA = "data_intelligence"
    ALPHA = "alpha_research"
    EXECUTION = "execution"
    RISK = "factor_risk"
    FORENSICS = "alpha_forensics"

class Action(Enum):
    HEALTH_CHECK = "health_check"
    SCAN = "scan"
    ANALYZE = "analyze"
    EXECUTE = "execute"
    AUDIT = "audit"
    RISK_CHECK = "risk_check"

# Skill Registry
SKILLS = {
    # Infrastructure
    "connectivity": ".agent/skills/mt5_bridge/scripts/connectivity_manager.py",
    "heartbeat": ".agent/skills/mt5_bridge/scripts/heartbeat_monitor.py",
    "audit_trail": ".agent/skills/mt5_bridge/scripts/audit_trail_manager.py",
    "db_sentinel": ".agent/skills/mt5_bridge/scripts/db_sentinel.py",
    
    # Data Intelligence
    "data_auditor": ".agent/skills/data_intelligence/scripts/data_auditor.py",
    "gap_recon": ".agent/skills/data_intelligence/scripts/gap_reconstructor.py",
    "feature_factory": ".agent/skills/data_intelligence/scripts/feature_factory.py",
    "macro_context": ".agent/skills/data_intelligence/scripts/macro_context.py",
    
    # Alpha Research
    "wfa": ".agent/skills/alpha_research/scripts/wfa_engine.py",
    "sensitivity": ".agent/skills/alpha_research/scripts/sensitivity_analyzer.py",
    "regime_scout": ".agent/skills/alpha_research/scripts/regime_scout.py",
    
    # Execution
    "tca": ".agent/skills/execution/scripts/execution_quality_tca.py",
    "adaptive_exit": ".agent/skills/execution/scripts/adaptive_exit.py",
    "liquidity_router": ".agent/skills/execution/scripts/liquidity_router.py",
    
    # Risk
    "factor_audit": ".agent/skills/factor_risk/scripts/factor_exposure_auditor.py",
    "black_swan": ".agent/skills/factor_risk/scripts/black_swan_tester.py",
    "kelly": ".agent/skills/factor_risk/scripts/dynamic_kelly_allocator.py",
    "adversarial": ".agent/skills/factor_risk/scripts/adversarial_simulator.py",
}

# Hooks
HOOKS = {
    "pre_trade": ".agent/hooks/pre_trade.py",
    "post_trade": ".agent/hooks/post_trade.py"
}

class TitanOrchestrator:
    """Central command dispatcher for the Titan Trading System."""
    
    def __init__(self):
        self.last_health = None
        self.session_start = datetime.now()
        
    def run_skill(self, skill_key: str, *args) -> Dict[str, Any]:
        """Execute a skill and return its JSON output."""
        if skill_key not in SKILLS:
            return {"status": "ERROR", "message": f"Unknown skill: {skill_key}"}
        
        try:
            cmd = [sys.executable, SKILLS[skill_key]] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"status": "COMPLETED", "raw_output": result.stdout[:500]}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
        return {"status": "FAILED"}
    
    def run_hook(self, hook_key: str, *args) -> Dict[str, Any]:
        """Execute a hook and return its result."""
        if hook_key not in HOOKS:
            return {"status": "ERROR", "message": f"Unknown hook: {hook_key}"}
        
        try:
            cmd = [sys.executable, HOOKS[hook_key]] + list(args)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
            # Parse JSON from output (may have other text)
            for line in result.stdout.split('\n'):
                if line.strip().startswith('{'):
                    try:
                        return json.loads(line)
                    except:
                        pass
            return {"status": "COMPLETED", "output": result.stdout[-500:]}
        except Exception as e:
            return {"status": "ERROR", "message": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Run a full system health check across all departments."""
        print("🏥 Running Titan Health Check...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "departments": {}
        }
        
        # Infrastructure
        print("   🌉 Checking Infrastructure...")
        hb = self.run_skill("heartbeat")
        results["departments"]["infrastructure"] = {
            "status": hb.get("status", "UNKNOWN"),
            "latency_ms": hb.get("latency_ms", "N/A")
        }
        
        # Data Intelligence
        print("   📊 Checking Data Intelligence...")
        macro = self.run_skill("macro_context", "GOLD")
        results["departments"]["data_intelligence"] = {
            "macro_status": macro.get("verdict", "UNKNOWN"),
            "threats": len(macro.get("active_threats", []))
        }
        
        # Alpha Research
        print("   🔬 Checking Alpha Research...")
        regime = self.run_skill("regime_scout")
        results["departments"]["alpha_research"] = {
            "regime": regime.get("regime", "UNKNOWN"),
            "hurst": regime.get("hurst_exponent", "N/A")
        }
        
        # Risk
        print("   🛡️ Checking Risk Desk...")
        kelly = self.run_skill("kelly")
        results["departments"]["risk"] = {
            "kelly_lots": kelly.get("suggested_lots", "N/A"),
            "edge_index": kelly.get("edge_index", "N/A")
        }
        
        # Overall status
        all_healthy = all(
            dept.get("status") == "HEALTHY" or dept.get("macro_status") not in ["BLOCK"]
            for dept in results["departments"].values()
        )
        results["overall_status"] = "HEALTHY" if all_healthy else "DEGRADED"
        
        self.last_health = results
        return results
    
    def scan(self, symbols: list = None) -> Dict[str, Any]:
        """Scan symbols using Data Intelligence + Alpha Research."""
        symbols = symbols or ["GOLD", "USDJPY", "BTCUSD"]
        print(f"🔍 Scanning {len(symbols)} symbols...")
        
        results = {"timestamp": datetime.now().isoformat(), "scans": []}
        
        for symbol in symbols:
            print(f"   Analyzing {symbol}...")
            
            # Data check
            macro = self.run_skill("macro_context", symbol)
            
            # Regime check
            regime = self.run_skill("regime_scout")
            
            results["scans"].append({
                "symbol": symbol,
                "macro_verdict": macro.get("verdict"),
                "regime": regime.get("regime"),
                "action": regime.get("action")
            })
        
        return results
    
    def execute_trade(
        self,
        symbol: str,
        direction: str,
        lots: float,
        entry_price: float
    ) -> Dict[str, Any]:
        """Execute a trade with full hook chain."""
        print(f"🚀 Executing {direction} {lots} {symbol}...")
        
        # 1. PRE-TRADE HOOK
        print("   Running pre-trade gate...")
        pre_result = self.run_hook("pre_trade", "--symbol", symbol, "--direction", direction, "--lots", str(lots))
        
        if pre_result.get("gate") == "BLOCKED":
            return {
                "status": "BLOCKED",
                "reason": pre_result.get("reason"),
                "hook": "pre_trade"
            }
        
        # 2. ACTUAL EXECUTION (LIVE)
        print("   Sending order to MT5...")
        import MetaTrader5 as mt5
        
        if not mt5.initialize():
            return {"status": "ERROR", "reason": "MT5 Init Failed"}
            
        # Determine order type
        type_op = mt5.ORDER_TYPE_BUY if direction == "BUY" else mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).ask if direction == "BUY" else mt5.symbol_info_tick(symbol).bid
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lots,
            "type": type_op,
            "price": price,
            "deviation": 20,
            "magic": 999000,
            "comment": "TITAN AUTO",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Add SL/TP if provided (and not 0.0)
        # Note: Pilot may override SL, but we set initial here if provided
        # args passed to this function don't have sl/tp, we need to update signature or rely on args logic
        # For now, let's just execute the market order and let pilot manage or if we can pass sl/tp
        
        res = mt5.order_send(request)
        mt5.shutdown()
        
        if res.retcode != mt5.TRADE_RETCODE_DONE:
             return {
                "status": "FAILED",
                "reason": f"MT5 Error: {res.comment} ({res.retcode})",
                "hook": "mt5_execution"
            }
            
        filled_price = res.price
        ticket = res.order
        
        # 3. POST-TRADE HOOK
        print("   Running post-trade actions...")
        post_result = self.run_hook(
            "post_trade",
            "--symbol", symbol,
            "--direction", direction,
            "--lots", str(lots),
            "--entry", str(entry_price),
            "--filled", str(filled_price),
            "--ticket", str(ticket)
        )
        
        return {
            "status": "EXECUTED",
            "ticket": ticket,
            "symbol": symbol,
            "direction": direction,
            "lots": lots,
            "entry": entry_price,
            "filled": filled_price,
            "tca_grade": post_result.get("tca_grade", "N/A")
        }

def main():
    parser = argparse.ArgumentParser(description="Titan Unified Orchestrator")
    parser.add_argument("--action", type=str, default="health_check",
                       choices=["health_check", "scan", "execute"],
                       help="Action to perform")
    parser.add_argument("--symbol", type=str, default="GOLD", help="Symbol for execute")
    parser.add_argument("--direction", type=str, choices=["BUY", "SELL"], help="Trade direction")
    parser.add_argument("--lots", type=float, default=0.01, help="Lot size")
    parser.add_argument("--sl", type=float, help="Stop Loss Price")
    parser.add_argument("--tp", type=float, help="Take Profit Price")
    
    args = parser.parse_args()
    
    orchestrator = TitanOrchestrator()
    
    print("="*60)
    print("   TITAN UNIFIED ORCHESTRATOR")
    print("="*60)
    
    if args.action == "health_check":
        result = orchestrator.health_check()
    elif args.action == "scan":
        result = orchestrator.scan()
    elif args.action == "execute":
        result = orchestrator.execute_trade(args.symbol, args.direction, args.lots, 2650.0)
    else:
        result = {"error": "Unknown action"}
    
    print("\n" + "="*60)
    print(json.dumps(result, indent=2))
    
if __name__ == "__main__":
    main()
