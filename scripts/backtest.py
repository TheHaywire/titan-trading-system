import pandas as pd
import numpy as np
import ta
import json
from mt5_interface import MT5Interface
import MetaTrader5 as mt5

class BacktestEngine:
    def __init__(self, data, initial_balance=10000):
        self.data = data.copy()
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.equity = initial_balance
        self.positions = [] # List of dicts
        self.trades = [] # List of closed trades
        self.equity_curve = []
        
    def run_strategy(self, short_window, long_window):
        # Calculate Indicators
        self.data['sma_short'] = ta.trend.sma_indicator(self.data['close'], window=short_window)
        self.data['sma_long'] = ta.trend.sma_indicator(self.data['close'], window=long_window)
        
        position = 0 # 0: None, 1: Long, -1: Short
        entry_price = 0
        
        for index, row in self.data.iterrows():
            # Signals (Shifted logic handled by using previous row in real-time, 
            # here we iterate row by row, so signal at 'row' executes at 'row' close or next open)
            # Simplification: Execute at Close of signal candle
            
            sma_short = row['sma_short']
            sma_long = row['sma_long']
            price = row['close']
            date = row['time']
            
            if pd.isna(sma_short) or pd.isna(sma_long):
                 self.equity_curve.append({'time': date, 'equity': self.balance})
                 continue
            
            # Buy Signal
            if sma_short > sma_long and position != 1:
                if position == -1:
                    # Close Short
                    pnl = (entry_price - price) * 100000 * 0.01 # Standard Lot logic simplification
                    self.balance += pnl
                    self.trades.append({'type': 'SELL_CLOSE', 'price': price, 'pnl': pnl, 'time': date})
                    position = 0
                
                # Open Long
                position = 1
                entry_price = price
                self.trades.append({'type': 'BUY_OPEN', 'price': price, 'time': date})

            # Sell Signal
            elif sma_short < sma_long and position != -1:
                if position == 1:
                    # Close Long
                    pnl = (price - entry_price) * 100000 * 0.01
                    self.balance += pnl
                    self.trades.append({'type': 'BUY_CLOSE', 'price': price, 'pnl': pnl, 'time': date})
                    position = 0
                
                # Open Short
                position = -1
                entry_price = price
                self.trades.append({'type': 'SELL_OPEN', 'price': price, 'time': date})
            
            # Calculate Floating Equity
            floating_pnl = 0
            if position == 1:
                floating_pnl = (price - entry_price) * 100000 * 0.01
            elif position == -1:
                floating_pnl = (entry_price - price) * 100000 * 0.01
            
            self.equity_curve.append({'time': date, 'equity': self.balance + floating_pnl})

    def get_performance_report(self):
        df_equity = pd.DataFrame(self.equity_curve)
        if df_equity.empty:
            return "No trades generated."
            
        df_equity['returns'] = df_equity['equity'].pct_change()
        
        total_return = (self.balance - self.initial_balance) / self.initial_balance * 100
        
        # Max Drawdown
        df_equity['peak'] = df_equity['equity'].cummax()
        df_equity['drawdown'] = (df_equity['equity'] - df_equity['peak']) / df_equity['peak']
        max_drawdown = df_equity['drawdown'].min() * 100
        
        # Sharpe Ratio (assuming hourly data, annualized)
        sharpe_ratio = 0
        std_dev = df_equity['returns'].std()
        if std_dev != 0:
            sharpe_ratio = df_equity['returns'].mean() / std_dev * np.sqrt(252 * 24)
            
        return {
            "Total Trades": len(self.trades),
            "Final Balance": self.balance,
            "Total Return (%)": total_return,
            "Max Drawdown (%)": max_drawdown,
            "Sharpe Ratio": sharpe_ratio
        }

if __name__ == "__main__":
    print("Running Backtest...")
    
    # 1. Fetch Data
    mt5_interface = MT5Interface()
    if mt5_interface.start():
        df = mt5_interface.get_closes("EURUSD", mt5.TIMEFRAME_H1, num_candles=5000)
        mt5_interface.shutdown()
        
        if df is not None:
            engine = BacktestEngine(df)
            engine.run_strategy(short_window=30, long_window=100)
            metrics = engine.get_performance_report()
            print(json.dumps(metrics, indent=4))
        else:
            print("No data.")
    else:
        print("MT5 Not connected.")
