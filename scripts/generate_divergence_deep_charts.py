import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
import matplotlib.pyplot as plt
from titan_system.backtest.engine import BacktestEngine
from scripts.validate_divergences_v2 import AdvancedDivergence_Strategy

def generate_deep_analysis():
    print("📈 Generating High-Fidelity Equity Curve Analysis...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    timeframe = mt5.TIMEFRAME_H4
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 1, 1)
    
    # Top 3 Strategies
    configs = [
        {'ind': ['macd'], 'mode': 'any', 'type': 'hidden', 'mtf': True},
        {'ind': ['rsi', 'macd'], 'mode': 'all', 'type': 'hidden'},
        {'ind': ['macd'], 'mode': 'any', 'type': 'hidden', 'vol': True}
    ]
    
    engine = BacktestEngine(symbol, timeframe, start_date, end_date)
    plt.figure(figsize=(12, 7))
    
    for config in configs:
        strat = AdvancedDivergence_Strategy(
            indicators=config['ind'], mode=config['mode'], div_type=config['type'],
            vol_filter=config.get('vol', False), mtf_filter=config.get('mtf', False)
        )
        print(f"Analyzing {strat.name}...")
        res = engine.run_backtest(strat)
        plt.plot(res.equity_curve, label=f"{strat.name} (Sharpe: {res.sharpe_ratio:.2f})")
    
    plt.title("Institutional Divergence - Advanced Equity Curves (24 Months)")
    plt.xlabel("Trade Number")
    plt.ylabel("Equity ($)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    report_path = "INSTITUTIONAL_DIVERGENCE_CHART.png"
    plt.savefig(report_path)
    print(f"✅ Chart saved to {report_path}")
    mt5.shutdown()

if __name__ == "__main__":
    generate_deep_analysis()
