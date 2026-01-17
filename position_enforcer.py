"""
MAX POSITION SIZE ENFORCER
==========================
Checks BEFORE any trade and blocks oversized positions.
Integrates with the pre-trade hook.
"""

import MetaTrader5 as mt5
import json
from datetime import datetime

# DYNAMIC LIMITS (Based on Equity)
# Support for 'AGGRESSIVE' mode for exponential growth
import os
RISK_MODE = os.getenv("TITAN_RISK_MODE", "CONSERVATIVE")

if RISK_MODE == "AGGRESSIVE":
    MAX_LOTS_PER_1K_EQUITY = 0.15  # 0.15 lots per $1000 equity (Aggressive)
    MAX_EQUITY_RISK_PCT = 5.0      # Max 5% risk per trade
    MAX_POSITIONS = 20             # Higher count allowed for scaling
else:
    MAX_LOTS_PER_1K_EQUITY = 0.05  # 0.05 lots per $1000 equity (Conservative)
    MAX_EQUITY_RISK_PCT = 2.0      # Max 2% risk per trade
    MAX_POSITIONS = 10             # Limit count to prevent spam

def check_position_size(symbol: str, proposed_lots: float, entry_price: float = None, sl_price: float = None):
    """
    Validate if a proposed trade meets position size limits.
    Returns: {"allowed": True/False, "reason": "...", "suggested_lots": X}
    """
    if not mt5.initialize():
        return {"allowed": False, "reason": "MT5 connection failed"}
    
    try:
        account = mt5.account_info()
        positions = mt5.positions_get()
        
        equity = account.equity
        max_lots_allowed = (equity / 1000) * MAX_LOTS_PER_1K_EQUITY
        
        # Ensure a minimum lot size (e.g. 0.01) if equity is very low
        max_lots_allowed = max(0.01, round(max_lots_allowed, 2))
        
        # Check 1: Dynamic lot limit
        if proposed_lots > max_lots_allowed:
            return {
                "allowed": False,
                "reason": f"Exceeds dynamic limit for ${equity:,.2f} equity ({max_lots_allowed} lots)",
                "proposed": proposed_lots,
                "max_allowed": max_lots_allowed,
                "suggested_lots": max_lots_allowed
            }
        
        # Check 2: Total exposure limit (e.g. 5x single trade limit)
        max_total_lots = max_lots_allowed * 5
        current_lots = sum(p.volume for p in positions) if positions else 0
        if current_lots + proposed_lots > max_total_lots:
            available = max_total_lots - current_lots
            return {
                "allowed": False,
                "reason": f"Would exceed max total portfolio exposure ({max_total_lots} lots)",
                "current_lots": current_lots,
                "proposed": proposed_lots,
                "max_allowed": max(0, round(available, 2)),
                "suggested_lots": max(0, round(available, 2))
            }
        
        # Check 3: Position count limit
        if positions and len(positions) >= MAX_POSITIONS:
            return {
                "allowed": False,
                "reason": f"Already at max positions ({MAX_POSITIONS})",
                "current_positions": len(positions),
                "suggested_lots": 0
            }
        
        # Check 4: Risk per trade (if SL provided)
        if sl_price and entry_price:
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                point_value = symbol_info.trade_tick_value
                sl_points = abs(entry_price - sl_price) / symbol_info.point
                risk_amount = sl_points * point_value * proposed_lots
                risk_pct = (risk_amount / equity) * 100
                
                if risk_pct > MAX_RISK_PER_TRADE_PCT:
                    # Calculate safe lot size
                    max_risk_amount = equity * (MAX_RISK_PER_TRADE_PCT / 100)
                    safe_lots = max_risk_amount / (sl_points * point_value)
                    
                    return {
                        "allowed": False,
                        "reason": f"Risk {risk_pct:.1f}% exceeds max {MAX_RISK_PER_TRADE_PCT}%",
                        "risk_amount": round(risk_amount, 2),
                        "max_risk": round(max_risk_amount, 2),
                        "suggested_lots": round(safe_lots, 2)
                    }
        
        # All checks passed
        return {
            "allowed": True,
            "proposed_lots": proposed_lots,
            "current_total_lots": current_lots,
            "current_positions": len(positions) if positions else 0,
            "equity": equity
        }
        
    finally:
        mt5.shutdown()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Position Size Enforcer")
    parser.add_argument("--symbol", type=str, default="GOLD", help="Symbol")
    parser.add_argument("--lots", type=float, default=0.1, help="Proposed lot size")
    parser.add_argument("--entry", type=float, help="Entry price")
    parser.add_argument("--sl", type=float, help="Stop loss price")
    parser.add_argument("--json-only", action="store_true", help="Output only JSON")
    args = parser.parse_args()
    
    result = check_position_size(args.symbol, args.lots, args.entry, args.sl)
    
    if args.json_only:
        print(json.dumps(result))
        return
        
    print("=" * 50)
    print("POSITION SIZE ENFORCEMENT")
    print("=" * 50)
    print(f"Symbol: {args.symbol}")
    print(f"Proposed Lots: {args.lots}")
    print("=" * 50)
    
    if result.get("allowed"):
        print("✅ TRADE ALLOWED")
    else:
        print("🛑 TRADE BLOCKED")
        print(f"   Reason: {result.get('reason')}")
        if result.get("suggested_lots"):
            print(f"   Suggested: {result.get('suggested_lots')} lots")
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
