from evolutionary_optimizer import EvolutionaryOptimizer
import pandas as pd
import numpy as np

# Mock Data Generation
def generate_mock_data():
    """Generates a random walk for testing."""
    dates = pd.date_range(start="2024-01-01", periods=1000, freq="H")
    prices = [1.0]
    for _ in range(999):
        change = np.random.normal(0, 0.001)
        prices.append(prices[-1] * (1 + change))
        
    df = pd.DataFrame({"time": dates, "close": prices})
    df['open'] = df['close'] * (1 + np.random.normal(0, 0.0005, 1000)) # slight noise
    # Mock Indicators
    df['SMA_50'] = df['close'].rolling(50).mean().fillna(df['close'])
    df['RSI'] = np.random.uniform(30, 70, 1000) # Random RSI
    return df

if __name__ == "__main__":
    print("Generating Mock Market Data...")
    data = generate_mock_data()
    
    print("Initializing Evolutionary Optimizer...")
    # Small population for fast test
    optimizer = EvolutionaryOptimizer(data, population_size=10, input_size=4, hidden_size=8, output_size=3)
    
    print("Starting Evolution (3 Generations)...")
    best_brain = None
    for i in range(3):
        best_brain = optimizer.run_generation()
        
    print("Evolution Setup Verified.")
    best_brain.save("neural_brain_v0.json")
    print("Brain saved to neural_brain_v0.json")
