"""
Proven Strategy Module
======================
Backtested strategies with POSITIVE expectancy.

Based on research findings:
- EMA Cross on USDJPY: 63.3% win, 0.79R expectancy
- EMA Pullback: 0.18R avg across symbols

Author: QuantAI Research
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger("Titan.ProvenStrategy")


@dataclass
class Signal:
    """Trading signal from strategy"""
    symbol: str
    direction: str  # BUY, SELL, HOLD
    strategy: str
    score: float  # 0-100
    entry: float
    stop_loss: float
    take_profit: float
    risk_pips: float
    reasoning: List[str]


class ProvenStrategy:
    """
    Combines backtested winning strategies:
    1. EMA Cross (9/21) with EMA50 filter
    2. EMA Pullback to EMA21 in strong trend
    
    Both strategies have positive expectancy in backtests.
    """
    
    def __init__(self):
        self.name = "ProvenStrategy"
        
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all needed indicators"""
        df = df.copy()
        
        # EMAs
        df['EMA9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['EMA50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['EMA200'] = df['close'].ewm(span=200, adjust=False).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        # ADX (for trend strength)
        df['DM_plus'] = (df['high'].diff()).where(
            (df['high'].diff() > df['low'].diff().abs()) & (df['high'].diff() > 0), 0
        )
        df['DM_minus'] = (df['low'].diff().abs()).where(
            (df['low'].diff().abs() > df['high'].diff()) & (df['low'].diff() < 0), 0
        )
        df['DI_plus'] = 100 * (df['DM_plus'].rolling(14).mean() / df['ATR'])
        df['DI_minus'] = 100 * (df['DM_minus'].rolling(14).mean() / df['ATR'])
        df['ADX'] = (np.abs(df['DI_plus'] - df['DI_minus']) / (df['DI_plus'] + df['DI_minus']) * 100).rolling(14).mean()
        
        return df
    
    def analyze(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """
        Analyze data and return signal if valid setup found.
        
        Args:
            df: OHLCV DataFrame with at least 200 rows
            symbol: Symbol being analyzed
            
        Returns:
            Signal if valid setup, None otherwise
        """
        if len(df) < 200:
            return None
        
        df = self.calculate_indicators(df)
        
        # Try each strategy in order of preference
        signal = self._check_ema_cross(df, symbol)
        if signal:
            return signal
        
        signal = self._check_ema_pullback(df, symbol)
        if signal:
            return signal
        
        return None
    
    def _check_ema_cross(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """
        Strategy 1: EMA 9/21 Crossover
        Best on: USDJPY (63.3% win, 0.79R)
        
        Rules:
        - BUY: EMA9 crosses above EMA21, price above EMA50
        - SELL: EMA9 crosses below EMA21, price below EMA50
        """
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        reasoning = []
        direction = None
        score = 70  # Base score
        
        # Bullish crossover
        if prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']:
            if curr['close'] > curr['EMA50']:
                direction = "BUY"
                reasoning.append("EMA9 crossed above EMA21")
                reasoning.append("Price above EMA50 (trend filter)")
                
                # Score adjustments
                if curr['RSI'] > 50 and curr['RSI'] < 70:
                    score += 10
                    reasoning.append(f"RSI supportive: {curr['RSI']:.1f}")
                if curr['ADX'] > 25:
                    score += 5
                    reasoning.append(f"Strong trend: ADX {curr['ADX']:.1f}")
        
        # Bearish crossover
        elif prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']:
            if curr['close'] < curr['EMA50']:
                direction = "SELL"
                reasoning.append("EMA9 crossed below EMA21")
                reasoning.append("Price below EMA50 (trend filter)")
                
                if curr['RSI'] < 50 and curr['RSI'] > 30:
                    score += 10
                    reasoning.append(f"RSI supportive: {curr['RSI']:.1f}")
                if curr['ADX'] > 25:
                    score += 5
                    reasoning.append(f"Strong trend: ADX {curr['ADX']:.1f}")
        
        if direction is None:
            return None
        
        # Calculate levels
        entry = curr['close']
        atr = curr['ATR']
        
        if direction == "BUY":
            stop_loss = entry - 1.5 * atr
            take_profit = entry + 2.0 * atr  # 1.33 R:R
        else:
            stop_loss = entry + 1.5 * atr
            take_profit = entry - 2.0 * atr
        
        return Signal(
            symbol=symbol,
            direction=direction,
            strategy="EMA_Cross",
            score=score,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_pips=1.5 * atr,
            reasoning=reasoning
        )
    
    def _check_ema_pullback(self, df: pd.DataFrame, symbol: str) -> Optional[Signal]:
        """
        Strategy 2: EMA Pullback in Trend
        Avg 0.18R across symbols
        
        Rules:
        - BUY: Strong uptrend (EMA21>50>200), price pulls back to EMA21, RSI 40-65
        - SELL: Strong downtrend (EMA21<50<200), price pulls back to EMA21, RSI 35-60
        """
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        reasoning = []
        direction = None
        score = 70
        
        # Uptrend pullback
        if curr['EMA21'] > curr['EMA50'] > curr['EMA200']:
            # Price touched EMA21 and bounced
            if prev['low'] <= prev['EMA21'] and curr['close'] > curr['EMA21']:
                if 40 < curr['RSI'] < 65:
                    direction = "BUY"
                    reasoning.append("Strong uptrend (EMA21 > EMA50 > EMA200)")
                    reasoning.append("Pullback to EMA21 completed")
                    reasoning.append(f"RSI in sweet spot: {curr['RSI']:.1f}")
                    
                    if curr['ADX'] > 25:
                        score += 10
                        reasoning.append(f"Strong trend confirmed: ADX {curr['ADX']:.1f}")
        
        # Downtrend pullback
        elif curr['EMA21'] < curr['EMA50'] < curr['EMA200']:
            if prev['high'] >= prev['EMA21'] and curr['close'] < curr['EMA21']:
                if 35 < curr['RSI'] < 60:
                    direction = "SELL"
                    reasoning.append("Strong downtrend (EMA21 < EMA50 < EMA200)")
                    reasoning.append("Pullback to EMA21 completed")
                    reasoning.append(f"RSI in sweet spot: {curr['RSI']:.1f}")
                    
                    if curr['ADX'] > 25:
                        score += 10
                        reasoning.append(f"Strong trend confirmed: ADX {curr['ADX']:.1f}")
        
        if direction is None:
            return None
        
        # Calculate levels
        entry = curr['close']
        atr = curr['ATR']
        
        if direction == "BUY":
            stop_loss = curr['EMA50'] - 0.5 * atr  # Stop below EMA50
            take_profit = entry + 2.0 * atr
        else:
            stop_loss = curr['EMA50'] + 0.5 * atr
            take_profit = entry - 2.0 * atr
        
        return Signal(
            symbol=symbol,
            direction=direction,
            strategy="EMA_Pullback",
            score=score,
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_pips=abs(entry - stop_loss),
            reasoning=reasoning
        )
    
    def analyze_multi_symbol(self, symbols: List[str], get_data_func) -> List[Signal]:
        """
        Analyze multiple symbols and return all valid signals.
        
        Args:
            symbols: List of symbols to analyze
            get_data_func: Function that takes symbol and returns DataFrame
        """
        signals = []
        
        for symbol in symbols:
            try:
                df = get_data_func(symbol)
                if df is not None and len(df) >= 200:
                    signal = self.analyze(df, symbol)
                    if signal:
                        signals.append(signal)
                        logger.info(
                            f"Signal: {symbol} {signal.direction} "
                            f"({signal.strategy}) Score: {signal.score}"
                        )
            except Exception as e:
                logger.debug(f"Error analyzing {symbol}: {e}")
        
        # Sort by score
        signals.sort(key=lambda x: x.score, reverse=True)
        return signals


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    import MetaTrader5 as mt5
    
    logging.basicConfig(level=logging.INFO)
    
    if not mt5.initialize():
        print("MT5 failed")
        exit()
    
    strategy = ProvenStrategy()
    
    def get_data(symbol):
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 300)
        if rates is not None:
            return pd.DataFrame(rates)
        return None
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "GOLD"]
    
    print("Scanning for signals...")
    signals = strategy.analyze_multi_symbol(symbols, get_data)
    
    if signals:
        print(f"\n{len(signals)} signals found:")
        for sig in signals:
            print(f"\n{sig.symbol} {sig.direction} ({sig.strategy})")
            print(f"  Score: {sig.score}")
            print(f"  Entry: {sig.entry:.5f}")
            print(f"  SL: {sig.stop_loss:.5f}")
            print(f"  TP: {sig.take_profit:.5f}")
            print(f"  Reasoning:")
            for r in sig.reasoning:
                print(f"    - {r}")
    else:
        print("No signals found")
    
    mt5.shutdown()
