"""
ML MODEL TRAINER
================
Trains the LightGBM Signal Filter using generated historical data.
Saves the model for the Autonomous Bot to use.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import logging
from titan_system.ml.signal_filter import SignalFilter

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Trainer")

def train_from_csv(file_path: str):
    """
    Loads data from CSV and trains the SignalFilter model.
    """
    logger.info(f"Loading training data from {file_path}...")
    
    if not os.path.exists(file_path):
        logger.error(f"File {file_path} not found")
        return False
        
    df = pd.read_csv(file_path)
    if df.empty:
        logger.error("Empty dataset")
        return False
        
    logger.info(f"Loaded {len(df)} samples with {len(df.columns)-1} features.")
    
    # Prepare features and target
    X = df.drop(columns=['outcome'])
    y = df['outcome']
    
    # Initialize SignalFilter
    sf = SignalFilter(confidence_threshold=0.55)
    
    # Train
    logger.info("Training LightGBM model...")
    success = sf.train(X, y)
    
    if success:
        logger.info("Model trained and saved successfully.")
        # Test on a few samples
        sample = X.iloc[0].to_dict()
        prob, trade = sf.predict(sample)
        logger.info(f"Verification Test - Predict Sample: Prob={prob:.4f}, Should Trade={trade}")
        return True
    else:
        logger.error("Model training failed.")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/training_gold.csv")
    args = parser.parse_args()
    
    train_from_csv(args.csv)
