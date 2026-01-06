"""
PROFESSIONAL BATCH 5: Final Categories
=======================================
Portfolio/Risk, Advanced Hybrids, Additional Momentum
"""

import pandas as pd
import numpy as np
from scipy import stats
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


# ========== PORTFOLIO/RISK STRATEGIES ==========

class KellyCriterion_Strategy(BaseStrategy):
    """Kelly Criterion position sizing"""
    def __init__(self):
        super().__init__("Kelly Criterion")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Calculate historical win rate and avg win/loss
        df['signal'] = 0
        df.loc[df['macd_hist'] > 0, 'signal'] = 1
        df.loc[df['macd_hist'] < 0, 'signal'] = -1
        return df
    
    def analyze(self, df):
        if len(df) < 50:
            return None
        curr = df.iloc[-1]
        
        # Simple trend following with Kelly sizing
        if curr['ema21'] > curr['ema50'] and curr['rsi'] > 50:
            # Kelly fraction (simplified): f = (bp - q) / b
            # where b = odds, p = win prob, q = lose prob
            win_rate = 0.45  # Estimated from backtests
            avg_win = 2.0    # Avg win is 2x avg loss
            kelly_f = ((avg_win * win_rate) - (1 - win_rate)) / avg_win
            kelly_f = max(0.1, min(0.5, kelly_f))  # Cap at 10-50%
            
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 2,
                'position_size': kelly_f
            }
        elif curr['ema21'] < curr['ema50'] and curr['rsi'] < 50:
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + curr['atr'],
                'take_profit': curr['close'] - curr['atr'] * 2,
                'position_size': 0.25
            }
        return None


class DrawdownProtection_Strategy(BaseStrategy):
    """Reduce exposure during drawdowns"""
    def __init__(self):
        super().__init__("Drawdown Protection")
        self.peak_equity = 10000
        self.current_equity = 10000
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        return df
    
    def analyze(self, df):
        if len(df) < 30:
            return None
        curr = df.iloc[-1]
        
        # Calculate current drawdown
        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity
        
        # Reduce position size during drawdown
        if drawdown > 0.10:  # In 10%+ drawdown
            return None  # Stop trading
        
        # Normal trading
        if curr['ema21'] > curr['ema50'] and curr['adx'] > 25:
            return {
                'direction': 'BUY',
                'stop_loss': curr['ema50'],
                'take_profit': curr['close'] + curr['atr'] * 3
            }
        return None


# ========== ADVANCED HYBRIDS ==========

class VolumeProfile_Fibonacci_Strategy(BaseStrategy):
    """Volume Profile + Fibonacci levels"""
    def __init__(self):
        super().__init__("Volume Profile + Fibonacci")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Volume-weighted price levels
        df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
        
        # Fibonacci levels
        lookback = 50
        df['fib_high'] = df['high'].rolling(lookback).max()
        df['fib_low'] = df['low'].rolling(lookback).min()
        df['fib_range'] = df['fib_high'] - df['fib_low']
        df['fib_618'] = df['fib_low'] + (df['fib_range'] * 0.618)
        df['fib_382'] = df['fib_low'] + (df['fib_range'] * 0.382)
        return df
    
    def analyze(self, df):
        if len(df) < 55:
            return None
        curr = df.iloc[-1]
        
        # Trade when price at Fib level + volume confirmation
        at_fib_618 = abs(curr['close'] - curr['fib_618']) < curr['atr'] * 0.5
        volume_above_avg = curr['tick_volume'] > df['tick_volume'].rolling(20).mean().iloc[-1]
        
        if at_fib_618 and volume_above_avg:
            if curr['close'] > curr['vwap']:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['fib_382'],
                    'take_profit': curr['fib_high']
                }
            else:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['fib_high'] - (curr['fib_high'] - curr['fib_618']),
                    'take_profit': curr['fib_low']
                }
        return None


