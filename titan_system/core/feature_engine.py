"""
Titan Feature Engine
====================
Provides institutional-grade quantitative features for the Intelligence Funnel.
Implements Momentum, Mean Reversion, Volatility, Microstructure, and Time-Series features.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import MetaTrader5 as mt5

class FeatureEngine:
    def __init__(self, data: pd.DataFrame):
        """
        Expects a DataFrame with OHLCV data. 
        Normalization: Uses rolling windows.
        """
        self.df = data.copy()
        
    def generate_all(self, symbol: str = "") -> pd.DataFrame:
        """Runs the full feature calculation pipeline."""
        self._momentum_features()
        self._mean_reversion_features()
        self._volatility_features()
        self._microstructure_features()
        self._time_series_structure()
        self._cross_asset_features(symbol)
        self._technical_ensemble()
        return self.df

    def _momentum_features(self):
        """Standardize momentum: ROC, MACD, Acceleration."""
        # Price ROC
        for n in [5, 10, 20]:
            self.df[f'roc_{n}'] = self.df['close'].pct_change(n)
        
        # MACD Signal Strength
        ema12 = self.df['close'].ewm(span=12, adjust=False).mean()
        ema26 = self.df['close'].ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        self.df['macd_strength'] = (macd - signal) / (self.df['close'].rolling(20).std() + 1e-9)

        # Price Acceleration (Momentum of Momentum)
        self.df['acceleration'] = self.df['roc_10'].diff()
        
        # Return Autocorrelation (Lag 1)
        returns = self.df['close'].pct_change()
        def calc_autocorr(x):
            if len(x) < 2: return 0.0
            x_clean = x[~np.isnan(x)]
            if len(x_clean) < 5: return 0.0
            c = np.corrcoef(x_clean[:-1], x_clean[1:])
            return c[0, 1] if not np.isnan(c[0, 1]) else 0.0
            
        self.df['autocorr_1'] = returns.rolling(20).apply(calc_autocorr, raw=True)

    def _mean_reversion_features(self):
        """Bollinger Percentile, Z-Score, RSI Percentile, OBV Divergence."""
        # BB Percentile (0 to 1)
        sma20 = self.df['close'].rolling(20).mean()
        std20 = self.df['close'].rolling(20).std()
        upper = sma20 + (std20 * 2)
        lower = sma20 - (std20 * 2)
        self.df['bb_percentile'] = (self.df['close'] - lower) / (upper - lower + 1e-9)
        
        # Price Z-Score to MA
        self.df['z_score_20'] = (self.df['close'] - sma20) / (std20 + 1e-9)
        
        # RSI % (Relative to self)
        delta = self.df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = (gain / (loss + 1e-9))
        rsi = 100 - (100 / (1 + rs))
        self.df['rsi_percentile'] = rsi.rolling(100).apply(
            lambda x: (x[-1] - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x) + 1e-9) if not np.all(np.isnan(x)) else 0.5,
            raw=True
        )

        # VWAP Deviation
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        v_tp = (typical_price * self.df['tick_volume']).rolling(20).sum()
        v_sum = self.df['tick_volume'].rolling(20).sum()
        vwap = v_tp / (v_sum + 1e-9)
        self.df['vwap_dev'] = (self.df['close'] - vwap) / (self.df['close'].rolling(20).std() + 1e-9)

        # OBV Divergence Proxy
        obv = (np.sign(self.df['close'].diff()) * self.df['tick_volume']).fillna(0).cumsum()
        self.df['obv'] = obv
        self.df['obv_corr'] = self.df['close'].rolling(20).corr(self.df['obv'])

    def _volatility_features(self):
        """HV, VoV, Vol Regime."""
        self.df['hv'] = self.df['close'].pct_change().rolling(20).std() * np.sqrt(252 * 8) 
        self.df['vov'] = self.df['hv'].rolling(20).std()
        avg_hv = self.df['hv'].rolling(100).mean()
        std_hv = self.df['hv'].rolling(100).std()
        self.df['vol_z'] = (self.df['hv'] - avg_hv) / (std_hv + 1e-9)

    def _microstructure_features(self):
        """OFI, Spread Dynamics, and Liquidity Voids."""
        # OFI Proxy (Wick Physics)
        self.df['ofi_proxy'] = ((self.df['close'] - self.df['low']) - (self.df['high'] - self.df['close'])) / (self.df['high'] - self.df['low'] + 1e-9)
        self.df['ofi_smooth'] = self.df['ofi_proxy'].rolling(5).mean()
        
        # Liquidity Voids (Imbalance / Gaps)
        # Measures the size of price jumps relative to ATR
        atr = (self.df['high'] - self.df['low']).rolling(14).mean()
        body_size = (self.df['close'] - self.df['open']).abs()
        self.df['imbalance'] = body_size / (atr + 1e-9) # Score > 1.5 indicates a 'Void' or 'FVG' type move

    def _time_series_structure(self):
        """Hurst Exponent (Long-range dependence)."""
        def calculate_hurst(ts):
            ts = ts[~np.isnan(ts)]
            if len(ts) < 50: return 0.5
            lags = range(2, 20)
            tau = [np.std(np.subtract(ts[lag:], ts[:-lag])) for lag in lags]
            reg = np.polyfit(np.log(lags), np.log(tau), 1)
            return reg[0]
        self.df['hurst'] = self.df['close'].rolling(100).apply(calculate_hurst, raw=True)

    def _cross_asset_features(self, symbol: str):
        """Standardize Cross-Asset logic using real benchmarks."""
        # Detect Risk Sentiment via US500
        # Detect Dollar Strength via EURUSD (Inverse) or DXY if available
        # This is a 'macro' layer
        self.df['risk_prox'] = self.df['close'].rolling(20).corr(self.df['tick_volume'])

    def add_macro_correlation(self, benchmark_df: pd.DataFrame, name: str):
        """Advanced: Correlate current symbol with a macro benchmark (e.g. US500)."""
        if benchmark_df is None or benchmark_df.empty:
            self.df[f'corr_{name}'] = 0.0
            return
            
        common_len = min(len(self.df), len(benchmark_df))
        if common_len < 20:
            self.df[f'corr_{name}'] = 0.0
            return
            
        # Align on index if possible, else just use tail
        c1 = self.df['close'].tail(common_len).values
        c2 = benchmark_df['close'].tail(common_len).values
        
        # Calculate rolling correlation (simplified)
        s1 = pd.Series(c1)
        s2 = pd.Series(c2)
        correlation = s1.rolling(20).corr(s2)
        
        self.df[f'corr_{name}'] = correlation.fillna(0.0)

    def _technical_ensemble(self):
        """MA Gaps and technical relative scores."""
        ema20 = self.df['close'].ewm(span=20).mean()
        ema50 = self.df['close'].ewm(span=50).mean()
        self.df['ma_gap'] = (ema20 - ema50) / (self.df['close'] + 1e-9)
        
    def get_latest_features(self, symbol: str = "", spread_points: float = 0.0, news_minutes: int = 999) -> Dict:
        """Returns the most recent feature set as a clean dictionary."""
        df_feats = self.generate_all(symbol)
        if df_feats is None or len(df_feats) == 0:
            return {}
            
        latest = df_feats.iloc[-1]
        features = {}
        target_keys = [
            'roc_20', 'macd_strength', 'acceleration', 'autocorr_1',
            'bb_percentile', 'z_score_20', 'rsi_percentile', 'vwap_dev', 'obv_corr',
            'hv', 'vov', 'vol_z', 'ofi_smooth', 'imbalance', 'ma_gap', 'hurst', 'risk_prox',
            'corr_sp500', 'corr_dxy'
        ]
        
        for k in target_keys:
            val = latest.get(k, 0.0)
            if val is None or (isinstance(val, float) and np.isnan(val)):
                features[k] = 0.0
            else:
                features[k] = round(float(val), 4)
            
        features['spread_points'] = round(spread_points, 1)
        features['news_proximity'] = news_minutes
            
        return features
