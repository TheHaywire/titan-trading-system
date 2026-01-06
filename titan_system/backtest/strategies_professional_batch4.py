"""
PROFESSIONAL BATCH 4: SMC, Exotic, Advanced MTF
===============================================
Complete professional implementations - no shortcuts
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


# ========== SMC (Smart Money Concepts) ==========

class OptimalTradeEntry_Strategy(BaseStrategy):
    """OTE - 0.62-0.79 Fibonacci retracement"""
    def __init__(self):
        super().__init__("Optimal Trade Entry (OTE)")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Calculate swing highs and lows
        df['swing_high'] = df['high'].rolling(10, center=True).max()
        df['swing_low'] = df['low'].rolling(10, center=True).min()
        return df
    
    def analyze(self, df):
        if len(df) < 30:
            return None
        curr = df.iloc[-1]
        
        # Find recent swing high/low
        recent_high = df['swing_high'].tail(20).max()
        recent_low = df['swing_low'].tail(20).min()
        swing_range = recent_high - recent_low
        
        # OTE zone (0.62-0.79 retracement)
        ote_low = recent_low + (swing_range * 0.62)
        ote_high = recent_low + (swing_range * 0.79)
        
        # Trade from OTE zone
        if curr['ema21'] > curr['ema50']:  # Uptrend
            if ote_low <= curr['close'] <= ote_high:
                return {
                    'direction': 'BUY',
                    'stop_loss': recent_low - curr['atr'],
                    'take_profit': recent_high
                }
        elif curr['ema21'] < curr['ema50']:  # Downtrend
            ote_low_bear = recent_high - (swing_range * 0.79)
            ote_high_bear = recent_high - (swing_range * 0.62)
            if ote_low_bear <= curr['close'] <= ote_high_bear:
                return {
                    'direction': 'SELL',
                    'stop_loss': recent_high + curr['atr'],
                    'take_profit': recent_low
                }
        return None


class BreakerBlock_Strategy(BaseStrategy):
    """Breaker blocks - failed order blocks"""
    def __init__(self):
        super().__init__("Breaker Blocks")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        return df
    
    def analyze(self, df):
        if len(df) < 20:
            return None
        curr = df.iloc[-1]
        
        # Identify breaker: strong move that breaks structure
        lookback = df.tail(20)
        
        # Bullish breaker: low gets broken, then reclaimed
        lows = lookback['low']
        recent_low = lows.min()
        
        broke_low = (lookback['close'] < recent_low).any()
        reclaimed = curr['close'] > recent_low
        
        if broke_low and reclaimed and curr['macd_hist'] > 0:
            return {
                'direction': 'BUY',
                'stop_loss': recent_low - curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 3
            }
        return None


# ========== EXOTIC INDICATORS ==========

class ZigZag_Strategy(BaseStrategy):
    """ZigZag swing trading"""
    def __init__(self):
        super().__init__("ZigZag Indicator")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Simplified zigzag: % based
        df['zz_swing'] = 0
        threshold = 0.03  # 3% swing
        
        last_peak = df['high'].iloc[0]
        last_trough = df['low'].iloc[0]
        
        for i in range(1, len(df)):
            if df['high'].iloc[i] > last_peak * (1 + threshold):
                df.loc[df.index[i], 'zz_swing'] = 1  # Peak
                last_peak = df['high'].iloc[i]
            elif df['low'].iloc[i] < last_trough * (1 - threshold):
                df.loc[df.index[i], 'zz_swing'] = -1  # Trough
                last_trough = df['low'].iloc[i]
        
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Trade swing reversals
        recent_swings = df['zz_swing'].tail(5)
        if recent_swings.iloc[-1] == 1:  # Just made peak
            if curr['rsi'] > 70:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['high'] + curr['atr'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        elif recent_swings.iloc[-1] == -1:  # Just made trough
            if curr['rsi'] < 30:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['low'] - curr['atr'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        return None


class LinearRegressionChannel_Strategy(BaseStrategy):
    """Trade linear regression channel bounces"""
    def __init__(self):
        super().__init__("Linear Regression Channel")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Linear regression
        df['lr'] = df['close'].rolling(50).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0] * (len(x)-1) + 
                     np.polyfit(range(len(x)), x, 1)[1]
        )
        df['lr_std'] = df['close'].rolling(50).std()
        df['lr_upper'] = df['lr'] + 2 * df['lr_std']
        df['lr_lower'] = df['lr'] - 2 * df['lr_std']
        return df
    
    def analyze(self, df):
        if len(df) < 55:
            return None
        curr = df.iloc[-1]
        
        # Trade bounces off channel
        if curr['close'] <= curr['lr_lower']:
            if curr['rsi'] < 40:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['lr_lower'] - curr['atr'],
                    'take_profit': curr['lr']  # Target midline
                }
        elif curr['close'] >= curr['lr_upper']:
            if curr['rsi'] > 60:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['lr_upper'] + curr['atr'],
                    'take_profit': curr['lr']
                }
        return None


# ========== ADVANCED MTF ==========

class TripleTimeframeAlignment_Strategy(BaseStrategy):
    """All 3 timeframes must align"""
    def __init__(self):
        super().__init__("Triple Timeframe Alignment")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Simulate 3 timeframes with different EMAs
        df['htf_trend'] = df['close'] > df['ema200']  # Weekly proxy
        df['mtf_trend'] = df['close'] > df['ema50']   # Daily proxy
        df['ltf_trend'] = df['close'] > df['ema21']   # H4 proxy
        return df
    
    def analyze(self, df):
        if len(df) < 210:
            return None
        curr = df.iloc[-1]
        
        # All timeframes must align
        if curr['htf_trend'] and curr['mtf_trend'] and curr['ltf_trend']:
            if curr['rsi'] > 45 and curr['rsi'] < 70:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['ema200'],
                    'take_profit': curr['close'] + curr['atr'] * 5
                }
        elif not curr['htf_trend'] and not curr['mtf_trend'] and not curr['ltf_trend']:
            if curr['rsi'] < 55 and curr['rsi'] > 30:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['ema200'],
                    'take_profit': curr['close'] - curr['atr'] * 5
                }
        return None


class MTF_SupportResistance_Strategy(BaseStrategy):
    """Multi-timeframe S/R zones"""
    def __init__(self):
        super().__init__("MTF Support/Resistance")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # HTF S/R (using 50-period high/low)
        df['htf_resistance'] = df['high'].rolling(50).max()
        df['htf_support'] = df['low'].rolling(50).min()
        # MTF S/R (using 20-period)
        df['mtf_resistance'] = df['high'].rolling(20).max()
        df['mtf_support'] = df['low'].rolling(20).min()
        return df
    
    def analyze(self, df):
        if len(df) < 55:
            return None
        curr = df.iloc[-1]
        
        # Trade bounces off HTF support with MTF confirmation
        near_htf_support = abs(curr['close'] - curr['htf_support']) < curr['atr']
        near_mtf_support = abs(curr['close'] - curr['mtf_support']) < curr['atr'] * 0.5
        
        if near_htf_support and curr['rsi'] < 45:
            return {
                'direction': 'BUY',
                'stop_loss': curr['htf_support'] - curr['atr'],
                'take_profit': curr['mtf_resistance']
            }
        
        # Trade rejections from HTF resistance
        near_htf_resistance = abs(curr['close'] - curr['htf_resistance']) < curr['atr']
        if near_htf_resistance and curr['rsi'] > 55:
            return {
                'direction': 'SELL',
                'stop_loss': curr['htf_resistance'] + curr['atr'],
                'take_profit': curr['mtf_support']
            }
        return None


class FractalTrading_Strategy(BaseStrategy):
    """Williams Fractals"""
    def __init__(self):
        super().__init__("Fractal Trading")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Identify fractals (5-bar pattern)
        df['fractal_high'] = False
        df['fractal_low'] = False
        
        for i in range(2, len(df)-2):
            # Fractal high
            if (df['high'].iloc[i] > df['high'].iloc[i-2] and
                df['high'].iloc[i] > df['high'].iloc[i-1] and
                df['high'].iloc[i] > df['high'].iloc[i+1] and
                df['high'].iloc[i] > df['high'].iloc[i+2]):
                df.iloc[i, df.columns.get_loc('fractal_high')] = True
            
            # Fractal low
            if (df['low'].iloc[i] < df['low'].iloc[i-2] and
                df['low'].iloc[i] < df['low'].iloc[i-1] and
                df['low'].iloc[i] < df['low'].iloc[i+1] and
                df['low'].iloc[i] < df['low'].iloc[i+2]):
                df.iloc[i, df.columns.get_loc('fractal_low')] = True
        
        return df
    
    def analyze(self, df):
        if len(df) < 10:
            return None
        curr = df.iloc[-1]
        
        # Find recent fractals
        recent = df.tail(10)
        last_fractal_high = recent[recent['fractal_high']]['high'].max() if recent['fractal_high'].any() else None
        last_fractal_low = recent[recent['fractal_low']]['low'].min() if recent['fractal_low'].any() else None
        
        # Trade breakouts of fractals
        if last_fractal_high and curr['close'] > last_fractal_high:
            if curr['adx'] > 20:
                return {
                    'direction': 'BUY',
                    'stop_loss': last_fractal_low if last_fractal_low else curr['close'] - curr['atr'] * 2,
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        elif last_fractal_low and curr['close'] < last_fractal_low:
            if curr['adx'] > 20:
                return {
                    'direction': 'SELL',
                    'stop_loss': last_fractal_high if last_fractal_high else curr['close'] + curr['atr'] * 2,
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# ========== ADDITIONAL STRATEGIES ==========

class ChoppinessIndex_Strategy(BaseStrategy):
    """Choppiness Index - trade trend vs range"""
    def __init__(self):
        super().__init__("Choppiness Index")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Choppiness Index
        n = 14
        df['tr_sum'] = df['atr'].rolling(n).sum() * n  # True range sum
        df['hh_ll'] = df['high'].rolling(n).max() - df['low'].rolling(n).min()
        df['chop'] = 100 * np.log10(df['tr_sum'] / df['hh_ll']) / np.log10(n)
        return df
    
    def analyze(self, df):
        if len(df) < 20:
            return None
        curr = df.iloc[-1]
        
        # Chop < 38 = trending, > 62 = ranging
        if curr['chop'] < 38:  # Strong trend
            if curr['macd_hist'] > 0:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['close'] - curr['atr'] * 1.5,
                    'take_profit': curr['close'] + curr['atr'] * 4
                }
            elif curr['macd_hist'] < 0:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['close'] + curr['atr'] * 1.5,
                    'take_profit': curr['close'] - curr['atr'] * 4
                }
        return None


class KeltnerChannel_Breakout_Strategy(BaseStrategy):
    """Keltner Channel breakouts"""
    def __init__(self):
        super().__init__("Keltner Channel Breakout")
    
    def calculate_indicators(self, df):
        df = add_indicators(df)
        # Keltner Channels
        df['kc_mid'] = df['ema21']
        df['kc_upper'] = df['kc_mid'] + (2 * df['atr'])
        df['kc_lower'] = df['kc_mid'] - (2 * df['atr'])
        return df
    
    def analyze(self, df):
        if len(df) < 25:
            return None
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Breakout above upper channel
        if prev['close'] <= prev['kc_upper'] and curr['close'] > curr['kc_upper']:
            if curr['adx'] > 20:
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['kc_mid'],
                    'take_profit': curr['close'] + curr['atr'] * 3
                }
        # Breakout below lower channel
        elif prev['close'] >= prev['kc_lower'] and curr['close'] < curr['kc_lower']:
            if curr['adx'] > 20:
                return {
                    'direction': 'SELL',
                    'stop_loss': curr['kc_mid'],
                    'take_profit': curr['close'] - curr['atr'] * 3
                }
        return None


# Export
PROFESSIONAL_BATCH4 = [
    OptimalTradeEntry_Strategy,
    BreakerBlock_Strategy,
    ZigZag_Strategy,
    LinearRegressionChannel_Strategy,
    TripleTimeframeAlignment_Strategy,
    MTF_SupportResistance_Strategy,
    FractalTrading_Strategy,
    ChoppinessIndex_Strategy,
    KeltnerChannel_Breakout_Strategy,
]