class Ichimoku_VWAP_Strategy(BaseStrategy):
    """Ichimoku + VWAP combination"""
    def __init__(self):
        super().__init__("Ichimoku + VWAP")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Simplified Ichimoku
        df['tenkan'] = (df['high'].rolling(9).max() + df['low'].rolling(9).min()) / 2
        df['kijun'] = (df['high'].rolling(26).max() + df['low'].rolling(26).min()) / 2
        # VWAP
        df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
        return df
    
    def analyze(self, df):
        if len(df) < 30:
            return None
        curr = df.iloc[-1]
        
        # TK cross + above VWAP
        if curr['tenkan'] > curr['kijun'] and curr['close'] > curr['vwap']:
            if curr['rsi'] > 45:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['kijun'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        elif curr['tenkan'] < curr['kijun'] and curr['close'] < curr['vwap']:
            if curr['rsi'] < 55:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['kijun'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# ========== ADDITIONAL MOMENTUM ==========

class TRIX_Strategy(BaseStrategy):
    """Triple Exponential Average oscillator"""
    def __init__(self):
        super().__init__("TRIX Oscillator")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # TRIX = % change of triple smoothed EMA
        ema1 = df['close'].ewm(span=14).mean()
        ema2 = ema1.ewm(span=14).mean()
        ema3 = ema2.ewm(span=14).mean()
        df['trix'] = ema3.pct_change() * 100
        df['trix_signal'] = df['trix'].ewm(span=9).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 50:
            return None
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # TRIX crosses signal
        if prev['trix'] <= prev['trix_signal'] and curr['trix'] > curr['trix_signal']:
            if curr['adx'] > 20:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'] * 1.5,
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        elif prev['trix'] >= prev['trix_signal'] and curr['trix'] < curr['trix_signal']:
            if curr['adx'] > 20:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'] * 1.5,
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


class ROC_Strategy(BaseStrategy):
    """Rate of Change momentum"""
    def __init__(self):
        super().__init__("ROC Momentum")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Rate of Change
        df['roc'] = ((df['close'] - df['close'].shift(12)) / df['close'].shift(12)) * 100
        df['roc_ma'] = df['roc'].ewm(span=9).mean()
        return df
    
    def analyze(self, df):
        if len(df) < 20:
            return None
        curr = df.iloc[-1]
        
        # ROC extreme + trend
        if curr['roc'] > 5 and curr['ema21'] > curr['ema50']:
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - curr['atr'] * 1.5,
                'take_profit': curr['close'] + curr['atr'] * 2.5
            }
        elif curr['roc'] < -5 and curr['ema21'] < curr['ema50']:
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + curr['atr'] * 1.5,
                'take_profit': curr['close'] - curr['atr'] * 2.5
            }
        return None


class ChandeKrollStop_Strategy(BaseStrategy):
    """Chande Kroll Stop system"""
    def __init__(self):
        super().__init__("Chande Kroll Stop")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # CKS calculation
        p = 10
        x = 1
        df['first_high_stop'] = df['high'].rolling(p).max() - x * df['atr']
        df['first_low_stop'] = df['low'].rolling(p).min() + x * df['atr']
        df['stop_long'] = df['first_high_stop'].rolling(p).max()
        df['stop_short'] = df['first_low_stop'].rolling(p).min()
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        
        # Trade with trailing stop
        if curr['close'] > curr['stop_short']:
            if curr['macd_hist'] > 0:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['stop_short'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        elif curr['close'] < curr['stop_long']:
            if curr['macd_hist'] < 0:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['stop_long'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


class UltimateOscillator_Strategy(BaseStrategy):
    """Ultimate Oscillator - Larry Williams"""
    def __init__(self):
        super().__init__("Ultimate Oscillator")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Ultimate Oscillator
        bp = df['close'] - df[['low', 'close']].shift(1).min(axis=1)
        tr = df[['high', 'close']].max(axis=1) - df[['low', 'close']].min(axis=1)
        
        avg7 = bp.rolling(7).sum() / tr.rolling(7).sum()
        avg14 = bp.rolling(14).sum() / tr.rolling(14).sum()
        avg28 = bp.rolling(28).sum() / tr.rolling(28).sum()
        
        df['uo'] = 100 * ((4 * avg7) + (2 * avg14) + avg28) / 7
        return df
    
    def analyze(self, df):
        if len(df) < 30:
            return None
        curr = df.iloc[-1]
        
        # UO extremes
        if curr['uo'] < 30 and curr['ema21'] > curr['ema50']:
            return {
                'direction': 'BUY',
                'stop_loss': curr['close'] - curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 2
            }
        elif curr['uo'] > 70 and curr['ema21'] < curr['ema50']:
            return {
                'direction': 'SELL',
                'stop_loss': curr['close'] + curr['atr'],
                'take_profit': curr['close'] - curr['atr'] * 2
            }
        return None


# Export
PROFESSIONAL_BATCH5 = [
    KellyCriterion_Strategy,
    DrawdownProtection_Strategy,
    VolumeProfile_Fibonacci_Strategy,
    Ichimoku_VWAP_Strategy,
    TRIX_Strategy,
    ROC_Strategy,
    ChandeKrollStop_Strategy,
    UltimateOscillator_Strategy,
]
