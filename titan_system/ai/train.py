import os
import sys
import numpy as np
import polars as pl
import json
import logging
from datetime import datetime

# Path Hack
sys.path.append(os.path.join(os.getcwd()))

from titan_system.data.loader import DataLoader
from titan_system.core.neural_strategy import NeuralStrategy
from titan_system.ai.features import compute_features
import MetaTrader5 as mt5

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("Titan.AI")

class GeneticTrainer:
    def __init__(self, symbol="XAUUSD", population_size=50, generations=20):
        self.symbol = symbol
        self.pop_size = population_size
        self.generations = generations
        self.population = []
        self.best_model = None
        self.best_score = -9999
        
        # Load Data
        self.loader = DataLoader(data_dir="titan_system/data/history")
        self.df = None
        self.feature_matrix = None
        self.price_returns = None
        
    def prepare_data(self):
        filename = f"{self.symbol}_M1.csv"
        path = os.path.join(self.loader.data_dir, filename)
        
        # Fallback fetch
        if not os.path.exists(path):
            logger.info("Fetching training data...")
            df = self.loader.fetch_history(self.symbol, mt5.TIMEFRAME_M1, 50000)
            if df is not None:
                self.loader.save_data(df, filename)
            else:
                raise Exception("Could not fetch data")
        
        # Load
        df = pl.read_csv(path).sort("time")
        
        # Compute Features
        logger.info("🧠 Engineering Features...")
        self.df_clean, self.feature_matrix = compute_features(df)
        
        # Pre-compute Market Returns for fast backtesting
        # Log Return of Close
        self.price_returns = (self.df_clean['close'] / self.df_clean['close'].shift(1)).log().fill_null(0).to_numpy()
        
        logger.info(f"Training Set: {len(self.feature_matrix)} samples x {self.feature_matrix.shape[1]} features")

    def init_population(self):
        input_size = self.feature_matrix.shape[1]
        hidden_size = 8
        output_size = 3 # Buy, Sell, Hold
        
        self.population = [NeuralStrategy(input_size, hidden_size, output_size) for _ in range(self.pop_size)]
        
    def evaluate(self, agent):
        """
        Runs a vectorized backtest for a single agent.
        Fast Matrix Multiplication approach.
        """
        # 1. Inference: Get Probabilities for ALL rows at once
        # NeuralStrategy.forward is usually for single sample. We need to vectorize it.
        # Simple Re-implementation of Forward for Batch
        
        # Layer 1
        z1 = np.dot(self.feature_matrix, agent.W1) + agent.b1
        a1 = np.maximum(0, z1) # ReLU
        
        # Layer 2
        z2 = np.dot(a1, agent.W2) + agent.b2
        
        # Softmax (axis=1)
        exp_scores = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
        probs = exp_scores / np.sum(exp_scores, axis=1, keepdims=True)
        
        # Actions: Argmax
        actions = np.argmax(probs, axis=1) # 0=Buy, 1=Sell, 2=Hold
        
        # Map Actions to Signal (1, -1, 0)
        # 0->1, 1->-1, 2->0
        signals = np.zeros_like(actions, dtype=float)
        signals[actions == 0] = 1.0  # Buy
        signals[actions == 1] = -1.0 # Sell
        
        # Shift Signals by 1 (Trade Next Bar)
        signals_shifted = np.roll(signals, 1)
        signals_shifted[0] = 0
        
        # Calculate Returns
        strategy_returns = self.price_returns * signals_shifted
        
        # Score: Total Log Return (Approx P&L)
        # Penalty for inactivity?
        total_return = np.sum(strategy_returns)
        
        # Validations: Trade Count
        trade_count = np.count_nonzero(signals)
        if trade_count < 10: # Minimum trades punishment
            total_return = -1.0
            
        return total_return

    def run(self):
        self.prepare_data()
        self.init_population()
        
        print("\n🧬 Starting Evolution...")
        
        for gen in range(self.generations):
            scores = []
            
            # Evaluate
            for i, agent in enumerate(self.population):
                score = self.evaluate(agent)
                scores.append((score, agent))
            
            # Sort (Higher is better)
            scores.sort(key=lambda x: x[0], reverse=True)
            
            # Stats
            best_gen_score = scores[0][0]
            avg_score = sum(s[0] for s in scores) / len(scores)
            
            print(f"Gen {gen+1:02d} | Best: {best_gen_score*100:.2f}% | Avg: {avg_score*100:.2f}%")
            
            if best_gen_score > self.best_score:
                self.best_score = best_gen_score
                self.best_model = scores[0][1]
            
            # Selection (Survival of top 20%)
            cutoff = int(self.pop_size * 0.2)
            parents = [s[1] for s in scores[:cutoff]]
            
            # Reproduction
            new_pop = list(parents) # Elitism
            
            while len(new_pop) < self.pop_size:
                # Randomly select 2 parents
                p1 = np.random.choice(parents)
                p2 = np.random.choice(parents)
                
                # Crossover
                child = p1.crossover(p2)
                
                # Mutation
                child.mutate(mutation_rate=0.05)
                new_pop.append(child)
                
            self.population = new_pop
            
        print("\n🏆 Training Complete!")
        print(f"Best Return: {self.best_score*100:.2f}%")
        
        # Save Best Model
        save_dir = "titan_system/ai/models"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        save_path = os.path.join(save_dir, "best_brain.json")
        self.best_model.save(save_path)
        print(f"💾 Brain saved to {save_path}")

if __name__ == "__main__":
    trainer = GeneticTrainer(symbol="XAUUSD", population_size=100, generations=10)
    trainer.run()
