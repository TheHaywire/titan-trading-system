"""
TITAN ML SIGNAL FILTER
======================
Machine Learning-based signal filtering using LightGBM.
Filters out weak signals and predicts trade outcome probability.

Features used:
- Technical indicators (RSI, ADX, EMA position, etc.)
- Regime information (TRENDING, MEAN_REVERTING, HIGH_VOL)
- Candlestick patterns
- Session time
- Volatility metrics

Usage:
    from titan_system.ml.signal_filter import SignalFilter
    
    filter = SignalFilter()
    
    # During training (run once on historical data)
    filter.train(historical_trades_df)
    
    # During live trading
    probability = filter.predict(signal_features)
    if probability > 0.6:  # 60% confidence threshold
        execute_trade()
"""

import numpy as np
import pandas as pd
from datetime import datetime
import logging
import pickle
import os
from typing import Dict, Optional, Tuple

# Import LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

logger = logging.getLogger("Titan.ML")


class SignalFilter:
    """
    ML-based signal filter using LightGBM.
    Predicts probability of trade success based on market features.
    """
    
    MODEL_PATH = "titan_system/ml/signal_model.pkl"
    GENERAL_MODEL_PATH = "titan_system/ml/general_model.pkl"
    
    def __init__(self, confidence_threshold: float = 0.55):
        """
        Initialize the signal filter.
        
        Args:
            confidence_threshold: Minimum probability to accept a signal (0.55 = 55%)
        """
        self.threshold = confidence_threshold
        self.model = None
        self.general_model = None
        self.feature_names = None
        self.is_trained = False
        
        if not LIGHTGBM_AVAILABLE:
            logger.warning("[ML] LightGBM not available - filter disabled")
            return
        
        # Try to load existing model
        self._load_model()
    
    def _normalize_row(self, row: Dict) -> np.ndarray:
        """Normalize a single row of features (for predict)"""
        features = []
        features.append(row.get('rsi', 50) / 100)
        features.append(row.get('adx', 20) / 50)
        features.append(row.get('ema_diff', 0))
        features.append(row.get('atr_pct', 0.01))
        features.append(row.get('range_position', 0.5))
        
        regime = row.get('regime', 'UNKNOWN')
        features.append(1 if regime == 'TRENDING' else 0)
        features.append(1 if regime == 'MEAN_REVERTING' else 0)
        features.append(1 if regime == 'HIGH_VOLATILITY' else 0)
        
        features.append(1 if row.get('direction', 'BUY') == 'BUY' else 0)
        features.append(row.get('score', 50) / 100)
        
        hour = row.get('hour', datetime.now().hour)
        features.append(np.sin(2 * np.pi * hour / 24))
        features.append(np.cos(2 * np.pi * hour / 24))
        features.append(1 if 7 <= hour <= 16 else 0)
        features.append(1 if 13 <= hour <= 22 else 0)
        features.append(row.get('candlestick_score', 0) / 5)
        
        return np.array(features).reshape(1, -1)

    def _get_feature_names(self) -> list:
        return [
            'rsi_norm', 'adx_norm', 'ema_diff', 'atr_pct', 'range_position',
            'regime_trending', 'regime_mean_rev', 'regime_high_vol',
            'direction_buy', 'score_norm', 'hour_sin', 'hour_cos',
            'session_london', 'session_ny', 'candlestick_score'
        ]

    def train(self, df: pd.DataFrame, target_col: str = 'outcome', model_type: str = 'personal'):
        """
        Train the model. Expects a dataframe with columns from _get_feature_names().
        model_type: 'personal' or 'general'
        """
        if not LIGHTGBM_AVAILABLE: return
        
        feature_names = self._get_feature_names()
        self.feature_names = feature_names
        
        # Ensure only required columns are used
        X = df[feature_names].values
        y = df[target_col].values
        
        # Train/test split (80/20)
        n_train = int(len(X) * 0.8)
        X_train, X_test = X[:n_train], X[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]
        
        # Create LightGBM dataset
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Training parameters
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'seed': 42
        }
        
        # Train model
        # Train model
        trained_model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(50)]
        )
        
        if model_type == 'general':
            self.general_model = trained_model
        else:
            self.model = trained_model
        
        self.is_trained = True
        
        # Evaluate
        model_to_test = self.general_model if model_type == 'general' else self.model
        y_pred = model_to_test.predict(X_test)
        accuracy = np.mean((y_pred > 0.5) == y_test)
        logger.info(f"[ML] Model trained - Test accuracy: {accuracy:.1%}")
        
        # Save model
        self._save_model(model_type)
        
        return accuracy
    
    def predict(self, signal_data: Dict) -> Tuple[float, bool]:
        """
        Predict probability of trade success.
        
        Args:
            signal_data: Dict with signal features
            
        Returns:
            Tuple of (probability, should_trade)
        """
        if not self.is_trained or not LIGHTGBM_AVAILABLE:
            # No model - don't filter
            return 0.5, True
        
        try:
            features = self._normalize_row(signal_data)
            
            # Personal Model Prediction
            prob_personal = self.model.predict(features)[0] if self.model else 0.5
            
            # General Model Prediction (if available)
            prob_general = self.general_model.predict(features)[0] if self.general_model else prob_personal
            
            # Weighted Ensemble (40% Personal, 60% General)
            # If no general model, use personal. If no personal, use general.
            if self.model and self.general_model:
                probability = (0.4 * prob_personal) + (0.6 * prob_general)
                logger.info(f"[ML] DUAL-BRAIN: Personal={prob_personal:.2%} | General={prob_general:.2%} -> Fused={probability:.2%}")
            elif self.general_model:
                probability = prob_general
                logger.info(f"[ML] GENERAL-ONLY: Prob={probability:.2%}")
            else:
                probability = prob_personal
                logger.info(f"[ML] PERSONAL-ONLY: Prob={probability:.2%}")
                
            should_trade = probability >= self.threshold
            
            return probability, should_trade
            
        except Exception as e:
            logger.debug(f"[ML] Prediction failed: {e}")
            return 0.5, True  # Don't filter if prediction fails
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance from trained model"""
        if not self.is_trained:
            return {}
        
        importance = self.model.feature_importance(importance_type='gain')
        return dict(zip(self.feature_names, importance))
    
    def _save_model(self, model_type: str = 'personal'):
        """Save trained model to disk"""
        target_path = self.GENERAL_MODEL_PATH if model_type == 'general' else self.MODEL_PATH
        target_model = self.general_model if model_type == 'general' else self.model
        
        if not target_model: return
        
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        with open(target_path, 'wb') as f:
            pickle.dump({
                'model': target_model,
                'feature_names': self.feature_names,
                'threshold': self.threshold
            }, f)
        
        logger.info(f"[ML] {model_type.title()} Model saved to {target_path}")
    
    def _load_model(self):
        """Load trained models from disk"""
        # Load Personal Model
        if os.path.exists(self.MODEL_PATH):
            try:
                with open(self.MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.model = data['model']
                self.feature_names = data['feature_names']
                self.threshold = data.get('threshold', 0.55)
                self.is_trained = True
                logger.info(f"[ML] Personal Model loaded from {self.MODEL_PATH}")
            except Exception as e:
                logger.warning(f"[ML] Failed to load Personal model: {e}")

        # Load General Model
        if os.path.exists(self.GENERAL_MODEL_PATH):
            try:
                with open(self.GENERAL_MODEL_PATH, 'rb') as f:
                    data = pickle.load(f)
                self.general_model = data['model']
                # Assume feature names match for now
                logger.info(f"[ML] General Model loaded from {self.GENERAL_MODEL_PATH}")
            except Exception as e:
                logger.warning(f"[ML] Failed to load General model: {e}")


class QuickSignalScorer:
    """
    Simple rule-based signal scorer (no ML required).
    Use this when model is not trained or for quick scoring.
    """
    
    def __init__(self):
        self.weights = {
            'rsi_extreme': 20,      # RSI < 30 or > 70
            'ema_cross': 15,        # Fresh EMA crossover
            'adx_strong': 10,       # ADX > 25
            'regime_aligned': 15,   # Strategy matches regime
            'candlestick': 10,      # Pattern confirmation
            'session_active': 5,    # London/NY session
        }
    
    def score(self, signal_data: Dict) -> int:
        """
        Calculate signal quality score (0-100).
        
        Returns:
            Score from 0-100
        """
        score = 50  # Base score
        
        # RSI extremes
        rsi = signal_data.get('rsi', 50)
        if rsi < 30 or rsi > 70:
            score += self.weights['rsi_extreme']
        
        # ADX trend strength
        adx = signal_data.get('adx', 20)
        if adx > 25:
            score += self.weights['adx_strong']
        
        # Regime alignment
        if signal_data.get('regime_aligned', False):
            score += self.weights['regime_aligned']
        
        # Candlestick confirmation
        cdl_score = signal_data.get('candlestick_score', 0)
        if cdl_score != 0:
            direction = signal_data.get('direction', 'BUY')
            if (cdl_score > 0 and direction == 'BUY') or (cdl_score < 0 and direction == 'SELL'):
                score += self.weights['candlestick']
        
        # Session activity
        hour = signal_data.get('hour', datetime.now().hour)
        if 7 <= hour <= 16 or 13 <= hour <= 22:
            score += self.weights['session_active']
        
        return min(100, score)


# =============================================================================
# QUICK FUNCTIONS
# =============================================================================

# Global filter instance
_signal_filter: Optional[SignalFilter] = None


def get_signal_filter() -> SignalFilter:
    """Get or create the global signal filter instance"""
    global _signal_filter
    if _signal_filter is None:
        _signal_filter = SignalFilter()
    return _signal_filter


def filter_signal(signal_data: Dict) -> Tuple[float, bool]:
    """
    Quick function to filter a signal.
    
    Returns:
        Tuple of (probability, should_trade)
    """
    return get_signal_filter().predict(signal_data)


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("TITAN ML SIGNAL FILTER - TEST")
    print("=" * 60)
    print()
    
    if not LIGHTGBM_AVAILABLE:
        print("[X] LightGBM not installed!")
    else:
        print("[OK] LightGBM available:", lgb.__version__)
    
    # Test feature creation
    test_signal = {
        'rsi': 35,
        'adx': 28,
        'ema_diff': 0.002,
        'atr_pct': 0.015,
        'range_position': 0.3,
        'regime': 'TRENDING',
        'direction': 'BUY',
        'score': 75,
        'hour': 14,
        'candlestick_score': 2
    }
    
    filter = SignalFilter()
    features = filter._create_features(test_signal)
    
    print()
    print("Test signal features:")
    print(f"  Feature vector shape: {features.shape}")
    print(f"  Feature names: {filter._get_feature_names()}")
    
    # Test prediction (model not trained yet)
    prob, should_trade = filter.predict(test_signal)
    print()
    print(f"Prediction (untrained): prob={prob:.2f}, trade={should_trade}")
    
    # Test quick scorer
    scorer = QuickSignalScorer()
    quick_score = scorer.score(test_signal)
    print(f"Quick score: {quick_score}")
    
    print()
    print("SUCCESS: ML Signal Filter module ready!")
    print()
    print("To train the model, run:")
    print("  filter.train(historical_trades_df)")
