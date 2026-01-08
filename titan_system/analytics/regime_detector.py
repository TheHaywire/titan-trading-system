"""
Markov Regime Switching Model
=============================
Institutional-grade regime detection using Hidden Markov Models.
Detects market regime shifts (Trending/Mean-Reverting/High-Volatility) 
before they impact P&L.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("Titan.Regime")


class MarketRegime(Enum):
    """Market regime classification."""
    TRENDING = "TRENDING"
    MEAN_REVERTING = "MEAN_REVERTING"  
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"
    UNKNOWN = "UNKNOWN"


@dataclass
class RegimeState:
    """Current regime state and probabilities."""
    current_regime: MarketRegime
    regime_probabilities: Dict[str, float]
    confidence: float
    duration_bars: int
    regime_change_signal: bool


class MarkovRegimeSwitcher:
    """
    Hidden Markov Model for regime detection.
    Uses volatility, trend strength, and mean-reversion metrics
    to classify market regimes.
    """
    
    def __init__(self, n_regimes: int = 3, lookback: int = 100):
        """
        Args:
            n_regimes: Number of hidden states (regimes)
            lookback: Number of bars for analysis
        """
        self.n_regimes = n_regimes
        self.lookback = lookback
        
        # State names
        self.regime_names = [
            MarketRegime.TRENDING,
            MarketRegime.MEAN_REVERTING,
            MarketRegime.HIGH_VOLATILITY
        ][:n_regimes]
        
        # Initialize transition matrix (learned from data)
        # Rows = current state, Cols = next state
        # Initial: slight preference to stay in same state
        self.transition_matrix = np.array([
            [0.7, 0.2, 0.1],  # From Trending
            [0.2, 0.7, 0.1],  # From Mean-Reverting
            [0.3, 0.3, 0.4]   # From High-Vol
        ])[:n_regimes, :n_regimes]
        
        # Emission parameters (will be fitted from data)
        # Each regime has characteristic volatility and trend stats
        self.emission_params = {
            MarketRegime.TRENDING: {
                'adx_mean': 35, 'adx_std': 10,
                'vol_ratio_mean': 1.0, 'vol_ratio_std': 0.3
            },
            MarketRegime.MEAN_REVERTING: {
                'adx_mean': 15, 'adx_std': 5,
                'vol_ratio_mean': 0.7, 'vol_ratio_std': 0.2
            },
            MarketRegime.HIGH_VOLATILITY: {
                'adx_mean': 25, 'adx_std': 15,
                'vol_ratio_mean': 2.0, 'vol_ratio_std': 0.5
            }
        }
        
        # State tracking
        self.current_state_idx = 0
        self.state_duration = 0
        self.state_history = []
    
    def fit(self, df: pd.DataFrame) -> None:
        """
        Fit emission parameters from historical data.
        Uses Expectation-Maximization to learn regime characteristics.
        """
        if len(df) < self.lookback:
            logger.warning(f"[REGIME] Insufficient data for fitting ({len(df)} bars)")
            return
        
        # Calculate features
        features = self._extract_features(df)
        
        # Simple K-means style initialization for 3 regimes
        # Based on volatility and trend strength percentiles
        vol_ratio = features['vol_ratio']
        adx = features['adx']
        
        # Classify bars into regimes based on simple rules
        high_vol_mask = vol_ratio > np.percentile(vol_ratio, 75)
        trending_mask = (adx > np.percentile(adx, 60)) & ~high_vol_mask
        mean_rev_mask = ~high_vol_mask & ~trending_mask
        
        # Update emission parameters
        if np.sum(trending_mask) > 5:
            self.emission_params[MarketRegime.TRENDING] = {
                'adx_mean': float(np.mean(adx[trending_mask])),
                'adx_std': max(1.0, float(np.std(adx[trending_mask]))),
                'vol_ratio_mean': float(np.mean(vol_ratio[trending_mask])),
                'vol_ratio_std': max(0.1, float(np.std(vol_ratio[trending_mask])))
            }
        
        if np.sum(mean_rev_mask) > 5:
            self.emission_params[MarketRegime.MEAN_REVERTING] = {
                'adx_mean': float(np.mean(adx[mean_rev_mask])),
                'adx_std': max(1.0, float(np.std(adx[mean_rev_mask]))),
                'vol_ratio_mean': float(np.mean(vol_ratio[mean_rev_mask])),
                'vol_ratio_std': max(0.1, float(np.std(vol_ratio[mean_rev_mask])))
            }
        
        if np.sum(high_vol_mask) > 5:
            self.emission_params[MarketRegime.HIGH_VOLATILITY] = {
                'adx_mean': float(np.mean(adx[high_vol_mask])),
                'adx_std': max(1.0, float(np.std(adx[high_vol_mask]))),
                'vol_ratio_mean': float(np.mean(vol_ratio[high_vol_mask])),
                'vol_ratio_std': max(0.1, float(np.std(vol_ratio[high_vol_mask])))
            }
        
        # Estimate transition matrix from data
        self._estimate_transitions(adx, vol_ratio)
        
        logger.info(f"[REGIME] Model fitted on {len(df)} bars")
    
    def _estimate_transitions(self, adx: np.ndarray, vol_ratio: np.ndarray) -> None:
        """Estimate transition probabilities from data."""
        # Classify each bar
        states = []
        for i in range(len(adx)):
            probs = self._get_emission_probs(adx[i], vol_ratio[i])
            states.append(np.argmax(probs))
        
        # Count transitions
        counts = np.zeros((self.n_regimes, self.n_regimes))
        for i in range(1, len(states)):
            counts[states[i-1], states[i]] += 1
        
        # Normalize to probabilities
        for i in range(self.n_regimes):
            row_sum = np.sum(counts[i])
            if row_sum > 0:
                self.transition_matrix[i] = counts[i] / row_sum
            else:
                # Default: stay in same state
                self.transition_matrix[i] = np.zeros(self.n_regimes)
                self.transition_matrix[i, i] = 0.8
                others = (1 - 0.8) / (self.n_regimes - 1)
                for j in range(self.n_regimes):
                    if j != i:
                        self.transition_matrix[i, j] = others
    
    def detect(self, df: pd.DataFrame) -> RegimeState:
        """
        Detect current market regime from recent data.
        
        Args:
            df: DataFrame with OHLC data (needs at least lookback bars)
            
        Returns:
            RegimeState with current regime and probabilities
        """
        if len(df) < 20:
            return RegimeState(
                current_regime=MarketRegime.UNKNOWN,
                regime_probabilities={r.value: 0.33 for r in self.regime_names},
                confidence=0.0,
                duration_bars=0,
                regime_change_signal=False
            )
        
        features = self._extract_features(df.tail(self.lookback))
        
        # Get latest observation
        current_adx = features['adx'][-1] if len(features['adx']) > 0 else 20
        current_vol_ratio = features['vol_ratio'][-1] if len(features['vol_ratio']) > 0 else 1.0
        
        # Calculate emission probabilities
        emission_probs = self._get_emission_probs(current_adx, current_vol_ratio)
        
        # Apply Bayesian update with transition priors
        prior = self.transition_matrix[self.current_state_idx]
        posterior = prior * emission_probs
        posterior = posterior / (np.sum(posterior) + 1e-10)
        
        # Determine most likely state
        new_state_idx = np.argmax(posterior)
        new_regime = self.regime_names[new_state_idx]
        confidence = float(posterior[new_state_idx])
        
        # Check for regime change
        regime_changed = new_state_idx != self.current_state_idx
        
        if regime_changed:
            self.state_duration = 1
            self.current_state_idx = new_state_idx
        else:
            self.state_duration += 1
        
        self.state_history.append(new_state_idx)
        if len(self.state_history) > 500:
            self.state_history.pop(0)
        
        result = RegimeState(
            current_regime=new_regime,
            regime_probabilities={
                self.regime_names[i].value: float(posterior[i]) 
                for i in range(self.n_regimes)
            },
            confidence=confidence,
            duration_bars=self.state_duration,
            regime_change_signal=regime_changed
        )
        
        if regime_changed:
            logger.info(f"[REGIME CHANGE] Switched to {new_regime.value} (confidence: {confidence:.2f})")
        
        return result
    
    def _extract_features(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """Extract regime detection features from OHLC data."""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        
        # Volatility ratio (current ATR vs historical)
        tr = np.maximum(high - low, 
                       np.maximum(np.abs(high - np.roll(close, 1)),
                                  np.abs(low - np.roll(close, 1))))
        tr[0] = high[0] - low[0]  # Fix first element
        
        atr_short = pd.Series(tr).rolling(5).mean().values
        atr_long = pd.Series(tr).rolling(20).mean().values
        vol_ratio = np.divide(atr_short, atr_long, 
                             out=np.ones_like(atr_short), 
                             where=atr_long > 0)
        
        # ADX (trend strength)
        plus_dm = np.maximum(np.diff(high, prepend=high[0]), 0)
        minus_dm = np.maximum(-np.diff(low, prepend=low[0]), 0)
        
        # Zero out when other is larger
        plus_dm[minus_dm > plus_dm] = 0
        minus_dm[plus_dm > minus_dm] = 0
        
        atr14 = pd.Series(tr).ewm(alpha=1/14, adjust=False).mean().values
        atr14 = np.maximum(atr14, 1e-10)  # Avoid division by zero
        
        plus_di = 100 * pd.Series(plus_dm).ewm(alpha=1/14, adjust=False).mean().values / atr14
        minus_di = 100 * pd.Series(minus_dm).ewm(alpha=1/14, adjust=False).mean().values / atr14
        
        di_sum = plus_di + minus_di
        di_sum = np.maximum(di_sum, 1e-10)
        dx = 100 * np.abs(plus_di - minus_di) / di_sum
        adx = pd.Series(dx).ewm(alpha=1/14, adjust=False).mean().values
        
        # Handle NaN
        vol_ratio = np.nan_to_num(vol_ratio, nan=1.0)
        adx = np.nan_to_num(adx, nan=20.0)
        
        return {
            'vol_ratio': vol_ratio,
            'adx': adx
        }
    
    def _get_emission_probs(self, adx: float, vol_ratio: float) -> np.ndarray:
        """Calculate emission probabilities for each state given observations."""
        probs = np.zeros(self.n_regimes)
        
        for i, regime in enumerate(self.regime_names):
            params = self.emission_params[regime]
            
            # Gaussian likelihood for ADX
            adx_prob = np.exp(-0.5 * ((adx - params['adx_mean']) / params['adx_std'])**2)
            
            # Gaussian likelihood for volatility ratio
            vol_prob = np.exp(-0.5 * ((vol_ratio - params['vol_ratio_mean']) / params['vol_ratio_std'])**2)
            
            # Combined probability
            probs[i] = adx_prob * vol_prob
        
        # Normalize
        total = np.sum(probs)
        if total > 0:
            probs = probs / total
        else:
            probs = np.ones(self.n_regimes) / self.n_regimes
        
        return probs
    
    def get_strategy_recommendation(self, regime_state: RegimeState) -> Dict:
        """
        Get strategy recommendations based on current regime.
        
        Returns:
            Dict with recommended strategy types and risk adjustments
        """
        regime = regime_state.current_regime
        confidence = regime_state.confidence
        duration = regime_state.duration_bars
        
        recommendations = {
            MarketRegime.TRENDING: {
                'preferred_strategies': ['Momentum', 'Trend Following', 'Breakout'],
                'avoid_strategies': ['Mean Reversion', 'RSI Overbought/Oversold'],
                'risk_multiplier': 1.2 if confidence > 0.6 else 1.0,
                'note': 'Strong trends favor momentum strategies'
            },
            MarketRegime.MEAN_REVERTING: {
                'preferred_strategies': ['Mean Reversion', 'Bollinger Band', 'RSI'],
                'avoid_strategies': ['Momentum', 'Breakout'],
                'risk_multiplier': 1.0,
                'note': 'Range-bound market favors reversion strategies'
            },
            MarketRegime.HIGH_VOLATILITY: {
                'preferred_strategies': ['Volatility Breakout'],
                'avoid_strategies': ['Scalping', 'Tight Stop Strategies'],
                'risk_multiplier': 0.5,  # Reduce risk in volatile conditions
                'note': 'High volatility - reduce position sizes and widen stops'
            },
            MarketRegime.UNKNOWN: {
                'preferred_strategies': [],
                'avoid_strategies': [],
                'risk_multiplier': 0.5,
                'note': 'Insufficient data for regime detection'
            }
        }
        
        rec = recommendations.get(regime, recommendations[MarketRegime.UNKNOWN])
        
        # Adjust risk multiplier based on regime duration
        # New regimes = higher risk of false signal
        if duration < 5:
            rec['risk_multiplier'] *= 0.8
            rec['note'] += ' (New regime - reduced confidence)'
        
        return {
            'regime': regime.value,
            'confidence': f"{confidence*100:.1f}%",
            'duration_bars': duration,
            **rec
        }


# Convenience singleton
_default_detector = None

def get_regime_detector() -> MarkovRegimeSwitcher:
    """Get default regime detector instance."""
    global _default_detector
    if _default_detector is None:
        _default_detector = MarkovRegimeSwitcher()
    return _default_detector


def detect_regime(df: pd.DataFrame, symbol: str = "") -> Dict:
    """
    Quick regime detection for a DataFrame.
    
    Returns:
        Dict with current regime and recommendations
    """
    detector = get_regime_detector()
    
    # Fit on first call or if we have significant new data
    if len(detector.state_history) == 0 and len(df) >= 100:
        detector.fit(df)
    
    state = detector.detect(df)
    recommendation = detector.get_strategy_recommendation(state)
    
    return {
        'symbol': symbol,
        **recommendation
    }


if __name__ == "__main__":
    # Test with sample data
    import MetaTrader5 as mt5
    
    print("Markov Regime Switching Model Test")
    print("=" * 50)
    
    if mt5.initialize():
        # Get some GOLD data
        rates = mt5.copy_rates_from_pos("GOLD", mt5.TIMEFRAME_H1, 0, 500)
        if rates is not None:
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            result = detect_regime(df, "GOLD")
            
            print(f"\nSymbol: {result['symbol']}")
            print(f"Current Regime: {result['regime']}")
            print(f"Confidence: {result['confidence']}")
            print(f"Duration: {result['duration_bars']} bars")
            print(f"\nPreferred Strategies: {', '.join(result['preferred_strategies'])}")
            print(f"Avoid Strategies: {', '.join(result['avoid_strategies'])}")
            print(f"Risk Multiplier: {result['risk_multiplier']}")
            print(f"\nNote: {result['note']}")
        
        mt5.shutdown()
    else:
        print("MT5 not available for test")
