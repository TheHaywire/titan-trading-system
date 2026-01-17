"""
ADVANCED Institutional Features
================================
Hedge fund-grade quantitative features:
- Machine Learning factors (PCA)
- Cross-sectional ranking
- Kalman filtering
- Hidden Markov regime detection
- Order flow signals
- Kelly Criterion sizing
- Portfolio correlation management
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List
from sklearn.decomposition import PCA
from scipy.signal import savgol_filter
from hmmlearn import hmm
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# ADVANCED TIME-SERIES FEATURES
# =============================================================================

class AdvancedTimeSeriesFeatures:
    """Sophisticated time-series analysis beyond basic indicators."""
    
    @staticmethod
    def kalman_trend(close: pd.Series, process_variance: float = 0.01) -> Tuple[pd.Series, pd.Series]:
        """
        Kalman filter for trend estimation.
        WHY: Smooths price while being responsive to real moves (better than SMA).
        TRADING USE:
          - Price > Kalman trend = long bias
          - Price < Kalman trend = short bias
          - Kalman uncertainty high = volatile regime, reduce size
        
        Returns: (kalman_estimate, kalman_uncertainty)
        """
        n = len(close)
        x = np.zeros(n)  # State estimate (trend)
        P = np.zeros(n)  # Uncertainty
        
        # Initialize
        x[0] = close.iloc[0]
        P[0] = 1.0
        
        Q = process_variance  # Process noise
        R = 1.0  # Measurement noise
        
        for i in range(1, n):
            # Predict
            x_pred = x[i-1]
            P_pred = P[i-1] + Q
            
            # Update
            K = P_pred / (P_pred + R)  # Kalman gain
            x[i] = x_pred + K * (close.iloc[i] - x_pred)
            P[i] = (1 - K) * P_pred
        
        return pd.Series(x, index=close.index), pd.Series(P, index=close.index)
    
    @staticmethod
    def savitzky_golay_trend(close: pd.Series, window: int = 21, polyorder: int = 3) -> pd.Series:
        """
        Savitzky-Golay filter for noise reduction while preserving trends.
        WHY: Better than moving average at preserving peaks/troughs.
        TRADING USE: Crossovers are higher quality than SMA crossovers.
        """
        if len(close) < window:
            return close
        try:
            filtered = savgol_filter(close.values, window, polyorder)
            return pd.Series(filtered, index=close.index)
        except:
            return close
    
    @staticmethod
    def hmm_regime_detection(returns: pd.Series, n_states: int = 3) -> Tuple[pd.Series, np.ndarray]:
        """
        Hidden Markov Model for regime detection.
        WHY: Probabilistic regime classification (Better than simple vol quantiles).
        TRADING USE:
          - State 0 = Low vol mean-reversion regime
          - State 1 = Normal regime
          - State 2 = High vol trending regime
        
        Returns: (regime_state, transition_probabilities)
        """
        # Prepare data
        X = returns.dropna().values.reshape(-1, 1)
        
        if len(X) < 100:
            return pd.Series([1] * len(returns), index=returns.index), np.eye(n_states)
        
        # Fit HMM
        try:
            model = hmm.GaussianHMM(n_components=n_states, covariance_type="full", n_iter=100)
            model.fit(X)
            states = model.predict(X)
            
            # Pad to match original length
            result = pd.Series([1] * len(returns), index=returns.index)
            result.iloc[-len(states):] = states
            
            return result, model.transmat_
        except:
            return pd.Series([1] * len(returns), index=returns.index), np.eye(n_states)


# =============================================================================
# CROSS-SECTIONAL FEATURES
# =============================================================================

class CrossSectionalFeatures:
    """Features comparing this symbol to a universe of symbols."""
    
    @staticmethod
    def compute_momentum_rank(symbol_returns: pd.Series, universe_returns: Dict[str, pd.Series], 
                             lookback: int = 20) -> pd.Series:
        """
        Cross-sectional momentum ranking.
        WHY: Relative strength - leaders tend to keep leading.
        TRADING USE:
          - Rank > 80th percentile → Strong relative momentum, OVERWEIGHT
          - Rank < 20th percentile → Weak relative momentum, UNDERWEIGHT
        
        Returns percentile rank (0-100)
        """
        # Calculate returns over lookback
        symbol_cum_ret = symbol_returns.rolling(lookback).sum()
        
        # Get universe returns
        universe_cum_rets = {}
        for sym, rets in universe_returns.items():
            universe_cum_rets[sym] = rets.rolling(lookback).sum()
        
        # Calculate rank
        ranks = []
        for i in range(len(symbol_cum_ret)):
            if pd.isna(symbol_cum_ret.iloc[i]):
                ranks.append(50)
                continue
            
            sym_ret = symbol_cum_ret.iloc[i]
            universe_rets_at_i = [universe_cum_rets[s].iloc[i] if i < len(universe_cum_rets[s]) else 0 
                                 for s in universe_cum_rets]
            universe_rets_at_i = [r for r in universe_rets_at_i if not pd.isna(r)]
            
            if len(universe_rets_at_i) == 0:
                ranks.append(50)
            else:
                rank_pct = (sum([1 for r in universe_rets_at_i if r < sym_ret]) / len(universe_rets_at_i)) * 100
                ranks.append(rank_pct)
        
        return pd.Series(ranks, index=symbol_returns.index)


# =============================================================================
# MACHINE LEARNING FEATURES
# =============================================================================

class MLFeatures:
    """Machine learning-derived features."""
    
    @staticmethod
    def compute_pca_factors(features_df: pd.DataFrame, n_components: int = 3) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        PCA dimensionality reduction on raw features.
        WHY: Extract latent factors, de-noise signals.
        TRADING USE:
          - PC1 usually captures trend
          - PC2 usually captures mean-reversion
          - Use factor loadings to understand market drivers
        
        Returns: (pca_factors_df, explained_variance_ratio)
        """
        # Select numeric columns
        numeric_cols = features_df.select_dtypes(include=[np.number]).columns
        data = features_df[numeric_cols].dropna()
        
        if len(data) < n_components or data.shape[1] < n_components:
            return pd.DataFrame(), np.array([])
        
        # Standardize
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        data_scaled = scaler.fit_transform(data)
        
        # PCA
        pca = PCA(n_components=n_components)
        factors = pca.fit_transform(data_scaled)
        
        factor_df = pd.DataFrame(
            factors,
            index=data.index,
            columns=[f'PC{i+1}' for i in range(n_components)]
        )
        
        return factor_df, pca.explained_variance_ratio_
    
    @staticmethod
    def rolling_beta(returns: pd.Series, market_returns: pd.Series, window: int = 60) -> pd.Series:
        """
        Rolling beta to market.
        WHY: Understand how much systematic risk you're taking.
        TRADING USE:
          - Beta > 1.5 → High leverage to market, reduce size in uncertain times
          - Beta < 0.5 → Defensive asset, can size up
        """
        def calc_beta(y, x):
            if len(x) < 10 or len(y) < 10:
                return 1.0
            covariance = np.cov(y, x)[0][1]
            variance = np.var(x)
            return covariance / variance if variance > 0 else 1.0
        
        beta_series = []
        for i in range(len(returns)):
            if i < window:
                beta_series.append(1.0)
            else:
                y = returns.iloc[i-window:i].values
                x = market_returns.iloc[i-window:i].values
                beta_series.append(calc_beta(y, x))
        
        return pd.Series(beta_series, index=returns.index)


