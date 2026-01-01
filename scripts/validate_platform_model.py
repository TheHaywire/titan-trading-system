"""
Institutional Platform Validator (EPIC-01)
Verifies broker-specific execution models, account types, and order precision.
"""

import MetaTrader5 as mt5
import pandas as pd
import sys
import os

def validate_platform():
    if not mt5.initialize():
        print("❌ MT5 Initialization Failed")
        return

    print("🏛️ Starting Institutional Platform Validation...")
    
    # 1. Account Model Check
    acc = mt5.account_info()
    if acc is None:
        print("❌ Could not fetch account info")
        return

    print(f"\n[ACCOUNT MODEL]")
    print(f"- Broker: {acc.company}")
    print(f"- Account ID: {acc.login}")
    print(f"- Currency: {acc.currency}")
    print(f"- Leverage: 1:{acc.leverage}")
    
    # Margin Mode: 0=Individual, 1=Netted, 2=Exchange, 3=Hedging
    margin_modes = {0: "Individual", 1: "Netted", 2: "Exchange", 3: "Hedging"}
    mode = margin_modes.get(acc.margin_mode, "Unknown")
    print(f"- Margin Mode: {mode}")

    # 2. Execution & Filling Mode Probe (on EURUSD)
    symbol = "EURUSD"
    mt5.symbol_select(symbol, True)
    s_info = mt5.symbol_info(symbol)
    
    if s_info:
        print(f"\n[SYMBOL PRECISION: {symbol}]")
        print(f"- Digits: {s_info.digits}")
        print(f"- Contract Size: {s_info.trade_contract_size}")
        print(f"- Tick Size: {s_info.trade_tick_size}")
        print(f"- Tick Value: {s_info.trade_tick_value}")
        
        # Filling Mode discovery
        fm = s_info.filling_mode
        filling_modes = []
        if fm & 1: filling_modes.append("FOK")
        if fm & 2: filling_modes.append("IOC")
        if not filling_modes: filling_modes.append("BOC/RETURN (Default)")
        print(f"- Allowed Filling Modes (raw {fm}): {', '.join(filling_modes)}")

    # 3. Connectivity Health (EPIC-02 Initial)
    terminal = mt5.terminal_info()
    print(f"\n[TERMINAL HEALTH]")
    print(f"- Connected: {terminal.connected}")
    print(f"- Trade Allowed: {terminal.trade_allowed}")
    print(f"- DLL Allowed: {terminal.dlls_allowed}")

    mt5.shutdown()
    print("\n✅ Platform Validation Complete.")

if __name__ == "__main__":
    validate_platform()
