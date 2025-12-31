import os
import sys
# Add parent directory to path so we can import titan_system
sys.path.append(os.path.join(os.getcwd()))

from titan_system.data.loader import DataLoader
from titan_system.backtest.vector_engine import VectorBacktester
from titan_system.backtest.indicators import compute_rsi, compute_sma
import polars as pl
import MetaTrader5 as mt5

def simple_rsi_strategy(df):
    """
    Example Strategy: 
    Buy when RSI < 30
    Sell when RSI > 70
    """
    # Calculate Indicators
    rsi = compute_rsi(pl.col("close"), period=14)
    
    # Generate Signals
    # 1 where RSI < 30, -1 where RSI > 70, else 0
    
    # Polars when().then().otherwise()
    signal = pl.when(rsi < 30).then(1)\
               .when(rsi > 70).then(-1)\
               .otherwise(0)
               
    return df.with_columns(signal.alias("signal"))

from titan_system.backtest.strategies.vector_gold import institutional_gold_vector_strategy

def main():
    print("🧪 Titan Research Lab 🧪")
    
    # 1. Setup Data
    loader = DataLoader(data_dir="titan_system/data/history")
    symbol = "XAUUSD"
    filename = "XAUUSD_M1.csv"
    filepath = os.path.join(loader.data_dir, filename)
    
    if not os.path.exists(filepath):
        print(f"📉 Data for {symbol} not found. Fetching from MT5...")
        # Fetch MORE data for a real test
        df = loader.fetch_history(symbol, mt5.TIMEFRAME_M1, n_bars=100000)
        if df is not None:
            loader.save_data(df, filename)
        else:
            print("❌ Critical Error: Could not fetch data.")
            return

    # 2. Run Backtest
    print(f"\n🚀 Running Institutional GOLD Strategy on {symbol}...")
    engine = VectorBacktester(filepath, symbol)
    
    results = engine.run(institutional_gold_vector_strategy)
    
    if results:
        print("\n📈 Final Results:")
        print(f"   Return: {results['total_return']*100:.2f}%")
        print(f"   Win Rate: {results['win_rate']:.1f}%")

if __name__ == "__main__":
    main()
