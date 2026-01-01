import numpy as np
import pandas as pd

class MT5TradingEnv:
    def __init__(self, data, initial_balance=10000):
        """
        A simulation environment for the AI to learn in.
        data: DataFrame with OHLCV and indicators.
        """
        self.data = data.reset_index(drop=True)
        self.initial_balance = initial_balance
        self.reset()
        
    def reset(self):
        """Resets the environment to the beginning."""
        self.current_step = 0
        self.balance = self.initial_balance
        self.position = 0 # 0: None, 1: Buy, -1: Sell
        self.entry_price = 0
        self.equity = self.initial_balance
        self.done = False
        self.history = []
        
        return self._get_state()
        
    def _get_state(self):
        """
        Returns the current market state (Input for Neural Network).
        Features: 
        - Normalized Price Changes
        - RSI (if available) / Moving Averages
        """
        # For simplicity, let's use last 5 close prices normalized by the first of the 5
        # In a real scenario, we'd use pre-calculated technical indicators
        
        if self.current_step < 5:
            # Pad with zeros if at start
            return np.zeros(4) # Match feature size
        
        # Example Features:
        # 1. RSI (Assuming column 'RSI' exists or we calc it)
        # 2. Distance from SMA
        # 3. Recent volatility
        
        row = self.data.iloc[self.current_step]
        
        # Safe feature extraction
        rsi = row['RSI'] if 'RSI' in row else 50
        sma_dist = (row['close'] - row['SMA_50']) / row['SMA_50'] if 'SMA_50' in row else 0
        
        features = np.array([
            rsi / 100.0, # Normalize RSI 0-1
            sma_dist * 10, # Scale generic pct diff
            (row['close'] - row['open']) / row['open'] * 100, # Candle body %
            0 # Placeholder
        ])
        
        # Pad features to match input_size of NN (let's say 4 for now)
        return features

    def step(self, action):
        """
        Executes an action.
        Action 0: BUY
        Action 1: SELL
        Action 2: HOLD / CLOSE (Simplify: 0=Buy, 1=Sell, 2=Close/Hold)
        
        Let's Define Actions:
        0: Go Long (Close Short if any)
        1: Go Short (Close Long if any)
        2: Flat (Close all)
        """
        
        current_price = self.data.iloc[self.current_step]['close']
        reward = 0
        
        # Execute Action
        if action == 0: # BUY
            if self.position == -1: # Close Short
                profit = (self.entry_price - current_price) * 1000 # 1000 units arbitrary size
                self.balance += profit
                self.position = 0
                
            if self.position == 0: # Open Long
                self.position = 1
                self.entry_price = current_price
                
        elif action == 1: # SELL
            if self.position == 1: # Close Long
                profit = (current_price - self.entry_price) * 1000
                self.balance += profit
                self.position = 0
                
            if self.position == 0: # Open Short
                self.position = -1
                self.entry_price = current_price
                
        elif action == 2: # CLOSE / FLAT
            if self.position == 1:
                profit = (current_price - self.entry_price) * 1000
                self.balance += profit
            elif self.position == -1:
                profit = (self.entry_price - current_price) * 1000
                self.balance += profit
            self.position = 0
            
        # Calculate Equity (Unrealized PnL)
        unrealized_pnl = 0
        if self.position == 1:
            unrealized_pnl = (current_price - self.entry_price) * 1000
        elif self.position == -1:
            unrealized_pnl = (self.entry_price - current_price) * 1000
            
        self.equity = self.balance + unrealized_pnl
        
        # Reward Function: Change in Equity
        # We want to maximize Equity growth
        # Normalized reward helps training stability
        reward = (self.equity - self.initial_balance) / self.initial_balance
        
        # Next Step
        self.current_step += 1
        if self.current_step >= len(self.data) - 1:
            self.done = True
            
        return self._get_state(), reward, self.done, {}

