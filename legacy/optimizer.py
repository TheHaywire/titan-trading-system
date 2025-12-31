import pandas as pd
import ta
from mt5_interface import MT5Interface
import MetaTrader5 as mt5

# Simple Backtest Function for Optimization
def run_backtest(df, short_window, long_window):
    """
    Runs a vectorized backtest on the dataframe.
    Returns Total Return (Change in %)
    """
    # Create copies to avoid SettingWithCopy warnings
    data = df.copy()
    
    # Calculate Indicators
    data['sma_short'] = ta.trend.sma_indicator(data['close'], window=short_window)
    data['sma_long'] = ta.trend.sma_indicator(data['close'], window=long_window)
    
    # Generate Signals
    data['signal'] = 0
    data.loc[data['sma_short'] > data['sma_long'], 'signal'] = 1 # Long
    data.loc[data['sma_short'] < data['sma_long'], 'signal'] = -1 # Short (or Exit if long only)
    
    # Calculate Daily Returns 
    # For simplicity: Strategy Return = Signal(prev) * Market Return
    # signal shifted by 1 because signal at t uses close at t, so we trade at t+1 (or assume close execution)
    # Actually, in this simple vector model, if signal is 1 at T, we hold from T to T+1.
    
    data['market_return'] = data['close'].pct_change()
    data['strategy_return'] = data['signal'].shift(1) * data['market_return']
    
    # Cumulative Return
    data['cumulative_market_return'] = (1 + data['market_return']).cumprod()
    data['cumulative_strategy_return'] = (1 + data['strategy_return']).cumprod()
    
    final_return = data['cumulative_strategy_return'].iloc[-1]
    return final_return

def optimize(symbol, timeframe):
    print(f"Optimizing {symbol}...")
    
    # 1. Get Data
    # For optimization, we use the interface to get fresh data, 
    # or we could load from CSV if downloaded. Let's use direct interface for seamlessness.
    mt5_interface = MT5Interface()
    if not mt5_interface.start():
        return
        
    df = mt5_interface.get_closes(symbol, timeframe, num_candles=5000)
    mt5_interface.shutdown()
    
    if df is None:
        return

    # 2. Grid Search Ranges
    short_windows = range(10, 100, 10)
    long_windows = range(50, 300, 50)
    
    best_return = 0
    best_params = (0, 0)
    
    results = []
    
    for fast in short_windows:
        for slow in long_windows:
            if fast >= slow:
                continue
                
            final_ret = run_backtest(df, fast, slow)
            results.append((fast, slow, final_ret))
            
            print(f"Fast: {fast}, Slow: {slow} -> Return: {final_ret:.4f}")
            
            if final_ret > best_return:
                best_return = final_ret
                best_params = (fast, slow)

    print("\n--- Optimization Complete ---")
    print(f"Best Parameters: Short={best_params[0]}, Long={best_params[1]}")
    print(f"Best Return: {best_return:.4f} (Factor)")
    
    results_df = pd.DataFrame(results, columns=['Short', 'Long', 'Return'])
    results_df = results_df.sort_values(by='Return', ascending=False)
    print("\nTop 5 Setups:")
    print(results_df.head())

if __name__ == "__main__":
    optimize("EURUSD", mt5.TIMEFRAME_H1)