# =============================================================================
# ORDER FLOW / MICROSTRUCTURE (Approximations for FX/Futures)
# =============================================================================

class OrderFlowFeatures:
    """Microstructure signals (approximated for MT5 data)."""
    
    @staticmethod
    def compute_vwap_deviation(df: pd.DataFrame, session_reset: bool = True) -> pd.Series:
        """
        Deviation from VWAP.
        WHY: Price tends to revert to VWAP intraday (fair value magnet).
        TRADING USE:
          - Price > VWAP + 1σ → Overbought intraday, fade
          - Price < VWAP - 1σ → Oversold intraday, buy
        """
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        volume = df['volume']
        
        if session_reset:
            # Reset VWAP each day (assumes time column exists)
            if 'time' in df.columns:
                df['date'] = pd.to_datetime(df['time']).dt.date
                vwap = df.groupby('date').apply(
                    lambda x: (x['close'] * x['volume']).cumsum() / x['volume'].cumsum()
                ).reset_index(level=0, drop=True)
            else:
                vwap = (typical_price * volume).cumsum() / volume.cumsum()
        else:
            vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        deviation = (df['close'] - vwap) / vwap * 100
        return deviation
    
    @staticmethod
    def tick_volume_imbalance(close: pd.Series, volume: pd.Series, window: int = 20) -> pd.Series:
        """
        Tick volume imbalance (buy vs sell pressure approximation).
        WHY: High buy volume predicts continuation.
        TRADING USE:
          - Imbalance > 0.6 → Strong buying, expect upside
          - Imbalance < 0.4 → Strong selling, expect downside
        
        Note: This is an approximation - real OFI requires tick data
        """
        # Approximate: up bars = buy volume, down bars = sell volume
        price_change = close.diff()
        buy_volume = volume.where(price_change > 0, 0)
        sell_volume = volume.where(price_change < 0, 0)
        
        buy_vol_sum = buy_volume.rolling(window).sum()
        sell_vol_sum = sell_volume.rolling(window).sum()
        total_vol = buy_vol_sum + sell_vol_sum
        
        imbalance = buy_vol_sum / total_vol.replace(0, np.nan)
        return imbalance.fillna(0.5)


