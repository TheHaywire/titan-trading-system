"""
Institutional Quantitative Feature Engine
==========================================
Practitioner-grade features used to generate signals in systematic trading.

Each feature class provides:
- compute(): Raw feature calculation
- normalize(): Z-score or percentile normalization  
- interpret(): Trading interpretation (e.g., "TRENDING", "MEAN-REVERTING")
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any


# =============================================================================
# NORMALIZATION UTILITIES
# =============================================================================

def rolling_zscore(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling z-score: (value - rolling_mean) / rolling_std"""
    mean = series.rolling(window, min_periods=20).mean()
    std = series.rolling(window, min_periods=20).std()
    return (series - mean) / std.replace(0, np.nan)


def rolling_percentile(series: pd.Series, window: int = 252) -> pd.Series:
    """Rolling percentile rank (0-100)"""
    def pct_rank(x):
        if len(x) < 2:
            return 50.0
        return (x.values < x.values[-1]).sum() / (len(x) - 1) * 100
    return series.rolling(window, min_periods=20).apply(pct_rank, raw=False)


# =============================================================================
# MOMENTUM FEATURES
# =============================================================================

class MomentumFeatures:
    """Captures trend persistence and momentum acceleration."""
    
    @staticmethod
    def compute_roc(close: pd.Series, periods: list = [5, 10, 20]) -> Dict[str, pd.Series]:
        """
        Price Rate of Change: (price_t / price_{t-N}) - 1
        WHY: Captures trend persistence; building block for momentum.
        TRADING USE: ROC > 0 and increasing = strong uptrend, scale IN. ROC reversing = scale OUT.
        """
        result = {}
        for n in periods:
            result[f'roc_{n}'] = (close / close.shift(n) - 1) * 100
        return result
    
    @staticmethod
    def compute_return_autocorrelation(close: pd.Series, lag: int = 1, window: int = 20) -> pd.Series:
        """
        Correlation between r_t and r_{t-lag} over a rolling window.
        WHY: Positive = momentum regime (winners keep winning). Negative = mean reversion regime.
        TRADING USE:
          - autocorr > 0.3 → USE trend-following strategies
          - autocorr < -0.3 → USE mean-reversion strategies
          - Near 0 → Market is random, REDUCE POSITION SIZE
        """
        returns = close.pct_change()
        lagged = returns.shift(lag)
        
        def corr_func(x):
            if len(x) < 5:
                return 0
            df = pd.DataFrame({'ret': x.values, 'lag': x.values})
            # Need to create proper lagged series
            ret = pd.Series(x.values[lag:])
            lag_ret = pd.Series(x.values[:-lag])
            if len(ret) < 2:
                return 0
            return ret.corr(lag_ret) if not np.isnan(ret.corr(lag_ret)) else 0
        
        # Simpler approach
        autocorr = returns.rolling(window).apply(
            lambda x: pd.Series(x).autocorr(lag=lag) if len(x) > lag else 0,
            raw=False
        )
        return autocorr.fillna(0)
    
    @staticmethod
    def compute_price_acceleration(close: pd.Series, period: int = 10) -> pd.Series:
        """
        Second derivative of price (momentum of momentum).
        WHY: Detects momentum BUILD-UP or EXHAUSTION before price turns.
        TRADING USE:
          - Positive acceleration + positive ROC = momentum building, ADD to position
          - Negative acceleration + positive ROC = momentum exhausting, TAKE PROFITS
          - Acceleration flip from + to - = Early exit signal
        """
        roc = (close / close.shift(period) - 1) * 100
        acceleration = roc - roc.shift(period)
        return acceleration


# =============================================================================
# MEAN REVERSION FEATURES
# =============================================================================

