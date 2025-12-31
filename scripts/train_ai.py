import sys
import os

# Go up one level to import core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.genetic_optimizer import GeneticOptimizer
from core.mt5_interface import MT5Interface
import MetaTrader5 as mt5
import pandas as pd
import json

def train_brain(symbol="EURUSD", timeframe=mt5.TIMEFRAME_H1):
    print(f"🧠 STARTING AI TRAINING FOR {symbol}...")
    
    # 1. Get Data
    interface = MT5Interface()
    if not interface.start():
        print("Failed to connect.")
        return

    print("Fetching History...")
    df = interface.get_closes(symbol, timeframe, num_candles=2000)
    interface.shutdown()
    
    if df is None:
        print("No data.")
        return

    # 2. Evolve
    print(f"Running Evolution ({len(df)} candles)...")
    optimizer = GeneticOptimizer(df, population_size=50, generations=10) # 10 Gens for speed
    best_gene = optimizer.run()
    
    # 3. Save with Metadata
    import datetime
    filename = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), 'data', f"brain_{symbol}.json")
    print(f"Evolution Complete. Saving to {filename}")
    
    brain_data = {
        "genes": best_gene,
        "generation": 10, # Hardcoded for this script run, or pass from optimizer
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open(filename, 'w') as f:
        json.dump(brain_data, f, indent=4)
        
    print("Done.")

if __name__ == "__main__":
    train_brain()
