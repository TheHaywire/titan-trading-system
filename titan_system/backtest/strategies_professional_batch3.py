"""
PROFESSIONAL BATCH 3: Complete Implementations
==============================================
Remaining volatility, macro, and ML strategies - FULL CODE
"""

import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


# ========== VOLATILITY STRATEGIES (Remaining) ==========

class HistoricalVolatilityRatio_Strategy(BaseStrategy):
    """Trade based on historical volatility ratio changes"""
    def __init__(self):
        super().__init__("Historical Volatility Ratio")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Short-term vs long-term volatility
        df['vol_short'] = df['close'].pct_change().rolling(10).std() * np.sqrt(252)
        df['vol_long'] = df['close'].pct_change().rolling(50).std() * np.sqrt(252)
        df['vol_ratio'] = df['vol_short'] / df['vol_long']
        return df
    
    def analyze(self, df):
        if len(df) < 55:
            return None
        curr = df.iloc[-1]
        
        # Trade when short-term vol expands vs long-term
        if curr['vol_ratio'] > 1.5:
            # High vol - trade breakouts
            if curr['close'] > curr['ema21'] and curr['rsi'] > 50:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'] * 2,
                    'take_profit': curr['close'] + curr['atr'] * 4
                }
            elif curr['close'] < curr['ema21'] and curr['rsi'] < 50:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'] * 2,
                    'take_profit': curr['close'] - curr['atr'] * 4
                }
        return None


class VolatilityTargeting_Strategy(BaseStrategy):
    """Position size based on volatility targeting"""
    def __init__(self):
        super().__init__("Volatility Targeting")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Realized volatility
        df['realized_vol'] = df['close'].pct_change().rolling(20).std() * np.sqrt(252)
        df['target_vol'] = 0.15  # 15% target
        df['vol_scalar'] = df['target_vol'] / df['realized_vol']
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        
        # Standard trend following but with vol-adjusted sizing
        if curr['ema21'] > curr['ema50']:
            if curr['close'] <= curr['ema21'] * 1.003:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 2,
                    'position_scalar': min(2.0, max(0.5, curr['vol_scalar']))
                }
        elif curr['ema21'] < curr['ema50']:
            if curr['close'] >= curr['ema21'] * 0.997:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'],
                    'take_profit': curr['close'] - curr['atr'] * 2,
                    'position_scalar': min(2.0, max(0.5, curr['vol_scalar']))
                }
        return None


# ========== MACRO/FUNDAMENTAL STRATEGIES ==========

class DayOfWeekEffect_Strategy(BaseStrategy):
    """Trade based on day of week patterns"""
    def __init__(self):
        super().__init__("Day of Week Effect")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        df['day_of_week'] = pd.to_datetime(df['time']).dt.dayofweek
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Avoid Mondays (weekend gap risk) and Fridays (rollover)
        if curr['day_of_week'] in [0, 4]:
            return None
        
        # Trade Tuesday-Thursday (best liquidity)
        if 1 <= curr['day_of_week'] <= 3:
            if curr['macd_hist'] > 0 and curr['adx'] > 20:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'] * 1.5,
                    'take_profit': curr['close'] + curr['atr'] * 2.5
                }
            elif curr['macd_hist'] < 0 and curr['adx'] > 20:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'] * 1.5,
                    'take_profit': curr['close'] - curr['atr'] * 2.5
                }
        return None


class MonthlySeasonality_Strategy(BaseStrategy):
    """Trade based on monthly seasonality patterns"""
    def __init__(self):
        super().__init__("Monthly Seasonality")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        df['month'] = pd.to_datetime(df['time']).dt.month
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Historically strong months for gold: Aug, Sep, Jan
        strong_months = [1, 8, 9]
        # Weak months: Mar, Oct
        weak_months = [3, 10]
        
        if curr['month'] in strong_months:
            # Bullish bias
            if curr['close'] > curr['ema21'] and curr['rsi'] > 45:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['ema50'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        elif curr['month'] in weak_months:
            # Bearish bias
            if curr['close'] < curr['ema21'] and curr['rsi'] < 55:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['ema50'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# ========== MACHINE LEARNING INSPIRED ==========

class SupportVectorMachine_Strategy(BaseStrategy):
    """SVM-inspired classification strategy"""
    def __init__(self):
        super().__init__("SVM Classification")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Feature engineering
        df['mom_5'] = df['close'].pct_change(5)
        df['mom_10'] = df['close'].pct_change(10)
        df['mom_20'] = df['close'].pct_change(20)
        df['vol_ratio'] = df['atr'] / df['atr'].rolling(20).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        
        # Decision boundary (manually crafted, SVM-inspired)
        # Score based on momentum and volatility
        score = 0
        
        # Momentum features
        if curr['mom_5'] > 0:
            score += 1
        if curr['mom_10'] > 0:
            score += 1
        if curr['mom_20'] > 0:
            score += 1
        
        # Technical features
        if curr['rsi'] > 55:
            score += 1
        if curr['macd_hist'] > 0:
            score += 1
        if curr['adx'] > 25:
            score += 1
        
        # Classification
        if score >= 5:  # Strong bullish
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - curr['atr'] * 1.5,
                'take_profit': curr['close'] + curr['atr'] * 2.5
            }
        elif score <= 1:  # Strong bearish
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + curr['atr'] * 1.5,
                'take_profit': curr['close'] - curr['atr'] * 2.5
            }
        return None


