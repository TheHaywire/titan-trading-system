import random
import pandas as pd
import numpy as np
import ta
import json
import copy

class GeneticOptimizer:
    """
    Evolves trading strategies using a Genetic Algorithm.
    Maximizes Profit Factor and Net Profit.
    """
    
    def __init__(self, df, population_size=50, generations=10):
        self.df = df
        self.population_size = population_size
        self.generations = generations
        self.population = []
        self.best_gene = None
        
        # Gene Limits (Search Space)
        self.gene_space = {
            'sma_fast': (10, 100),
            'sma_slow': (50, 300),
            'rsi_period': (5, 25),
            'rsi_overbought': (60, 90),
            'rsi_oversold': (10, 40)
        }

    def _create_gene(self):
        """Create a random gene."""
        gene = {}
        for key, (min_val, max_val) in self.gene_space.items():
            gene[key] = random.randint(min_val, max_val)
        
        # Constraint: Fast < Slow
        if gene['sma_fast'] >= gene['sma_slow']:
            gene['sma_fast'] = int(gene['sma_slow'] * 0.5)
            
        return gene

    def initialize_population(self):
        """Create initial random population."""
        self.population = [self._create_gene() for _ in range(self.population_size)]

    def fitness_function(self, gene):
        """
        Run backtest for a gene and return fitness score.
        Fitness = Profit Factor * log(Net Profit)
        """
        try:
            # Need a fast vectorized backtest here
            # Copy data
            data = self.df.copy()
            
            # Indicators
            data['fast'] = ta.trend.sma_indicator(data['close'], window=gene['sma_fast'])
            data['slow'] = ta.trend.sma_indicator(data['close'], window=gene['sma_slow'])
            
            # Shift signal generation to match 'close' availability
            # Signal at T is calculated using Close at T. 
            # Trade entry is at T+1 Open (or approximated by T Close if we accept slip).
            # For vector backtest, we use trend following.
            
            data['signal'] = 0
            # Long condition
            data.loc[data['fast'] > data['slow'], 'signal'] = 1
            # Short condition
            data.loc[data['fast'] < data['slow'], 'signal'] = -1
            
            # Apply RSI Filters? (Would slow it down, but let's try strict crossover for now for speed)
            # Or add RSI column
            # data['rsi'] = ta.momentum.rsi(data['close'], window=gene['rsi_period'])
            # data.loc[data['rsi'] > gene['rsi_overbought'], 'signal'] = 0 ... complex in vector
            
            # Cost Simulation (The "Reality Check")
            # User Feedback: "Don't assume, use data."
            # We assume a base cost of 1.5 pips (0.00015) per trade to account for spread + comms.
            SPREAD_COST = 0.00015 
            
            data['market_return'] = data['close'].pct_change()
            
            # Identify Trade Execution (Signal Change)
            # Signal: 0 -> 1 (Buy), 1 -> -1 (Flip), etc.
            data['trade_executed'] = data['signal'].diff().abs().fillna(0)
            
            # If signal changes, we pay the spread
            data['transaction_costs'] = data['trade_executed'] * SPREAD_COST
            
            # Strategy Return = (Signal * Market) - Costs
            data['strategy_return'] = (data['signal'].shift(1) * data['market_return']) - data['transaction_costs']
            
            # Metrics
            total_return = data['strategy_return'].sum()
            winning_days = data[data['strategy_return'] > 0]['strategy_return'].sum()
            losing_days = abs(data[data['strategy_return'] < 0]['strategy_return'].sum())
            
            if losing_days == 0:
                profit_factor = 10 # Capped max
            else:
                profit_factor = winning_days / losing_days
                
            # Score
            # We want high profit factor AND positive return
            if total_return <= 0:
                return 0.1 # Penalize storage
                
            score = profit_factor * (1 + total_return)
            return max(0.1, score)
            
        except Exception:
            return 0.1

    def select(self, sorted_pop):
        """Select top 20% + randoms."""
        cutoff = int(self.population_size * 0.2)
        survivors = [g for g, s in sorted_pop[:cutoff]]
        
        # Add a few lucky losers to maintain diversity
        for _ in range(int(self.population_size * 0.05)):
            survivors.append(random.choice(sorted_pop[cutoff:])[0])
            
        return survivors

    def crossover(self, parent1, parent2):
        """Mix genes of two parents."""
        child = {}
        for key in self.gene_space:
            if random.random() > 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        
        # Validation
        if child['sma_fast'] >= child['sma_slow']:
            child['sma_fast'] = int(child['sma_slow'] * 0.5)
            
        return child

    def mutate(self, gene):
        """Randomly change one parameter."""
        if random.random() < 0.2: # 20% mutation rate
            key = random.choice(list(self.gene_space.keys()))
            min_val, max_val = self.gene_space[key]
            gene[key] = random.randint(min_val, max_val)
            
            if gene['sma_fast'] >= gene['sma_slow']:
                gene['sma_fast'] = int(gene['sma_slow'] * 0.5)
        return gene

    def run(self):
        """Run the optimization loop."""
        self.initialize_population()
        
        for generation in range(self.generations):
            # 1. Evaluate
            scored_pop = []
            for gene in self.population:
                score = self.fitness_function(gene)
                scored_pop.append((gene, score))
            
            # Sort by score desc
            scored_pop.sort(key=lambda x: x[1], reverse=True)
            
            best_gene, best_score = scored_pop[0]
            avg_score = sum(s for g, s in scored_pop) / len(scored_pop)
            
            print(f"Gen {generation+1}: Best Score={best_score:.4f}, Avg={avg_score:.4f} | Params: {best_gene}")
            
            self.best_gene = best_gene
            
            # 2. Select
            survivors = self.select(scored_pop)
            
            # 3. Next Gen (Crossover + Mutation)
            new_pop = []
            while len(new_pop) < self.population_size:
                p1 = random.choice(survivors)
                p2 = random.choice(survivors)
                child = self.crossover(p1, p2)
                child = self.mutate(child)
                new_pop.append(child)
                
            self.population = new_pop
            
        return self.best_gene
