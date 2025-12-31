
import MetaTrader5 as mt5
import pandas as pd
import asyncio
from titan_system.strategies.divergence_hunter import DivergenceHunter
from titan_system.analytics.market_state import MarketAnalyzer
from titan_system.core.execution import MT5Execution
from config.settings import settings

async def analyze_gold():
    print("🔎 Running Deep Technical Analysis on GOLD...")
    
    # Init
    exec_engine = MT5Execution(settings)
    if not exec_engine.connect():
        print("Failed to connect.")
        return

    # 1. Market Brain Analysis (Trend, Volatility, Liquidity)
    brain = MarketAnalyzer(exec_engine)
    market_state = await brain.analyze_symbol("GOLD")
    
    print(f"\n🧠 Market Brain Outlook:")
    print(f"   Score: {market_state['score']} ({market_state['bias']})")
    for reason in market_state['reasoning']:
        print(f"   > {reason}")

    # 2. Divergence Hunter Analysis (RSI Structure)
    print(f"\n🦅 Divergence Hunter Scan:")
    hunter = DivergenceHunter()
    
    # Get M15 and H1 data
    df_m15 = exec_engine.get_data("GOLD", mt5.TIMEFRAME_M15, 200)
    df_h1 = exec_engine.get_data("GOLD", mt5.TIMEFRAME_H1, 200)
    
    if df_m15 is None or df_h1 is None:
        print("   ❌ Insufficient Data")
    else:
        # Run Scanner
        result_m15 = hunter.analyze("GOLD", df_m15)
        result_h1 = hunter.analyze("GOLD", df_h1) # Scan H1 too

        print(f"   [M15 Frame] Signal: {result_m15['signal']} | {result_m15['reason']}")
        if 'metrics' in result_m15: print(f"      Metrics: {result_m15['metrics']}")
        
        print(f"   [H1 Frame]  Signal: {result_h1['signal']} | {result_h1['reason']}")
        if 'metrics' in result_h1: print(f"      Metrics: {result_h1['metrics']}")

    exec_engine.shutdown()

if __name__ == "__main__":
    asyncio.run(analyze_gold())
