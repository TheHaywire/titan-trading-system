"""
ML TRAINER - Predictive Success Modeling
========================================
Extracts historical performance data from the Strategy Registry and trains
the ML Gatekeeper model to predict which bots will succeed in live trading.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import logging
import joblib
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.factory import factory_config as cfg

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MLTrainer")

class MLTrainer:
    def __init__(self, db_path: str = "data/strategy_factory.db"):
        self.db_path = db_path
        self.model_dir = Path("models")
        self.model_dir.mkdir(exist_ok=True)
        
    def extract_training_data(self):
        """
        Extract features and labels from the Strategy Registry.
        Label 1: Strategy succeeded and is still active/promoted.
        Label 0: Strategy failed, retired, or degraded significantly.
        """
        conn = sqlite3.connect(self.db_path)
        
        # We look at historical metrics and current status to determine "success"
        query = """
        SELECT 
            id, genome, bt_sharpe, bt_oos_sharpe, bt_max_drawdown, bt_total_trades,
            monte_carlo_stable, walkforward_consistent, parameter_sensitive,
            live_pnl, live_trades, status
        FROM strategies
        WHERE bt_sharpe IS NOT NULL
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if len(df) < 5:
            logger.warning(f"Insufficient data for training: {len(df)} records found.")
            return None
            
        features = []
        labels = []
        
        for idx, row in df.iterrows():
            genome = json.loads(row['genome'])
            
            # Feature extraction from genome
            tf_map = {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
            
            f_set = {
                'bt_sharpe': row['bt_sharpe'],
                'bt_oos_sharpe': row['bt_oos_sharpe'] or 0,
                'bt_drawdown': row['bt_max_drawdown'] or 0,
                'bt_trades': row['bt_total_trades'] or 0,
                'tf_minutes': tf_map.get(genome.get('timeframe', 'H1'), 60),
                'indicator_count': len(genome.get('indicators', {})),
                'mc_stable': 1 if row['monte_carlo_stable'] else 0,
                'wfa_pass': 1 if row['walkforward_consistent'] else 0,
                'param_sensitive': 1 if row['parameter_sensitive'] else 0
            }
            
            # Success Labeling logic
            # Success = Active in paper/live with non-negative PnL and at least 1 trade
            # Failure = Retired or status marked as failure
            success = 0
            if row['status'] in ['paper', 'live']:
                if row['live_trades'] > 0 and row['live_pnl'] >= 0:
                    success = 1
                elif row['live_trades'] == 0:
                    # Too early to tell, but it passed BT and hasn't failed yet
                    success = 1 
            
            features.append(f_set)
            labels.append(success)
            
        return pd.DataFrame(features), np.array(labels)

    def train_v1(self):
        """Train a simple Random Forest or LightGBM model."""
        data = self.extract_training_data()
        if data is None: return False
        
        X, y = data
        
        # In early stages, we might have imbalanced classes (mostly successes or unknown)
        # We need at least one of each class to train
        if len(np.unique(y)) < 2:
            logger.info("Only one class detected in labels. Skipping training until failure data accumulates.")
            return False
            
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        
        logger.info(f"Training Gatekeeper v1 on {len(X)} samples...")
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
        model.fit(X_train, y_train)
        
        score = model.score(X_test, y_test)
        logger.info(f"✅ Model trained. Accuracy: {score:.2f}")
        
        save_path = self.model_dir / "gatekeeper_v1.pkl"
        joblib.dump(model, save_path)
        logger.info(f"💾 Model saved to: {save_path}")
        
        return True

if __name__ == "__main__":
    trainer = MLTrainer()
    trainer.train_v1()
