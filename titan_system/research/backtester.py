import vectorbt as vbt
import pandas as pd
from titan_system.research.data_loader import load_data

class Backtester:
    def __init__(self, symbol: str, timeframe: str = 'H1'):
        self.symbol = symbol
        self.timeframe = timeframe
        self.data: pd.DataFrame = load_data(symbol, timeframe)
        
    def run_sma_crossover(self, fast_window: int = 10, slow_window: int = 50):
        if self.data.empty:
            print("No data to backtest.")
            return

        price = self.data['close']
        
        # Calculate MA
        fast_ma = vbt.MA.run(price, fast_window)
        slow_ma = vbt.MA.run(price, slow_window)
        
        # Entries/Exits
        entries = fast_ma.ma_crossed_above(slow_ma)
        exits = fast_ma.ma_crossed_below(slow_ma)
        
        # Simulate Portfolio
        portfolio = vbt.Portfolio.from_signals(price, entries, exits, init_cash=10000, fees=0.0001)
        
        # Stats
        print(f"\n--- Backtest Result: {self.symbol} {self.timeframe} (SMA {fast_window}/{slow_window}) ---")
        print(f"Total Return: {portfolio.total_return():.2%}")
        # DEBUG: Print available methods
        # print(dir(portfolio))
        
        # Safe access attempts based on common VBT versions
        try:
            print(f"Total Trades: {portfolio.trades.count()}")
        except:
            print("Could not get trades count")

        try:
             # win_rate might be a property or method, or part of trades
             wr = portfolio.trades.win_rate()
             print(f"Win Rate: {wr:.2%}")
        except:
             print("Could not get win rate")

        try:
            sr = portfolio.sharpe_ratio()
            print(f"Sharpe Ratio: {sr:.2f}")
        except:
             print("Could not get Sharpe Ratio")
             
        return portfolio
        print(f"Win Rate: {portfolio.win_rate():.2%}")
        print(f"Sharpe Ratio: {portfolio.sharpe_ratio():.2f}")
        
        return portfolio