class MeanReversionFeatures:
    """Detects overextension and reversion pressure."""
    
    @staticmethod
    def compute_bb_percentile(close: pd.Series, window: int = 20, num_std: float = 2.0) -> pd.Series:
        """
        Where price sits within Bollinger Bands (0-1 scale).
        WHY: Mean-reversion pressure near extremes.
        TRADING USE:
          - BBP < 0.1 → Price near lower band, look for LONG entries
          - BBP > 0.9 → Price near upper band, look for SHORT entries or TAKE PROFITS
          - BBP 0.4-0.6 → Neutral, no edge
        """
        sma = close.rolling(window).mean()
        std = close.rolling(window).std()
        upper = sma + (num_std * std)
        lower = sma - (num_std * std)
        bbp = (close - lower) / (upper - lower)
        return bbp.clip(0, 1)
    
    @staticmethod
    def compute_rsi_percentile(close: pd.Series, rsi_period: int = 14, pct_window: int = 252) -> pd.Series:
        """
        RSI mapped to its historical percentile (more robust than fixed 30/70).
        WHY: Adapts to changing volatility regimes. RSI of 40 might be oversold in a bear market.
        TRADING USE:
          - RSI_pct < 10 → Historically oversold for THIS symbol, strong long signal
          - RSI_pct > 90 → Historically overbought, strong short signal or exit longs
        """
        # Compute RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(rsi_period).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        # Convert to percentile
        return rolling_percentile(rsi, pct_window)
    
    @staticmethod
    def compute_zscore_to_ma(close: pd.Series, ma_period: int = 50, std_period: int = 50) -> pd.Series:
        """
        Z-score of price deviation from moving average.
        WHY: Normalized deviation from equilibrium - tells you how "stretched" price is.
        TRADING USE:
          - Z < -2 → 2 std below MA, strong mean-reversion long
          - Z > +2 → 2 std above MA, expect pullback
          - Use for position sizing: larger Z = smaller position (higher risk of snap-back)
        """
        ma = close.rolling(ma_period).mean()
        std = close.rolling(std_period).std()
        return (close - ma) / std.replace(0, np.nan)


# =============================================================================
# VOLATILITY FEATURES
# =============================================================================

class VolatilityFeatures:
    """Risk scaling, regime detection, and setup filtering."""
    
    @staticmethod
    def compute_historical_volatility(close: pd.Series, window: int = 20, annualize: int = 252) -> pd.Series:
        """
        Rolling std of log returns, annualized.
        WHY: Risk scaling; regime detection; filter for setups.
        TRADING USE:
          - High HV → REDUCE position size (same dollar risk = smaller lots)
          - Low HV → Can take LARGER positions
          - HV spike → Often precedes trend moves, be ready
        """
        log_returns = np.log(close / close.shift(1))
        hv = log_returns.rolling(window).std() * np.sqrt(annualize) * 100
        return hv
    
    @staticmethod
    def compute_volatility_of_volatility(close: pd.Series, hv_window: int = 20, vov_window: int = 20) -> pd.Series:
        """
        Standard deviation of Historical Volatility.
        WHY: Measures STABILITY of the risk environment.
        TRADING USE:
          - High VoV → Unstable regime, AVOID new positions or use wider stops
          - Low VoV → Stable regime, can trust your stop distances
        """
        hv = VolatilityFeatures.compute_historical_volatility(close, hv_window)
        vov = hv.rolling(vov_window).std()
        return vov
    
    @staticmethod
    def compute_volatility_regime(close: pd.Series, window: int = 20, lookback: int = 252) -> Tuple[pd.Series, pd.Series]:
        """
        Discrete volatility state: LOW / MEDIUM / HIGH.
        WHY: Different strategies work in different regimes.
        TRADING USE:
          - LOW vol → Mean-reversion works well, trend-following struggles
          - MEDIUM vol → Trend-following works best
          - HIGH vol → Reduce size, use wider stops, or sit out
        
        Returns: (regime_label, hv_percentile)
        """
        hv = VolatilityFeatures.compute_historical_volatility(close, window)
        hv_pct = rolling_percentile(hv, lookback)
        
        def classify(pct):
            if pd.isna(pct):
                return 'MEDIUM'
            if pct < 33:
                return 'LOW'
            elif pct < 67:
                return 'MEDIUM'
            else:
                return 'HIGH'
        
        regime = hv_pct.apply(classify)
        return regime, hv_pct


# =============================================================================
# TIME-SERIES STRUCTURE FEATURES
# =============================================================================