# =============================================================================
# PORTFOLIO / RISK MANAGEMENT FEATURES
# =============================================================================

class PortfolioFeatures:
    """Portfolio-level risk and correlation features."""
    
    @staticmethod
    def compute_correlation_risk(current_positions: List[str], 
                                 returns_dict: Dict[str, pd.Series],
                                 lookback: int = 60) -> Dict[str, float]:
        """
        Correlation clamp for portfolio risk.
        WHY: Prevent over-concentration in correlated bets.
        TRADING USE:
          - max_pairwise_corr > 0.8 → Stop taking correlated positions
          - avg_correlation > 0.5 → Portfolio too concentrated
        """
        if len(current_positions) < 2:
            return {'max_corr': 0, 'avg_corr': 0, 'risk_score': 0}
        
        # Build correlation matrix
        corr_matrix = pd.DataFrame()
        for sym in current_positions:
            if sym in returns_dict:
                corr_matrix[sym] = returns_dict[sym].tail(lookback)
        
        if corr_matrix.empty or corr_matrix.shape[1] < 2:
            return {'max_corr': 0, 'avg_corr': 0, 'risk_score': 0}
        
        corr = corr_matrix.corr()
        
        # Get max pairwise correlation (excluding diagonal)
        np.fill_diagonal(corr.values, 0)
        max_corr = corr.abs().max().max()
        avg_corr = corr.abs().mean().mean()
        
        # Risk score: 0-100 (higher = more concentrated)
        risk_score = (max_corr * 50 + avg_corr * 50)
        
        return {
            'max_corr': max_corr,
            'avg_corr': avg_corr,
            'risk_score': risk_score,
            'action': 'STOP ADDING' if max_corr > 0.8 else ('REDUCE CORR' if avg_corr > 0.5 else 'OK')
        }
    
    @staticmethod
    def kelly_criterion_size(win_rate: float, avg_win: float, avg_loss: float, 
                            max_leverage: float = 1.0) -> float:
        """
        Kelly Criterion for optimal position sizing.
        WHY: Maximize long-term growth rate.
        TRADING USE:
          - Kelly fraction tells you optimal % of capital to risk
          - Use 1/4 Kelly to 1/2 Kelly for safety
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade size
            avg_loss: Average losing trade size (positive)
            max_leverage: Cap on Kelly output
        
        Returns: Fraction of capital to allocate (0-1)
        """
        if avg_loss == 0:
            return 0
        
        win_loss_ratio = avg_win / avg_loss
        kelly_fraction = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Cap at max leverage and ensure non-negative
        kelly_capped = max(0, min(kelly_fraction, max_leverage))
        
        # Use half-Kelly for conservatism
        return kelly_capped * 0.5


# =============================================================================
# ADVANCED MASTER ENGINE
# =============================================================================

