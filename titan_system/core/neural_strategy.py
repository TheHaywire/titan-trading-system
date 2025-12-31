import numpy as np
import json

class NeuralStrategy:
    def __init__(self, input_size, hidden_size, output_size):
        """
        A simple Feed-Forward Neural Network.
        Input Layer -> Hidden Layer (ReLU) -> Output Layer (Softmax/Linear)
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize weights randomly (The "DNA")
        # Scale by sqrt(2/n) for He Initialization equivalent
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2/input_size)
        self.b1 = np.zeros(hidden_size)
        self.W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2/hidden_size)
        self.b2 = np.zeros(output_size)
        
    def forward(self, x):
        """
        Forward pass to get action probabilities.
        x: Input vector (Market Features)
        """
        # Ensure input is numpy array
        x = np.array(x)
        
        # Layer 1
        self.z1 = np.dot(x, self.W1) + self.b1
        self.a1 = np.maximum(0, self.z1) # ReLU Activation
        
        # Layer 2 (Output)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        
        # Softmax for action probabilities (Buy, Sell, Hold)
        exp_scores = np.exp(self.z2 - np.max(self.z2)) # subtract max for stability
        probs = exp_scores / np.sum(exp_scores)
        
        return probs

    def get_action(self, state):
        """
        Returns the action with highest probability.
        0: BUY, 1: SELL, 2: HOLD
        """
        probs = self.forward(state)
        return np.argmax(probs)

    def mutate(self, mutation_rate=0.01, mutation_scale=0.1):
        """
        Evolve: Randomly adjust weights.
        """
        # Helper to mutate a parameter array
        def mutate_param(param):
            mask = np.random.rand(*param.shape) < mutation_rate
            noise = np.random.randn(*param.shape) * mutation_scale
            param[mask] += noise[mask]
            
        mutate_param(self.W1)
        mutate_param(self.b1)
        mutate_param(self.W2)
        mutate_param(self.b2)

    def crossover(self, partner):
        """
        Reproduction: Create a child by mixing weights with a partner.
        Returns: A new NeuralStrategy instance.
        """
        child = NeuralStrategy(self.input_size, self.hidden_size, self.output_size)
        
        # Randomly inherit W1 from self or partner
        if np.random.rand() > 0.5:
            child.W1 = self.W1.copy()
            child.b1 = self.b1.copy()
        else:
            child.W1 = partner.W1.copy()
            child.b1 = partner.b1.copy()
            
        # Randomly inherit W2
        if np.random.rand() > 0.5:
            child.W2 = self.W2.copy()
            child.b2 = self.b2.copy()
        else:
            child.W2 = partner.W2.copy()
            child.b2 = partner.b2.copy()
            
        return child

    def save(self, filename):
        data = {
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist()
        }
        with open(filename, 'w') as f:
            json.dump(data, f)
            
    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        obj = cls(data["input_size"], data["hidden_size"], data["output_size"])
        obj.W1 = np.array(data["W1"])
        obj.b1 = np.array(data["b1"])
        obj.W2 = np.array(data["W2"])
        obj.b2 = np.array(data["b2"])
        return obj
