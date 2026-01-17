import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def run_backtest_learning(symbol, matrix_bias):
    if not mt5.initialize():
        return "MT5 Init Failed"
    
    # 1. Get Today's M15 Data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        return "No data"
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # 2. Simulate "Strict Matrix" (Only Longs in a Bullish Bias)
    # Simple strategy: Buy at open of M15 if previous bar was green, exit at close.
    matrix_pnl = []
    contrarian_pnl = []
    
    for i in range(1, len(df)):
        change = df.iloc[i]['close'] - df.iloc[i]['open']
        
        if matrix_bias == "Bullish":
            # Matrix alignment: Buy the trend
            matrix_pnl.append(change)
            # Contrarian: Sell the top
            contrarian_pnl.append(-change)
    
    # 3. Calculate Metrics
    matrix_sum = sum(matrix_pnl)
    contra_sum = sum(contrarian_pnl)
    
    matrix_dd = min(np.cumsum(matrix_pnl)) if matrix_pnl else 0
    contra_dd = min(np.cumsum(contrarian_pnl)) if contrarian_pnl else 0
    
    mt5.shutdown()
    
    return {
        "Symbol": symbol,
        "Matrix_Total": matrix_sum,
        "Contra_Total": contra_sum,
        "Matrix_Drawdown": matrix_dd,
        "Contra_Drawdown": contra_dd
    }

if __name__ == "__main__":
    results = []
    # Test High Conviction
    results.append(run_backtest_learning("US500Cash", "Bullish")) # S&P 500
    results.append(run_backtest_learning("EURUSD", "Bearish"))    # EUR/USD
    # Test Medium Conviction
    results.append(run_backtest_learning("GOLD", "Bullish"))
    results.append(run_backtest_learning("SILVER", "Bullish"))
    
    print("\n--- STATISTICAL TRUTH: TODAY'S PERFORMANCE ---")
    for r in results:
        print(r)
