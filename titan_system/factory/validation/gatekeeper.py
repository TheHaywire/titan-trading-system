"""
STRATEGY GATEKEEPER - Phase 13 Validation Layer
==============================================
A multi-stage validation filter that ensures only the highest-probability
strategies move to paper/live trading.

Stage 1: Heuristic (Weighted scoring of backtest + robustness)
Stage 2: Machine Learning (Predictive success model - active when enough data)
"""

import os
import json
import logging
import sqlite3
import pandas as pd
import joblib
from typing import Dict, Tuple, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Gatekeeper")

class StrategyGatekeeper:
    def __init__(self, model_path: str = "models/gatekeeper_v1.pkl"):
        self.model_path = model_path
        self.model = None
        self.load_model()
        
        # Heuristic Weights
        self.weights = {
            'sharpe': 0.35,
            'oos_stability': 0.25,
            'mc_confidence': 0.20,
            'wfa_consistency': 0.15,
            'param_sensitivity': 0.05
        }
        
    def load_model(self):
        """Load the ML model if it exists."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info(f"✅ ML Gatekeeper model loaded: {self.model_path}")
            except Exception as e:
                logger.error(f"❌ Failed to load ML model: {e}")

    def calculate_heuristic_score(self, results: Dict) -> float:
        """
        Calculate a 0-1 confidence score based on backtest and robustness metrics.
        """
        score = 0.0
        
        # 1. Sharpe Score (Normalized to 0-1, cap at 3.0)
        sharpe = results.get('sharpe', 0)
        sharpe_score = min(sharpe / 3.0, 1.0)
        score += sharpe_score * self.weights['sharpe']
        
        # 2. OOS Stability (IS vs OOS Sharpe ratio)
        oos_sharpe = results.get('oos_sharpe', 0)
        if sharpe > 0:
            oos_ratio = oos_sharpe / sharpe
            oos_score = min(max(oos_ratio, 0), 1.0)
        else:
            oos_score = 0
        score += oos_score * self.weights['oos_stability']
        
        # 3. Monte Carlo Confidence
        mc_pass = 1.0 if results.get('monte_carlo_stable') else 0.0
        score += mc_pass * self.weights['mc_confidence']
        
        # 4. WFA Consistency
        wfa_pass = 1.0 if results.get('walkforward_consistent') else 0.0
        score += wfa_pass * self.weights['wfa_consistency']
        
        # 5. Parameter Sensitivity
        param_fail = 1.0 if results.get('parameter_sensitive') else 0.0
        param_score = 1.0 - param_fail # Low sensitivity is better
        score += param_score * self.weights['param_sensitivity']
        
        return score

    def get_ml_prediction(self, genome: Dict, results: Dict) -> Optional[float]:
        """Get success probability from ML model."""
        if not self.model:
            return None
            
        try:
            # Prepare features (simplified example - needs alignment with trainer)
            features = {
                'sharpe': results.get('sharpe', 0),
                'oos_sharpe': results.get('oos_sharpe', 0),
                'drawdown': results.get('max_drawdown', 0),
                'trades': results.get('total_trades', 0),
                'tf_minutes': self._tf_to_minutes(genome.get('timeframe', 'H1')),
                'indicator_count': len(genome.get('indicators', {})),
                'mc_stable': 1 if results.get('monte_carlo_stable') else 0,
                'wfa_pass': 1 if results.get('walkforward_consistent') else 0
            }
            
            df = pd.DataFrame([features])
            prob = self.model.predict_proba(df)[0][1] # Probability of success
            return prob
        except Exception as e:
            logger.error(f"❌ ML Prediction error: {e}")
            return None

    def validate(self, genome: Dict, results: Dict) -> Tuple[bool, Dict]:
        """
        Primary entry point for the Gatekeeper.
        Returns (passed, details).
        """
        h_score = self.calculate_heuristic_score(results)
        ml_prob = self.get_ml_prediction(genome, results)
        
        # Combined Score
        if ml_prob is not None:
            # 50/50 blend of heuristic and ML when model is available
            final_score = (h_score * 0.5) + (ml_prob * 0.5)
        else:
            final_score = h_score
            
        # Threshold (70% required for "Expert" status)
        threshold = 0.70
        passed = final_score >= threshold
        
        details = {
            "final_score": round(final_score, 2),
            "heuristic_score": round(h_score, 2),
            "ml_probability": round(ml_prob, 2) if ml_prob is not None else "N/A",
            "threshold": threshold,
            "status": "APPROVED" if passed else "REJECTED"
        }
        
        return passed, details

    def _tf_to_minutes(self, tf: str) -> int:
        mapping = {"M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240, "D1": 1440}
        return mapping.get(tf, 60)

if __name__ == "__main__":
    # Test logic
    gk = StrategyGatekeeper()
    mock_results = {
        'sharpe': 2.1,
        'oos_sharpe': 1.8,
        'monte_carlo_stable': True,
        'walkforward_consistent': True,
        'parameter_sensitive': False
    }
    mock_genome = {'timeframe': 'H1', 'indicators': {'RSI': {}, 'EMA': {}}}
    
    passed, info = gk.validate(mock_genome, mock_results)
    print(f"Gatekeeper Audit: {info}")
