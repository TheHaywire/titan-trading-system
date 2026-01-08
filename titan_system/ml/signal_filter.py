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
    
    def __init__(self, confidence_threshold: float = 0.55):
        """
        Initialize the signal filter.
        
        Args:
            confidence_threshold: Minimum probability to accept a signal (0.55 = 55%)
        """
        self.threshold = confidence_threshold
        self.model = None
        self.feature_names = None
        self.is_trained = False
        
        if not LIGHTGBM_AVAILABLE:
            logger.warning("[ML] LightGBM not available - filter disabled")
            return
        
        # Try to load existing model
        self._load_model()
    
    def _create_features(self, signal_data: Dict) -> np.ndarray:
        """
        Create feature vector from signal data.
        
        Expected signal_data keys:
        - rsi: RSI value (0-100)
        - adx: ADX value
        - ema_diff: EMA9 - EMA21 (normalized)
        - atr_pct: ATR as % of price
        - regime: 'TRENDING', 'MEAN_REVERTING', 'HIGH_VOLATILITY'
        - direction: 'BUY' or 'SELL'
        - score: Signal score (50-100)
        - hour: Hour of day (0-23)
        - candlestick_score: Net candlestick pattern score
        - range_position: Position in 20-bar range (0-1)
        """
        features = []
        
        # Momentum features
        features.append(signal_data.get('rsi', 50) / 100)  # Normalized 0-1
        features.append(signal_data.get('adx', 20) / 50)   # Normalized
        features.append(signal_data.get('ema_diff', 0))    # Already normalized
        
        # Volatility features
        features.append(signal_data.get('atr_pct', 0.01))  # ATR as % of price
        features.append(signal_data.get('range_position', 0.5))
        
        # Regime encoding (one-hot)
        regime = signal_data.get('regime', 'UNKNOWN')
        features.append(1 if regime == 'TRENDING' else 0)
        features.append(1 if regime == 'MEAN_REVERTING' else 0)
        features.append(1 if regime == 'HIGH_VOLATILITY' else 0)
        
        # Direction encoding
        direction = signal_data.get('direction', 'BUY')
        features.append(1 if direction == 'BUY' else 0)
        
        # Score (normalized)
        features.append(signal_data.get('score', 50) / 100)
        
        # Time features
        hour = signal_data.get('hour', datetime.now().hour)
        # Encode as sin/cos for cyclical nature
        features.append(np.sin(2 * np.pi * hour / 24))
        features.append(np.cos(2 * np.pi * hour / 24))
        
        # Session encoding (London, NY, Asian)
        features.append(1 if 7 <= hour <= 16 else 0)  # London
        features.append(1 if 13 <= hour <= 22 else 0)  # NY
        
        # Candlestick features
        features.append(signal_data.get('candlestick_score', 0) / 5)  # Normalized
        
        return np.array(features).reshape(1, -1)
    
    def _get_feature_names(self) -> list:
        """Get list of feature names for interpretability"""
        return [
            'rsi_norm', 'adx_norm', 'ema_diff',
            'atr_pct', 'range_position',
            'regime_trending', 'regime_mean_rev', 'regime_high_vol',
            'direction_buy',
            'score_norm',
            'hour_sin', 'hour_cos',
            'session_london', 'session_ny',
            'candlestick_score'
        ]
    
    def train(self, trades_df: pd.DataFrame, target_col: str = 'profitable'):
        """
        Train the signal filter on historical trades.
        
        Args:
            trades_df: DataFrame with trade features and outcome
            target_col: Column name for binary target (1=profitable, 0=loss)
        """
        if not LIGHTGBM_AVAILABLE:
            logger.warning("[ML] Cannot train - LightGBM not available")
            return
        
        logger.info("[ML] Training signal filter...")
        
        # Create feature matrix
        feature_cols = self._get_feature_names()
        self.feature_names = feature_cols
        
        # Prepare data
        X = trades_df[feature_cols].values
        y = trades_df[target_col].values
        
        # Train/test split (80/20)
        n_train = int(len(X) * 0.8)
        X_train, X_test = X[:n_train], X[n_train:]
        y_train, y_test = y[:n_train], y[n_train:]
        
        # Create LightGBM dataset
        train_data = lgb.Dataset(X_train, label=y_train, feature_name=feature_cols)
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
        self.model = lgb.train(
            params,
            train_data,
            num_boost_round=200,
            valid_sets=[test_data],
            callbacks=[lgb.early_stopping(50)]
        )
        
        self.is_trained = True
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = np.mean((y_pred > 0.5) == y_test)
        logger.info(f"[ML] Model trained - Test accuracy: {accuracy:.1%}")
        
        # Save model
        self._save_model()
        
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
            features = self._create_features(signal_data)
            probability = self.model.predict(features)[0]
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
    
    def _save_model(self):
        """Save trained model to disk"""
        if not self.is_trained:
            return
        
        os.makedirs(os.path.dirname(self.MODEL_PATH), exist_ok=True)
        
        with open(self.MODEL_PATH, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_names': self.feature_names,
                'threshold': self.threshold
            }, f)
        
        logger.info(f"[ML] Model saved to {self.MODEL_PATH}")
    
    def _load_model(self):
        """Load trained model from disk"""
        if not os.path.exists(self.MODEL_PATH):
            return
        
        try:
            with open(self.MODEL_PATH, 'rb') as f:
                data = pickle.load(f)
            
            self.model = data['model']
            self.feature_names = data['feature_names']
            self.threshold = data.get('threshold', 0.55)
            self.is_trained = True
            
            logger.info(f"[ML] Model loaded from {self.MODEL_PATH}")
            
        except Exception as e:
            logger.warning(f"[ML] Failed to load model: {e}")


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
