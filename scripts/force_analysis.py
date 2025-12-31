"""
Force Live Analysis Demo
========================
Immediately analyzes all symbols and shows what trades WOULD be executed.
This bypasses waiting for candle closes to demonstrate the system.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime, timezone

def main():
    print("=" * 60)
    print("🔥 FORCING LIVE ANALYSIS NOW")
    print("=" * 60)

    if not mt5.initialize():
        print(f"MT5 failed: {mt5.last_error()}")
        return

    from titan_system.smc.institutional_engine import InstitutionalEngine
    from titan_system.agents.execution_decision_agent import (
        ExecutionDecisionAgent, QuantSignal, VolatilityState, RiskApproval, Direction
    )
    from titan_system.agents.macro_strategist import MacroStrategist
    from titan_system.agents.execution_decision_agent import MacroBias as MacroBiasData
    from titan_system.core.circuit_breaker import DrawdownStateMachine
    from titan_system.execution.mt5_executor import MT5Executor

    # Initialize
    inst_engine = InstitutionalEngine()
    exec_agent = ExecutionDecisionAgent(trading_mode="LIVE")
    macro = MacroStrategist()
    dsm = DrawdownStateMachine()
    executor = MT5Executor()
    executor.connect()

    account = mt5.account_info()
    dsm.update(account.equity, account.balance)
    
    print(f"\n💰 Account: {account.login}")
    print(f"💵 Equity: ${account.equity:,.2f}")

    symbols = ["EURUSD", "GBPUSD", "GOLD", "USDJPY", "BTCUSD"]
    trade_opportunities = []

    for symbol in symbols:
        print(f"\n{'='*40}")
        print(f"📊 Analyzing {symbol}")
        print("="*40)
        
        # Get data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
        if rates is None or len(rates) < 50:
            print(f"   ⚠️ Skipping - no data")
            continue
        
        df = pd.DataFrame(rates)
        
        try:
            # Institutional analysis
            analysis = inst_engine.analyze_symbol(df, symbol)
            regime = analysis.get("regime", "UNKNOWN")
            setups = analysis.get("setup", [])
            
            print(f"   Regime: {regime}")
            print(f"   Setups Found: {len(setups)}")
            
            if not setups:
                print(f"   ⏸️ No setups - conditions not ideal")
                continue
            
            setup = setups[0]
            setup_name = setup.get("name", "UNKNOWN")
            print(f"   Best Setup: {setup_name}")
            
            # Determine direction
            if "BULLISH" in setup_name or "LONG" in setup_name:
                direction = Direction.BUY
            elif "BEARISH" in setup_name or "SHORT" in setup_name:
                direction = Direction.SELL
            else:
                print(f"   ⚠️ Cannot determine direction")
                continue
            
            # Calculate score
            score = 70
            if "STRONG" in regime:
                score += 15
            
            # Get macro bias  
            bias = macro.analyze(symbol)
            print(f"   Macro Bias: {bias.direction} ({bias.session_quality})")
            print(f"   HTF Trend: {bias.htf_trend}")
            
            # Build inputs
            current_price = df.iloc[-1]["close"]
            
            quant = QuantSignal(
                symbol=symbol,
                direction=direction,
                score=score,
                setup_type=setup_name,
                entry_price=current_price,
                stop_loss=setup.get("stop", current_price * 0.99),
                take_profit=setup.get("target", current_price * 1.02),
                reasoning=[f"Setup: {setup_name}", f"Regime: {regime}"]
            )
            
            macro_data = MacroBiasData(
                direction=bias.direction,
                session_quality=bias.session_quality,
                htf_trend=bias.htf_trend,
                participation_allowed=bias.participation_allowed,
                score_adjustment=bias.score_adjustment
            )
            
            vol_data = analysis.get("volatility", {})
            vol_state = VolatilityState(
                regime=vol_data.get("regime", "NORMAL"),
                volatility=vol_data.get("state", "NORMAL"),
                lot_size_multiplier=dsm.get_actions()["lot_multiplier"]
            )
            
            risk = RiskApproval(
                approved=True,
                max_lot_size=0.01,
                drawdown_state=dsm.current_state.value
            )
            
            # EVALUATE
            print(f"\n   🧠 DECISION ENGINE EVALUATING...")
            command = exec_agent.evaluate(quant, macro_data, vol_state, risk)
            
            print(f"\n   📊 DECISION:")
            print(f"      State: {command.state.value}")
            print(f"      Action: {command.action}")
            print(f"      Score: {command.final_score:.1f}/100")
            print(f"      Lot Size: {command.lot_size}")
            
            if command.action in ["BUY", "SELL"]:
                print(f"\n   ✅ TRADEABLE OPPORTUNITY!")
                trade_opportunities.append({
                    "symbol": symbol,
                    "action": command.action,
                    "lot": command.lot_size,
                    "score": command.final_score,
                    "state": command.state.value
                })
            else:
                reason = command.rejection_reason or "Score below threshold"
                print(f"\n   ⏸️ NO TRADE: {reason}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Summary
    print("\n" + "=" * 60)
    print("📋 SUMMARY")
    print("=" * 60)
    
    if trade_opportunities:
        print(f"\n🎯 {len(trade_opportunities)} TRADE OPPORTUNITIES FOUND:\n")
        for opp in trade_opportunities:
            print(f"   {opp['symbol']}: {opp['action']} {opp['lot']} lots")
            print(f"      Score: {opp['score']:.1f} | State: {opp['state']}")
        
        print("\n⚠️ These would be executed if running in LIVE mode.")
        print("   Run: python -m titan_system.quantai_engine")
    else:
        print("\n⏸️ No trade opportunities right now.")
        print("   Current market conditions don't meet criteria.")
        print("   The system will wait for better setups.")
    
    print("\n" + "=" * 60)
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