class NeuralNetworkSignals_Strategy(BaseStrategy):
    """Neural network-inspired signal processing"""
    def __init__(self):
        super().__init__("Neural Network Signals")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        return df
    
    def sigmoid(self, x):
        """Activation function"""
        return 1 / (1 + np.exp(-x))
    
    def analyze(self, df):
        if len(df) < 30:
            return None
        curr = df.iloc[-1]
        
        # Input layer: normalized features
        inputs = np.array([
            (curr['rsi'] - 50) / 50,  # Normalize to [-1, 1]
            curr['macd_hist'] / curr['atr'],
            (curr['close'] - curr['ema21']) / curr['atr']
        ])
        
        # Hidden layer (simplified, hand-crafted weights)
        weights = np.array([0.5, 0.3, 0.2])
        hidden = np.dot(inputs, weights)
        
        # Output layer with sigmoid activation
        output = self.sigmoid(hidden)
        
        # Trading decision
        if output > 0.7:  # Strong bullish signal
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 2
            }
        elif output < 0.3:  # Strong bearish signal
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + curr['atr'],
                'take_profit': curr['close'] - curr['atr'] * 2
            }
        return None


class GeneticAlgorithmOptimized_Strategy(BaseStrategy):
    """GA-optimized parameter strategy"""
    def __init__(self):
        super().__init__("Genetic Algorithm Optimized")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # "Evolved" parameters (simulated GA optimization)
        df['ema_fast'] = df['close'].ewm(span=13).mean()
        df['ema_slow'] = df['close'].ewm(span=34).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 40:
            return None
        curr = df.iloc[-1]
        
        # "Fitness-optimized" rules
        if curr['ema_fast'] > curr['ema_slow']:
            if curr['rsi'] > 52 and curr['rsi'] < 78:
                if curr['adx'] > 22:
                    return {
                        'direction': 'BUY',
                        'stop_loss': curr['ema_slow'] - curr['atr'] * 0.8,
                        'take_profit': curr['close'] + curr['atr'] * 3.2
                    }
        elif curr['ema_fast'] < curr['ema_slow']:
            if curr['rsi'] < 48 and curr['rsi'] > 22:
                if curr['adx'] > 22:
                    return {
                        'direction': 'SELL',
                        'stop_loss': curr['ema_slow'] + curr['atr'] * 0.8,
                        'take_profit': curr['close'] - curr['atr'] * 3.2
                    }
        return None


# ========== HYBRID STRATEGIES ==========

class ADX_BollingerSqueeze_Strategy(BaseStrategy):
    """ADX trend + Bollinger squeeze combination"""
    def __init__(self):
        super().__init__("ADX + Bollinger Squeeze")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Bollinger bandwidth
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        df['bb_width_ma'] = df['bb_width'].rolling(20).mean()
        df['squeeze'] = df['bb_width'] < df['bb_width_ma'] * 0.8
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Trade breakout after squeeze + strong trend
        if prev['squeeze'] and not curr['squeeze']:  # Squeeze release
            if curr['adx'] > 25:  # Strong trend
                if curr['close'] > curr['bb_mid']:
                    return {
                        'direction': 'BUY',
                        'stop_loss': curr['bb_lower'],
                        'take_profit': curr['close'] + curr['atr'] * 3
                    }
                else:
                    return {
                        'direction': 'SELL',
                        'stop_loss': curr['bb_upper'],
                        'take_profit': curr['close'] - curr['atr'] * 3
                    }
        return None


class RSIDivergence_MACD_Strategy(BaseStrategy):
    """RSI divergence confirmed by MACD"""
    def __init__(self):
        super().__init__("RSI Divergence + MACD")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        return df
    
    def detect_bullish_divergence(self, df):
        """Detect bullish divergence"""
        if len(df) < 20:
            return False
        
        # Find local lows in price and RSI
        prices = df['close'].tail(20)
        rsis = df['rsi'].tail(20)
        
        # Simple divergence check
        price_low = prices.iloc[-10]
        curr_price = prices.iloc[-1]
        rsi_low = rsis.iloc[-10]
        curr_rsi = rsis.iloc[-1]
        
        # Price makes lower low, RSI makes higher low
        if curr_price < price_low and curr_rsi > rsi_low:
            return True
        return False
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        
        # Bullish divergence + MACD confirmation
        if self.detect_bullish_divergence(df):
            if curr['macd_hist'] > 0:
                return {
                    'direction': 'BUY',
                    'stop_loss': df['close'].tail(20).min() - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        
        return None


# Export all
PROFESSIONAL_BATCH3 = [
    HistoricalVolatilityRatio_Strategy,
    VolatilityTargeting_Strategy,
    DayOfWeekEffect_Strategy,
    MonthlySeasonality_Strategy,
    SupportVectorMachine_Strategy,
    NeuralNetworkSignals_Strategy,
    GeneticAlgorithmOptimized_Strategy,
    ADX_BollingerSqueeze_Strategy,
    RSIDivergence_MACD_Strategy,
]
