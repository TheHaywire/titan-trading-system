"""
Full SMC System Test
Runs the complete Institutional Engine (TE-1, VE-2, ME-1, LE-1) on GOLD
"""

import MetaTrader5 as mt5
import pandas as pd
from config.settings import settings
from titan_system.smc.institutional_engine import InstitutionalEngine

def run_test():
    if not mt5.initialize():
        print("MT5 Init Failed")
        return

    if settings.mt5_login:
        mt5.login(settings.mt5_login, settings.mt5_password, settings.mt5_server)

    symbol = "GOLD"
    print(f"\n🔬 RUNNING INSTITUTIONAL DIAGNOSTICS ON {symbol}...")
    
    # 1. Fetch Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
    df = pd.DataFrame(rates)
    
    # 2. Initialize Engine
    engine = InstitutionalEngine()
    
    # 3. Analyze
    result = engine.analyze_symbol(df, symbol)
    
    # 4. Report
    print(f"\n📊 REGIME: {result['regime']}")
    
    print("\n📈 TREND ENGINE (TE-1)")
    print(f"Bias: {result['trend']['bias']}")
    print(f"TSS Score: {result['trend']['tss']}/5")
    print(f"EMA Alignment: {result['trend']['ema_alignment']}")
    print(f"EMA50 Slope: {result['trend']['slope_50']:.4f}")
    
    print("\n🌊 VWAP ENGINE (VE-2)")
    print(f"Current VWAP: {result['vwap']['vwap']:.2f}")
    print(f"VWAP Regime: {result['vwap']['regime']}")
    
    print("\n🚀 MOMENTUM ENGINE (ME-1)")
    print(f"RSI: {result['momentum']['rsi']:.1f} ({result['momentum']['rsi_zone']})")
    print(f"ROC: {result['momentum']['roc']:.2f}%")
    
    print("\n💥 VOLATILITY ENGINE (VE-1)")
    print(f"ATR: {result['volatility']['atr']:.2f}")
    print(f"Regime: {result['volatility']['regime']}")
    print(f"Compression: {result['volatility']['compression']}")

    print("\n💧 LIQUIDITY (LE-1)")
    if result['liquidity']['sweeps']:
        for sweep in result['liquidity']['sweeps']:
             print(f"⚠️ SWEEP DETECTED: {sweep['sweep_type']} at {sweep['level']:.2f}")
    else:
        print("No major sweeps detected nearby.")
        
    print("\n🚀 SETUPS IDENTIFIED")
    if result['setup']:
        for setup in result['setup']:
            print(f"🔥 {setup['name']} | {setup.get('trigger', '')} {setup.get('entry', '')}")
    else:
        print("No valid institutional setups found right now.")

    mt5.shutdown()

if __name__ == "__main__":
    run_test()
