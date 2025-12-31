import numpy as np
import copy
from neural_strategy import NeuralStrategy
from mt5_trading_env import MT5TradingEnv

class EvolutionaryOptimizer:
    def __init__(self, data, population_size=50, input_size=4, hidden_size=8, output_size=3):
        """
        Manages the evolution of trading strategies.
        """
        self.data = data
        self.population_size = population_size
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize Population
        self.population = [NeuralStrategy(input_size, hidden_size, output_size) for _ in range(population_size)]
        self.generation = 0
        self.best_agent = None
        self.best_fitness = -float('inf')

    def evaluate_fitness(self, agent):
        """
        Runs the agent in the environment and returns its fitness score.
        """
        env = MT5TradingEnv(self.data)
        state = env.reset()
        done = False
        
        while not done:
            action = agent.get_action(state)
            state, reward, done, _ = env.step(action)
            
        # Fitness = Profit Ratio * (1 + Win Rate?)
        # Simple Fitness: Final Balance
        try:
            return env.balance
        except:
            return 0

    def run_generation(self):
        """
        Evaluates the current population and produces the next generation.
        """
        scores = []
        print(f"Generation {self.generation} running...")
        
        # 1. Evaluate
        for i, agent in enumerate(self.population):
            fitness = self.evaluate_fitness(agent)
            scores.append((fitness, agent))
            
            # Track best
            if fitness > self.best_fitness:
                self.best_fitness = fitness
                self.best_agent = copy.deepcopy(agent)
                print(f"  New High Score: ${fitness:.2f}")

        # Sort by fitness (descending)
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # 2. Selection (Elitism)
        # Keep top 20%
        elite_count = int(self.population_size * 0.2)
        elites = [x[1] for x in scores[:elite_count]]
        
        # 3. Breeding
        next_gen = []
        
        # Direct Elitism (Carry over best unchanged)
        for e in elites:
            next_gen.append(copy.deepcopy(e))
            
        # Fill the rest with children
        while len(next_gen) < self.population_size:
            # Tournament Selection for parents
            parent1 = self._tournament_select(scores)
            parent2 = self._tournament_select(scores)
            
            # Crossover
            child = parent1.crossover(parent2)
            
            # Mutation
            child.mutate(mutation_rate=0.05, mutation_scale=0.2)
            
            next_gen.append(child)
            
        self.population = next_gen
        self.generation += 1
        
        avg_score = sum(s[0] for s in scores) / len(scores)
        print(f"Generation {self.generation} Complete. Avg Fitness: ${avg_score:.2f}, Best: ${self.best_fitness:.2f}")
        return self.best_agent

    def _tournament_select(self, scores_list, k=3):
        """
        Randomly picks k agents and returns the best one.
        """
        import random
        candidates = random.sample(scores_list, k)
        candidates.sort(key=lambda x: x[0], reverse=True)
        return candidates[0][1]

    def save_best(self, filename="best_brain.json"):
        if self.best_agent:
            self.best_agent.save(filename)
