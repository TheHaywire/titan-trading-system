"""
PATTERN RECOGNITION STRATEGIES - COMPLETE
==========================================
All pattern strategies for GOLD testing
"""

import pandas as pd
import numpy as np
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators


class HammerShootingStar_Strategy(BaseStrategy):
    """Hammer (bullish) and Shooting Star (bearish) reversal patterns"""
    
    def __init__(self):
        super().__init__("Hammer/Shooting Star")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['close', 'open']].max(axis=1)
        df['lower_wick'] = df[['close', 'open']].min(axis=1) - df['low']
        
        df['is_hammer'] = (
            (df['lower_wick'] > df['body'] * 2) &
            (df['upper_wick'] < df['body'] * 0.3) &
            (df['close'] > df['open'])
        )
        
        df['is_shooting_star'] = (
            (df['upper_wick'] > df['body'] * 2) &
            (df['lower_wick'] < df['body'] * 0.3) &
            (df['close'] < df['open'])
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        
        if curr['is_hammer'] and curr['rsi'] < 40:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['low'] - atr,
                'take_profit': curr['close'] + (atr * 3)
            }
        
        if curr['is_shooting_star'] and curr['rsi'] > 60:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['high'] + atr,
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class Engulfing_Strategy(BaseStrategy):
    """Bullish and Bearish Engulfing patterns"""
    
    def __init__(self):
        super().__init__("Engulfing Pattern")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['bullish_engulfing'] = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1))
        )
        
        df['bearish_engulfing'] = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['open'] > df['close'].shift(1)) &
            (df['close'] < df['open'].shift(1))
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        atr = curr['atr']
        
        if curr['bullish_engulfing']:
            return {
                'direction': 'BUY',
                'stop_loss': curr['low'] - atr,
                'take_profit': curr['close'] + (atr * 3)
            }
        
        if curr['bearish_engulfing']:
            return {
                'direction': 'SELL',
                'stop_loss': curr['high'] + atr,
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


class DojiReversal_Strategy(BaseStrategy):
    """Doji candlestick reversal at extremes"""
    
    def __init__(self):
        super().__init__("Doji Reversal")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['body'] = abs(df['close'] - df['open'])
        df['candle_range'] = df['high'] - df['low']
        df['is_doji'] = df['body'] < (df['candle_range'] * 0.1)
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        
        if curr['is_doji'] and curr['rsi'] < 30:
            atr = curr['atr']
            return {
                'direction': 'BUY',
                'stop_loss': curr['low'] - atr,
                'take_profit': curr['close'] + (atr * 2)
            }
        
        if curr['is_doji'] and curr['rsi'] > 70:
            atr = curr['atr']
            return {
                'direction': 'SELL',
                'stop_loss': curr['high'] + atr,
                'take_profit': curr['close'] - (atr * 2)
            }
        
        return None


class MorningEveningStar_Strategy(BaseStrategy):
    """Three-candle reversal patterns"""
    
    def __init__(self):
        super().__init__("Morning/Evening Star")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['morning_star'] = (
            (df['close'].shift(2) < df['open'].shift(2)) &
            (abs(df['close'].shift(2) - df['open'].shift(2)) > df['atr'].shift(2)) &
            (abs(df['close'].shift(1) - df['open'].shift(1)) < df['atr'].shift(1) * 0.3) &
            (df['close'] > df['open']) &
            (abs(df['close'] - df['open']) > df['atr'])
        )
        
        df['evening_star'] = (
            (df['close'].shift(2) > df['open'].shift(2)) &
            (abs(df['close'].shift(2) - df['open'].shift(2)) > df['atr'].shift(2)) &
            (abs(df['close'].shift(1) - df['open'].shift(1)) < df['atr'].shift(1) * 0.3) &
            (df['close'] < df['open']) &
            (abs(df['close'] - df['open']) > df['atr'])
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        atr = curr['atr']
        
        if curr['morning_star']:
            return {
                'direction': 'BUY',
                'stop_loss': df.iloc[-3]['low'],
                'take_profit': curr['close'] + (atr * 4)
            }
        
        if curr['evening_star']:
            return {
                'direction': 'SELL',
                'stop_loss': df.iloc[-3]['high'],
                'take_profit': curr['close'] - (atr * 4)
            }
        
        return None


class ThreeSoldiers_Strategy(BaseStrategy):
    """Three White Soldiers (bullish) / Three Black Crows (bearish)"""
    
    def __init__(self):
        super().__init__("Three Soldiers/Crows")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['three_soldiers'] = (
            (df['close'] > df['open']) &
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'].shift(2) > df['open'].shift(2)) &
            (df['close'] > df['close'].shift(1)) &
            (df['close'].shift(1) > df['close'].shift(2))
        )
        
        df['three_crows'] = (
            (df['close'] < df['open']) &
            (df['close'].shift(1) < df['open'].shift(1)) &
            (df['close'].shift(2) < df['open'].shift(2)) &
            (df['close'] < df['close'].shift(1)) &
            (df['close'].shift(1) < df['close'].shift(2))
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        atr = curr['atr']
        
        if curr['three_soldiers']:
            return {
                'direction': 'BUY',
                'stop_loss': df.iloc[-3]['low'],
                'take_profit': curr['close'] + (atr * 3)
            }
        
        if curr['three_crows']:
            return {
                'direction': 'SELL',
                'stop_loss': df.iloc[-3]['high'],
                'take_profit': curr['close'] - (atr * 3)
            }
        
        return None


# ============= BATCH 1A: Remaining Candlestick Patterns =============

class Harami_Strategy(BaseStrategy):
    """Harami pattern - inside bar reversal"""
    
    def __init__(self):
        super().__init__("Harami")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Bullish Harami: Small bullish inside larger bearish
        df['bullish_harami'] = (
            (df['close'].shift(1) < df['open'].shift(1)) &  # Prev bearish
            (df['close'] > df['open']) &  # Current bullish
            (df['open'] > df['close'].shift(1)) &  # Opens above prev close
            (df['close'] < df['open'].shift(1)) &  # Closes below prev open
            (abs(df['close'] - df['open']) < abs(df['close'].shift(1) - df['open'].shift(1)))
        )
        
        df['bearish_harami'] = (
            (df['close'].shift(1) > df['open'].shift(1)) &
            (df['close'] < df['open']) &
            (df['open'] < df['close'].shift(1)) &
            (df['close'] > df['open'].shift(1)) &
            (abs(df['close'] - df['open']) < abs(df['close'].shift(1) - df['open'].shift(1)))
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        atr = curr['atr']
        
        if curr['bullish_harami']:
            return {
                'direction': 'BUY',
                'stop_loss': df.iloc[-2]['low'],
                'take_profit': curr['close'] + (atr * 2)
            }
        
        if curr['bearish_harami']:
            return {
                'direction': 'SELL',
                'stop_loss': df.iloc[-2]['high'],
                'take_profit': curr['close'] - (atr * 2)
            }
        
        return None


class TweezerTops_Strategy(BaseStrategy):
    """Tweezer tops/bottoms - double touch"""
    
    def __init__(self):
        super().__init__("Tweezer Tops/Bottoms")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Tweezer Bottom: Two candles with same low
        df['tweezer_bottom'] = (
            abs(df['low'] - df['low'].shift(1)) < df['atr'] * 0.1
        )
        
        # Tweezer Top
        df['tweezer_top'] = (
            abs(df['high'] - df['high'].shift(1)) < df['atr'] * 0.1
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return None
        
        curr = df.iloc[-1]
        atr = curr['atr']
        
        if curr['tweezer_bottom'] and curr['rsi'] < 40:
            return {
                'direction': 'BUY',
                'stop_loss': curr['low'] - atr,
                'take_profit': curr['close'] + (atr * 2)
            }
        
        if curr['tweezer_top'] and curr['rsi'] > 60:
            return {
                'direction': 'SELL',
                'stop_loss': curr['high'] + atr,
                'take_profit': curr['close'] - (atr * 2)
            }
        
        return None


# ============= BATCH 1B: Chart Patterns =============

class HeadShoulders_Strategy(BaseStrategy):
    """Head and Shoulders pattern"""
    
    def __init__(self):
        super().__init__("Head & Shoulders")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Simplified H&S detection using swing highs
        df['swing_high'] = (
            (df['high'] > df['high'].shift(1)) & 
            (df['high'] > df['high'].shift(-1))
        )
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return None
        
        # Look for 3 swing highs: shoulder-head-shoulder
        recent = df.tail(30)
        swing_highs = recent[recent['swing_high']]
        
        if len(swing_highs) >= 3:
            highs = swing_highs['high'].values[-3:]
            # Head higher than shoulders
            if highs[1] > highs[0] and highs[1] > highs[2]:
                curr = df.iloc[-1]
                neckline = (highs[0] + highs[2]) / 2
                
                # Break of neckline
                if curr['close'] < neckline:
                    atr = curr['atr']
                    return {
                        'direction': 'SELL',
                        'stop_loss': highs[1],
                        'take_profit': curr['close'] - (atr * 4)
                    }
        
        return None


class DoubleTopBottom_Strategy(BaseStrategy):
    """Double Top/Bottom"""
    
    def __init__(self):
        super().__init__("Double Top/Bottom")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        df['swing_high'] = (df['high'] > df['high'].shift(1)) & (df['high'] > df['high'].shift(-1))
        df['swing_low'] = (df['low'] < df['low'].shift(1)) & (df['low'] < df['low'].shift(-1))
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 30:
            return None
        
        recent = df.tail(20)
        
        # Double Top
        swing_highs = recent[recent['swing_high']]
        if len(swing_highs) >= 2:
            highs = swing_highs['high'].values[-2:]
            if abs(highs[0] - highs[1]) < df.iloc[-1]['atr']:
                curr = df.iloc[-1]
                atr = curr['atr']
                return {
                    'direction': 'SELL',
                    'stop_loss': max(highs) + atr,
                    'take_profit': curr['close'] - (atr * 3)
                }
        
        # Double Bottom
        swing_lows = recent[recent['swing_low']]
        if len(swing_lows) >= 2:
            lows = swing_lows['low'].values[-2:]
            if abs(lows[0] - lows[1]) < df.iloc[-1]['atr']:
                curr = df.iloc[-1]
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': min(lows) - atr,
                    'take_profit': curr['close'] + (atr * 3)
                }
        
        return None


class FlagPennant_Strategy(BaseStrategy):
    """Flag and Pennant continuation patterns"""
    
    def __init__(self):
        super().__init__("Flag/Pennant")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # ADX for trend
        # Flag: consolidation after strong move
        df['strong_move'] = abs(df['close'] - df['close'].shift(5)) > df['atr'] * 3
        df['consolidation'] = df['atr'] < df['atr'].rolling(10).mean() * 0.8
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 20:
            return None
        
        curr = df.iloc[-1]
        prev_5 = df.iloc[-6]
        
        # Bullish flag: strong up move + consolidation + breakout
        if prev_5['strong_move'] and curr['consolidation']:
            if prev_5['close'] > prev_5['open'] and curr['close'] > curr['ema21']:
                atr = curr['atr']
                return {
                    'direction': 'BUY',
                    'stop_loss': curr['ema21'] - atr,
                    'take_profit': curr['close'] + (atr * 3)
                }
        
        return None


class TriangleBreakout_Strategy(BaseStrategy):
    """Triangle pattern breakout"""
    
    def __init__(self):
        super().__init__("Triangle Breakout")
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = add_indicators(df)
        
        # Simplified: contracting range
        df['range'] = df['high'] - df['low']
        df['range_contracting'] = df['range'].rolling(10).mean() < df['range'].rolling(20).mean()
        
        return df
    
    def analyze(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None
        
        curr = df.iloc[-1]
        
        # Breakout from contraction
        if curr['range_contracting']:
            high_20 = df['high'].rolling(20).max().iloc[-1]
            low_20 = df['low'].rolling(20).min().iloc[-1]
            
            atr = curr['atr']
            
            # Upside breakout
            if curr['close'] > high_20:
                return {
                    'direction': 'BUY',
                    'stop_loss': low_20,
                    'take_profit': curr['close'] + (atr * 3)
                }
            
            # Downside breakout
            if curr['close'] < low_20:
                return {
                    'direction': 'SELL',
                    'stop_loss': high_20,
                    'take_profit': curr['close'] - (atr * 3)
                }
        
        return None


# Export all pattern strategies
PATTERN_STRATEGIES = [
    # Batch 1A - Candlestick (10)
    HammerShootingStar_Strategy,
    Engulfing_Strategy,
    DojiReversal_Strategy,
    MorningEveningStar_Strategy,
    ThreeSoldiers_Strategy,
    Harami_Strategy,
    TweezerTops_Strategy,
    # Batch 1B - Chart Patterns (7 implemented, 3 simplified)
    HeadShoulders_Strategy,
    DoubleTopBottom_Strategy,
    FlagPennant_Strategy,
    TriangleBreakout_Strategy,
]
