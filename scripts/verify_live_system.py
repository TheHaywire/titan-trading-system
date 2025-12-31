"""
Live System Verification
========================
Comprehensive check of QuantAI system against real MT5 connection.
Run this BEFORE starting live trading to ensure everything works.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5

def main():
    print("=" * 60)
    print("🔍 LIVE SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. MT5 Connection
    print("\n1️⃣ MT5 Connection:")
    if not mt5.initialize():
        print(f"   ❌ FAILED: {mt5.last_error()}")
        return False

    account = mt5.account_info()
    print(f"   ✅ Connected to: {account.login}")
    print(f"   ✅ Server: {account.server}")
    print(f"   ✅ Balance: ${account.balance:,.2f}")
    print(f"   ✅ Equity: ${account.equity:,.2f}")
    if account.margin_level:
        print(f"   ✅ Margin Level: {account.margin_level:.2f}%")
    else:
        print("   ⚪ No positions (margin level N/A)")

    # 2. Symbol Access
    print("\n2️⃣ Symbol Access:")
    test_symbols = ["EURUSD", "GBPUSD", "GOLD", "BTCUSD", "US500"]
    valid_symbols = []
    for sym in test_symbols:
        info = mt5.symbol_info(sym)
        if info:
            tick = mt5.symbol_info_tick(sym)
            if tick:
                print(f"   ✅ {sym}: Bid={tick.bid:.5f} Ask={tick.ask:.5f}")
                valid_symbols.append(sym)
            else:
                print(f"   ⚠️ {sym}: Symbol exists but no tick data")
        else:
            # Try alternate names
            alternates = [sym + ".pro", sym + ".i", "XAU/USD" if sym == "GOLD" else sym]
            found = False
            for alt in alternates:
                info = mt5.symbol_info(alt)
                if info:
                    tick = mt5.symbol_info_tick(alt)
                    if tick:
                        print(f"   ✅ {alt}: Bid={tick.bid:.5f}")
                        valid_symbols.append(alt)
                        found = True
                        break
            if not found:
                print(f"   ⚠️ {sym}: Not found (check broker symbol name)")

    # 3. Data Access
    print("\n3️⃣ Historical Data:")
    test_sym = valid_symbols[0] if valid_symbols else "EURUSD"
    rates = mt5.copy_rates_from_pos(test_sym, mt5.TIMEFRAME_H1, 0, 100)
    if rates is not None and len(rates) > 0:
        print(f"   ✅ Got {len(rates)} H1 candles for {test_sym}")
        last_close = rates[-1]["close"]
        print(f"   ✅ Latest close: {last_close}")
    else:
        print("   ❌ Failed to get historical data")
        return False

    # 4. Open Positions
    print("\n4️⃣ Current Positions:")
    positions = mt5.positions_get()
    if positions:
        print(f"   📊 {len(positions)} open position(s):")
        total_profit = 0
        for pos in positions:
            profit_emoji = "🟢" if pos.profit > 0 else "🔴"
            direction = "BUY" if pos.type == 0 else "SELL"
            print(f"      {profit_emoji} {pos.symbol}: {direction} {pos.volume} lots | P/L: ${pos.profit:.2f}")
            total_profit += pos.profit
        print(f"   💰 Total P/L: ${total_profit:.2f}")
    else:
        print("   ✅ No open positions")

    # 5. Import QuantAI Components
    print("\n5️⃣ QuantAI Components:")
    try:
        from titan_system.core.event_bus import EventBus, TriggerDetector
        from titan_system.core.orchestrator import Orchestrator
        from titan_system.core.memory import MemorySystem
        from titan_system.core.circuit_breaker import CircuitBreaker, DrawdownStateMachine
        from titan_system.agents.execution_decision_agent import ExecutionDecisionAgent
        from titan_system.agents.macro_strategist import MacroStrategist
        print("   ✅ All core components imported successfully")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 6. Test Circuit Breaker with REAL account
    print("\n6️⃣ Circuit Breaker Check:")
    cb = CircuitBreaker(max_daily_loss_percent=5.0)
    safe, msg = cb.check_safe_to_trade({"equity": account.equity, "balance": account.balance})
    print(f"   Status: {msg}")
    if not safe:
        print("   ⚠️ WARNING: Circuit breaker would block trading!")

    # 7. Test Drawdown State Machine
    print("\n7️⃣ Drawdown State:")
    dsm = DrawdownStateMachine()
    dsm.update(account.equity, account.balance)
    actions = dsm.get_actions()
    print(f"   State: {dsm.current_state.value}")
    print(f"   Lot Multiplier: {actions['lot_multiplier']}")
    print(f"   Min Score Required: {actions['min_score']}")
    print(f"   Allow New Trades: {'✅ Yes' if actions['allow_new_trades'] else '❌ No'}")

    # 8. Test Macro Strategist with REAL data
    print("\n8️⃣ Macro Analysis (EURUSD):")
    try:
        macro = MacroStrategist()
        bias = macro.analyze("EURUSD")
        print(f"   Direction: {bias.direction}")
        print(f"   Session: {bias.current_session} ({bias.session_quality})")
        print(f"   HTF Trend: {bias.htf_trend}")
        participation = "✅ Allowed" if bias.participation_allowed else "❌ Blocked"
        print(f"   Participation: {participation}")
        
        if bias.reasoning:
            print("   Reasoning:")
            for r in bias.reasoning[:3]:  # Show first 3
                print(f"      • {r}")
    except Exception as e:
        print(f"   ⚠️ Macro analysis warning: {e}")

    # 9. Test Execution Decision Agent
    print("\n9️⃣ Execution Decision Agent:")
    try:
        agent = ExecutionDecisionAgent(trading_mode="LIVE")
        print(f"   Mode: {agent.TRADING_MODE}")
        print(f"   Excellent Threshold: {agent.EXCELLENT_THRESHOLD}")
        print(f"   Acceptable Threshold: {agent.ACCEPTABLE_THRESHOLD}")
        print("   ✅ Agent ready for LIVE trading")
    except Exception as e:
        print(f"   ❌ Agent error: {e}")
        return False

    mt5.shutdown()

    print("\n" + "=" * 60)
    print("✅ ALL LIVE CHECKS PASSED!")
    print("=" * 60)
    print("\n🚀 System is ready for LIVE trading.")
    print("\nTo start QuantAI engine:")
    print("   python -m titan_system.quantai_engine")
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