class AdvancedQuantEngine:
    """
    Advanced institutional feature engine.
    Combines basic features with ML, microstructure, and portfolio analytics.
    """
    
    @staticmethod
    def compute_all_advanced(df: pd.DataFrame, 
                            universe_returns: Dict[str, pd.Series] = None,
                            current_positions: List[str] = None,
                            market_returns: pd.Series = None) -> pd.DataFrame:
        """
        Compute all advanced features.
        
        Args:
            df: OHLCV dataframe
            universe_returns: Dict of {symbol: returns} for cross-sectional analysis
            current_positions: List of current position symbols for correlation analysis
            market_returns: Market benchmark returns for beta calculation
        """
        result = df.copy()
        close = df['close']
        returns = close.pct_change()
        
        # --- ADVANCED TIME-SERIES ---
        kalman, kalman_unc = AdvancedTimeSeriesFeatures.kalman_trend(close)
        result['kalman_trend'] = kalman
        result['kalman_uncertainty'] = kalman_unc
        
        result['savgol_trend'] = AdvancedTimeSeriesFeatures.savitzky_golay_trend(close)
        
        hmm_states, hmm_trans = AdvancedTimeSeriesFeatures.hmm_regime_detection(returns)
        result['hmm_regime'] = hmm_states
        
        # --- CROSS-SECTIONAL ---
        if universe_returns is not None:
            result['momentum_rank'] = CrossSectionalFeatures.compute_momentum_rank(
                returns, universe_returns, lookback=20
            )
        
        # --- MACHINE LEARNING ---
        if market_returns is not None and len(market_returns) == len(returns):
            result['market_beta'] = MLFeatures.rolling_beta(returns, market_returns)
        
        # --- ORDER FLOW ---
        result['vwap_deviation'] = OrderFlowFeatures.compute_vwap_deviation(df)
        result['volume_imbalance'] = OrderFlowFeatures.tick_volume_imbalance(close, df['volume'])
        
        return result
    
    @staticmethod
    def get_advanced_signals(features: pd.Series, 
                            win_rate: float = 0.55,
                            avg_win: float = 2.0,
                            avg_loss: float = 1.0,
                            current_positions: List[str] = None,
                            returns_dict: Dict[str, pd.Series] = None) -> Dict:
        """
        Generate advanced trading signals.
        """
        signals = {}
        
        # Kalman signal
        if 'kalman_trend' in features:
            close = features.get('close', 0)
            kalman = features.get('kalman_trend', close)
            if close > kalman:
                signals['kalman_signal'] = 'LONG'
                signals['kalman_distance'] = ((close - kalman) / kalman * 100)
            else:
                signals['kalman_signal'] = 'SHORT'
                signals['kalman_distance'] = ((close - kalman) / kalman * 100)
        
        # HMM regime
        hmm_state = int(features.get('hmm_regime', 1))
        if hmm_state == 0:
            signals['hmm_advice'] = 'LOW VOL - Use mean-reversion'
        elif hmm_state == 2:
            signals['hmm_advice'] = 'HIGH VOL - Use trend-following'
        else:
            signals['hmm_advice'] = 'NORMAL - Standard strategies'
        
        # Cross-sectional momentum
        mom_rank = features.get('momentum_rank', 50)
        if mom_rank > 80:
            signals['relative_strength'] = 'LEADER - Overweight this symbol'
        elif mom_rank < 20:
            signals['relative_strength'] = 'LAGGARD - Underweight or avoid'
        else:
            signals['relative_strength'] = 'NEUTRAL'
        
        # VWAP signal
        vwap_dev = features.get('vwap_deviation', 0)
        if vwap_dev > 0.5:
            signals['vwap_signal'] = 'Above VWAP - Consider fade or take profits'
        elif vwap_dev < -0.5:
            signals['vwap_signal'] = 'Below VWAP - Consider long entries'
        else:
            signals['vwap_signal'] = 'Near VWAP - Fair value'
        
        # Volume imbalance
        vol_imb = features.get('volume_imbalance', 0.5)
        if vol_imb > 0.6:
            signals['flow_signal'] = 'BUYING PRESSURE - Bullish'
        elif vol_imb < 0.4:
            signals['flow_signal'] = 'SELLING PRESSURE - Bearish'
        else:
            signals['flow_signal'] = 'BALANCED'
        
        # Kelly sizing
        kelly_size = PortfolioFeatures.kelly_criterion_size(win_rate, avg_win, avg_loss)
        signals['kelly_fraction'] = kelly_size
        signals['kelly_advice'] = f'Optimal size: {kelly_size*100:.1f}% of capital'
        
        # Portfolio correlation
        if current_positions and returns_dict:
            corr_risk = PortfolioFeatures.compute_correlation_risk(
                current_positions, returns_dict
            )
            signals['portfolio_risk'] = corr_risk
        
        return signals
    
    @staticmethod
    def get_institutional_recommendation(basic_features: pd.Series, 
                                        advanced_signals: Dict) -> str:
        """
        Combine all signals into final institutional recommendation.
        """
        # Get basic metrics
        hurst = basic_features.get('hurst', 0.5)
        kalman_signal = advanced_signals.get('kalman_signal', 'NEUTRAL')
        hmm_advice = advanced_signals.get('hmm_advice', '')
        mom_rank = basic_features.get('momentum_rank', 50) if 'momentum_rank' in basic_features else advanced_signals.get('momentum_rank', 50)
        vwap_signal = advanced_signals.get('vwap_signal', '')
        flow = advanced_signals.get('flow_signal', 'BALANCED')
        kelly = advanced_signals.get('kelly_fraction', 0.5)
        
        rec = []
        rec.append(f"=== INSTITUTIONAL TRADE RECOMMENDATION ===\n")
        
        # Market regime
        if hurst > 0.6:
            rec.append(f"Market Regime: STRONG TREND (H={hurst:.2f})")
            rec.append(f"  -> Strategy: Trend-following, breakouts")
        elif hurst < 0.4:
            rec.append(f"Market Regime: MEAN-REVERTING (H={hurst:.2f})")
            rec.append(f"  -> Strategy: Fade extremes, range-bound")
        else:
            rec.append(f"Market Regime: TRANSITIONAL (H={hurst:.2f})")
            rec.append(f"  -> Strategy: Be selective, reduce size")
        
        # Kalman + HMM
        rec.append(f"\nKalman Filter: {kalman_signal}")
        rec.append(f"HMM Regime: {hmm_advice}")
        
        # Relative strength
        if 'relative_strength' in advanced_signals:
            rec.append(f"Relative Strength: {advanced_signals['relative_strength']}")
        
        # Intraday signals
        rec.append(f"\nIntraday Microstructure:")
        rec.append(f"  VWAP: {vwap_signal}")
        rec.append(f"  Order Flow: {flow}")
        
        # Position sizing
        rec.append(f"\nOptimal Position Size:")
        rec.append(f"  Kelly Criterion: {kelly*100:.1f}% of capital")
        rec.append(f"  Recommendation: Use {kelly*0.5*100:.1f}% (Half-Kelly for safety)")
        
        # Portfolio risk
        if 'portfolio_risk' in advanced_signals:
            prisk = advanced_signals['portfolio_risk']
            rec.append(f"\nPortfolio Correlation Risk:")
            rec.append(f"  Max Pairwise: {prisk['max_corr']:.2f}")
            rec.append(f"  Action: {prisk['action']}")
        
        # Final action
        rec.append(f"\n{'='*45}")
        rec.append(f"FINAL ACTION:")
        
        if kalman_signal == 'LONG' and flow == 'BUYING PRESSURE - Bullish' and hurst > 0.55:
            rec.append(f"  >> STRONG LONG SIGNAL <<")
            rec.append(f"  Entry: Market or pullback to Kalman trend")
            rec.append(f"  Size: {kelly*0.5*100:.1f}% of capital")
        elif kalman_signal == 'SHORT' and flow == 'SELLING PRESSURE - Bearish' and hurst > 0.55:
            rec.append(f"  >> STRONG SHORT SIGNAL <<")
            rec.append(f"  Entry: Market or rally to Kalman trend")
            rec.append(f"  Size: {kelly*0.5*100:.1f}% of capital")
        else:
            rec.append(f"  >> MIXED SIGNALS - Be cautious <<")
            rec.append(f"  Size: {kelly*0.25*100:.1f}% of capital (reduced)")
        
        return "\n".join(rec)