class TimeSeriesFeatures:
    """Characterize the time-series to match strategy to market."""
    
    @staticmethod
    def compute_hurst_exponent(close: pd.Series, window: int = 100, max_lag: int = 20) -> pd.Series:
        """
        Hurst Exponent: Long-range dependence measure.
        WHY: Tells you if the market is trending, random, or mean-reverting.
        
        INTERPRETATION:
          - H > 0.5 → TRENDING (persistence) - Use trend-following, breakouts
          - H = 0.5 → RANDOM WALK - No edge, reduce position size
          - H < 0.5 → MEAN-REVERTING - Use fade strategies, buy dips
        
        TRADING USE:
          - H > 0.6 → Strong trend environment, trail stops, let winners run
          - H < 0.4 → Strong reversion, take quick profits, fade moves
          - Check H before entering: match your strategy to the regime
        """
        def rs_hurst(prices):
            """R/S Analysis for Hurst calculation"""
            if len(prices) < max_lag * 2:
                return 0.5
            
            prices = np.array(prices)
            log_returns = np.diff(np.log(prices))
            
            if len(log_returns) < max_lag:
                return 0.5
            
            lags = range(2, min(max_lag, len(log_returns) // 2))
            rs_values = []
            
            for lag in lags:
                rs_list = []
                for start in range(0, len(log_returns) - lag, lag):
                    chunk = log_returns[start:start + lag]
                    if len(chunk) < 2:
                        continue
                    mean_chunk = np.mean(chunk)
                    cumdev = np.cumsum(chunk - mean_chunk)
                    R = np.max(cumdev) - np.min(cumdev)
                    S = np.std(chunk, ddof=1) if np.std(chunk, ddof=1) > 0 else 1e-10
                    rs_list.append(R / S)
                if rs_list:
                    rs_values.append((lag, np.mean(rs_list)))
            
            if len(rs_values) < 3:
                return 0.5
            
            # Fit log-log regression
            x = np.log([v[0] for v in rs_values])
            y = np.log([v[1] for v in rs_values])
            
            try:
                slope, _ = np.polyfit(x, y, 1)
                return np.clip(slope, 0, 1)
            except Exception:
                return 0.5
        
        return close.rolling(window, min_periods=window).apply(rs_hurst, raw=True).fillna(0.5)


# =============================================================================
# RISK FEATURES
# =============================================================================

class RiskFeatures:
    """Drawdown and de-risking signals."""
    
    @staticmethod
    def compute_drawdown(equity: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """
        Current drawdown from peak and drawdown duration.
        TRADING USE: De-risk when DD exceeds thresholds.
        """
        peak = equity.expanding().max()
        dd = (equity - peak) / peak * 100
        
        # Duration (bars since peak)
        is_at_peak = equity >= peak
        duration = (~is_at_peak).groupby((is_at_peak).cumsum()).cumsum()
        
        return dd, duration
    
    @staticmethod
    def compute_drawdown_acceleration(equity: pd.Series, window: int = 5) -> pd.Series:
        """
        Rate of change of drawdown.
        WHY: Accelerating losses = time to cut risk aggressively.
        TRADING USE:
          - DD_accel < -2%/bar → HALT new trades, consider closing losers
          - DD_accel improving → Can resume normal operations
        """
        dd, _ = RiskFeatures.compute_drawdown(equity)
        dd_change = dd.diff(window)
        return dd_change


# =============================================================================
# MASTER FEATURE ENGINE
# =============================================================================

class QuantFeatureEngine:
    """
    Master class to compute all institutional-grade features.
    
    Usage:
        engine = QuantFeatureEngine()
        features = engine.compute_all(df)
        interpretation = engine.interpret(features)
    """
    
    @staticmethod
    def compute_all(df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute all features from OHLCV data.
        Expects columns: open, high, low, close, volume (optional)
        """
        close = df['close']
        result = df.copy()
        
        # --- MOMENTUM ---
        for name, series in MomentumFeatures.compute_roc(close).items():
            result[name] = series
        result['return_autocorr'] = MomentumFeatures.compute_return_autocorrelation(close)
        result['price_accel'] = MomentumFeatures.compute_price_acceleration(close)
        
        # --- MEAN REVERSION ---
        result['bb_percentile'] = MeanReversionFeatures.compute_bb_percentile(close)
        result['rsi_percentile'] = MeanReversionFeatures.compute_rsi_percentile(close)
        result['zscore_to_ma'] = MeanReversionFeatures.compute_zscore_to_ma(close)
        
        # --- VOLATILITY ---
        result['hist_volatility'] = VolatilityFeatures.compute_historical_volatility(close)
        result['vol_of_vol'] = VolatilityFeatures.compute_volatility_of_volatility(close)
        regime, hv_pct = VolatilityFeatures.compute_volatility_regime(close)
        result['vol_regime'] = regime
        result['vol_percentile'] = hv_pct
        
        # --- TIME-SERIES ---
        result['hurst'] = TimeSeriesFeatures.compute_hurst_exponent(close)
        
        return result
    
    @staticmethod
    def interpret(features: pd.Series) -> Dict[str, str]:
        """
        Convert latest feature values into trading interpretations.
        """
        interp = {}
        
        # Hurst interpretation
        h = features.get('hurst', 0.5)
        if h > 0.55:
            interp['market_character'] = f"TRENDING (H={h:.2f}) → Use breakouts, trail stops"
        elif h < 0.45:
            interp['market_character'] = f"MEAN-REVERTING (H={h:.2f}) → Fade moves, quick profits"
        else:
            interp['market_character'] = f"RANDOM (H={h:.2f}) → No edge, reduce size"
        
        # Volatility regime
        vol_regime = features.get('vol_regime', 'MEDIUM')
        vol_pct = features.get('vol_percentile', 50)
        if vol_regime == 'HIGH':
            interp['vol_action'] = f"HIGH VOL ({vol_pct:.0f}th pct) → Reduce position size, wider stops"
        elif vol_regime == 'LOW':
            interp['vol_action'] = f"LOW VOL ({vol_pct:.0f}th pct) → Mean-reversion favored"
        else:
            interp['vol_action'] = f"NORMAL VOL ({vol_pct:.0f}th pct) → Standard sizing OK"
        
        # Mean reversion signals
        bbp = features.get('bb_percentile', 0.5)
        if bbp < 0.15:
            interp['reversion_signal'] = f"OVERSOLD (BBP={bbp:.2f}) → Look for long entries"
        elif bbp > 0.85:
            interp['reversion_signal'] = f"OVERBOUGHT (BBP={bbp:.2f}) → Take profits or short"
        else:
            interp['reversion_signal'] = f"NEUTRAL (BBP={bbp:.2f}) → No reversion edge"
        
        # Momentum state
        roc = features.get('roc_20', 0)
        accel = features.get('price_accel', 0)
        if roc > 0 and accel > 0:
            interp['momentum_action'] = f"ACCELERATING UP (ROC={roc:.1f}%) → Add to longs"
        elif roc > 0 and accel < 0:
            interp['momentum_action'] = f"DECELERATING UP (ROC={roc:.1f}%) → Tighten stops"
        elif roc < 0 and accel < 0:
            interp['momentum_action'] = f"ACCELERATING DOWN (ROC={roc:.1f}%) → Stay short or out"
        else:
            interp['momentum_action'] = f"MOMENTUM SHIFTING → Watch for reversal"
        
        # Autocorrelation advice
        autocorr = features.get('return_autocorr', 0)
        if autocorr > 0.2:
            interp['strategy_fit'] = f"MOMENTUM REGIME (ρ={autocorr:.2f}) → Trend-following works"
        elif autocorr < -0.2:
            interp['strategy_fit'] = f"REVERSION REGIME (ρ={autocorr:.2f}) → Fade strategies work"
        else:
            interp['strategy_fit'] = f"MIXED REGIME (ρ={autocorr:.2f}) → Be selective"
        
        return interp
    
    @staticmethod
    def get_trading_score(features: pd.Series) -> Dict[str, Any]:
        """
        Combine features into actionable trading scores.
        Returns scores for: trend_strength, mean_reversion_opportunity, risk_level
        """
        scores = {}
        
        # Trend strength (0-100): Higher = stronger trend environment
        h = features.get('hurst', 0.5)
        roc = abs(features.get('roc_20', 0))
        autocorr = features.get('return_autocorr', 0)
        trend_score = (
            (h - 0.5) * 200 +  # Hurst contribution
            min(roc, 10) * 5 +  # ROC contribution (capped)
            autocorr * 50  # Autocorr contribution
        )
        scores['trend_strength'] = np.clip(trend_score, 0, 100)
        
        # Mean reversion opportunity (0-100): Higher = better reversion setup
        bbp = features.get('bb_percentile', 0.5)
        zscore = abs(features.get('zscore_to_ma', 0))
        reversion_score = (
            (1 - abs(bbp - 0.5) * 2) * 50 +  # BBP at extremes
            min(zscore, 3) * 20  # Z-score stretch
        )
        # Flip if BBP at extremes
        if bbp < 0.2 or bbp > 0.8:
            reversion_score = 70 + min(zscore, 2) * 15
        scores['reversion_opportunity'] = np.clip(reversion_score, 0, 100)
        
        # Risk level (0-100): Higher = more dangerous
        vol_pct = features.get('vol_percentile', 50)
        vov = features.get('vol_of_vol', 0)
        risk_score = vol_pct * 0.7 + min(vov, 10) * 3
        scores['risk_level'] = np.clip(risk_score, 0, 100)
        
        # Position size multiplier (0.25 to 1.5)
        if scores['risk_level'] > 70:
            scores['size_multiplier'] = 0.5
        elif scores['risk_level'] > 50:
            scores['size_multiplier'] = 0.75
        elif scores['risk_level'] < 30:
            scores['size_multiplier'] = 1.25
        else:
            scores['size_multiplier'] = 1.0
        
        return scores
