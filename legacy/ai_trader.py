from neural_strategy import NeuralStrategy
from mt5_interface import MT5Interface
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
import time
import os

class AITrader:
    def __init__(self, brain_file="best_brain_eurusd.json", symbol="EURUSD"):
        self.symbol = symbol
        self.interface = MT5Interface()
        if os.path.exists(brain_file):
            print(f"Loading AI Brain from {brain_file}...")
            self.brain = NeuralStrategy.load(brain_file)
        else:
            print(f"Brain file {brain_file} not found! Please run train_ai.py first.")
            self.brain = None
            
    def get_market_features(self):
        """
        Constructs the exact same feature vector used in training.
        """
        # We need enough data to calc indicators
        df = self.interface.get_closes(self.symbol, mt5.TIMEFRAME_H1, num_candles=100)
        
        if df is None or len(df) < 60:
            return None
            
        # Add SMA
        df['SMA_50'] = df['close'].rolling(50).mean()
        
        # Simple RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Get last row
        row = df.iloc[-1]
        
        # Safe feature extraction
        rsi = row['RSI'] if not pd.isna(row['RSI']) else 50
        sma_val = row['SMA_50'] if not pd.isna(row['SMA_50']) else row['close']
        sma_dist = (row['close'] - sma_val) / sma_val
        
        features = np.array([
            rsi / 100.0, 
            sma_dist * 10, 
            (row['close'] - row['open']) / row['open'] * 100, 
            0 
        ])
        
        return features

    def run_live(self):
        if not self.brain:
            print("No Brain! Aborting.")
            return
            
        print(f"Starting AI Trader on {self.symbol}...")
        if not self.interface.start():
            return

        try:
            while True:
                # 1. Get State
                features = self.get_market_features()
                if features is not None:
                    # 2. Get AI Decision
                    action = self.brain.get_action(features)
                    
                    # 3. Execute
                    print(f"AI sees: {features} -> Action: {action}")
                    
                    if action == 0: # BUY
                        print("AI Signal: BUY")
                        # self.interface.place_market_order(self.symbol, 0.01, mt5.ORDER_TYPE_BUY)
                        
                    elif action == 1: # SELL
                        print("AI Signal: SELL")
                        # self.interface.place_market_order(self.symbol, 0.01, mt5.ORDER_TYPE_SELL)
                        
                    else:
                        print("AI Signal: HOLD")
                        
                else:
                    print("Not enough data for features.")
                    
                time.sleep(10) # check every 10s
                
        except KeyboardInterrupt:
            print("AI Trader Stopped.")
            self.interface.shutdown()

if __name__ == "__main__":
    bot = AITrader()
    bot.run_live()
