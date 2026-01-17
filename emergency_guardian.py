"""
EMERGENCY EQUITY GUARDIAN
=========================
HARD KILL SWITCH - When equity drops below threshold, CLOSE EVERYTHING.
No fancy analysis. No delays. Just protection.
"""

import MetaTrader5 as mt5
import sys
import json
from datetime import datetime

# CONFIGURATION - SET YOUR LIMITS
EQUITY_KILL_THRESHOLD = 3000  # Close ALL positions if equity drops below this
MAX_DRAWDOWN_PCT = 75  # Close all if drawdown exceeds this %
MAX_SINGLE_POSITION_LOSS = 1500  # Close any single position losing more than this
STARTING_BALANCE = 10000  # Your starting balance

def get_account_status():
    """Get current account state."""
    info = mt5.account_info()
    if not info:
        return None
    
    positions = mt5.positions_get()
    
    return {
        "balance": info.balance,
        "equity": info.equity,
        "margin": info.margin,
        "free_margin": info.margin_free,
        "drawdown_pct": ((info.balance - info.equity) / info.balance * 100) if info.balance > 0 else 0,
        "position_count": len(positions) if positions else 0,
        "floating_pnl": info.equity - info.balance
    }

def close_position(ticket):
    """Close a single position by ticket."""
    position = mt5.positions_get(ticket=ticket)
    if not position:
        return {"error": f"Position {ticket} not found"}
    
    pos = position[0]
    symbol = pos.symbol
    volume = pos.volume
    
    # Determine close direction
    if pos.type == 0:  # Buy position, close with sell
        close_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    else:  # Sell position, close with buy
        close_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": close_type,
        "position": ticket,
        "price": price,
        "deviation": 50,
        "magic": 999999,
        "comment": "EMERGENCY_GUARDIAN",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        return {"status": "CLOSED", "ticket": ticket, "symbol": symbol, "volume": volume}
    else:
        return {"status": "FAILED", "ticket": ticket, "error": result.comment, "retcode": result.retcode}

def close_all_positions():
    """Nuclear option - close everything."""
    positions = mt5.positions_get()
    if not positions:
        return {"message": "No positions to close"}
    
    results = []
    for pos in positions:
        result = close_position(pos.ticket)
        results.append(result)
    
    return results

def check_position_limits():
    """Check each position against limits."""
    positions = mt5.positions_get()
    if not positions:
        return []
    
    violations = []
    for pos in positions:
        if pos.profit < -MAX_SINGLE_POSITION_LOSS:
            violations.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "loss": pos.profit,
                "reason": f"Exceeds max loss limit of ${MAX_SINGLE_POSITION_LOSS}"
            })
    
    return violations

def run_guardian(auto_close=False):
    """Main guardian loop - check and act."""
    if not mt5.initialize():
        return {"error": "MT5 connection failed"}
    
    try:
        status = get_account_status()
        if not status:
            return {"error": "Could not get account status"}
        
        # Check equity threshold
        equity_breach = status["equity"] < EQUITY_KILL_THRESHOLD
        
        # Check drawdown percentage
        drawdown_breach = status["drawdown_pct"] > MAX_DRAWDOWN_PCT
        
        # Check individual position limits
        position_violations = check_position_limits()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "account": status,
            "triggers": {
                "equity_breach": equity_breach,
                "drawdown_breach": drawdown_breach,
                "position_violations": len(position_violations)
            },
            "violations": position_violations,
            "action_required": equity_breach or drawdown_breach or len(position_violations) > 0
        }
        
        if report["action_required"]:
            report["alert"] = "🚨 EMERGENCY ACTION REQUIRED"
            
            if auto_close:
                if equity_breach or drawdown_breach:
                    report["action_taken"] = "CLOSING ALL POSITIONS"
                    report["close_results"] = close_all_positions()
                elif position_violations:
                    report["action_taken"] = "CLOSING VIOLATING POSITIONS"
                    report["close_results"] = [close_position(v["ticket"]) for v in position_violations]
            else:
                report["recommendation"] = "Run with --execute flag to auto-close"
        
        return report
        
    finally:
        mt5.shutdown()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Emergency Equity Guardian")
    parser.add_argument("--execute", action="store_true", help="Actually close positions (not just report)")
    parser.add_argument("--close-all", action="store_true", help="Close ALL positions immediately")
    args = parser.parse_args()
    
    print("=" * 60)
    print("🛡️ EMERGENCY EQUITY GUARDIAN")
    print("=" * 60)
    print(f"Equity Kill Threshold: ${EQUITY_KILL_THRESHOLD}")
    print(f"Max Drawdown: {MAX_DRAWDOWN_PCT}%")
    print(f"Max Single Position Loss: ${MAX_SINGLE_POSITION_LOSS}")
    print("=" * 60)
    
    if args.close_all:
        print("\n🚨 NUCLEAR OPTION: Closing ALL positions...")
        if not mt5.initialize():
            print("MT5 connection failed")
            return
        results = close_all_positions()
        mt5.shutdown()
        print(json.dumps(results, indent=2))
    else:
        result = run_guardian(auto_close=args.execute)
        print(json.dumps(result, indent=2))
        
        if result.get("action_required"):
            print("\n" + "=" * 60)
            print("⚠️ TO CLOSE VIOLATING POSITIONS:")
            print("   python emergency_guardian.py --execute")
            print("\n⚠️ TO CLOSE ALL POSITIONS:")
            print("   python emergency_guardian.py --close-all")
            print("=" * 60)

if __name__ == "__main__":
    main()
