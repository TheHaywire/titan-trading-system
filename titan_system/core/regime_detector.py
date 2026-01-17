"""
Regime Detection Module
======================
Determines the current market state (Trend vs Range) using 
statistical indicators and price action.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from typing import Dict, Optional, List
from datetime import datetime

class RegimeDetector:
    """Detects market regimes (Trending, Ranging, Volatile, Neutral)."""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        
    def get_market_data(self, timeframe=mt5.TIMEFRAME_H1, count=100, symbol: str = None) -> Optional[pd.DataFrame]:
        """Fetch historical data from MT5."""
        if not mt5.initialize():
            return None
            
        target_symbol = symbol if symbol else self.symbol
        
        # Ensure symbol is visible
        mt5.symbol_select(target_symbol, True)
        
        rates = mt5.copy_rates_from_pos(target_symbol, timeframe, 0, count)
        if rates is None or len(rates) == 0:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for regime detection."""
        # Simple Moving Averages
        df['sma20'] = df['close'].rolling(window=20).mean()
        df['sma50'] = df['close'].rolling(window=50).mean()
        
        # Relative Strength Index (RSI)
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Average True Range (ATR) for Volatility
        df['tr'] = np.maximum(df['high'] - df['low'], 
                    np.maximum(abs(df['high'] - df['close'].shift(1)), 
                    abs(df['low'] - df['close'].shift(1))))
        df['atr'] = df['tr'].rolling(window=14).mean()
        
        # ADX (Directional Movement Index) - Simplified Calculation
        # True Range, Directional Movement
        df['up_move'] = df['high'] - df['high'].shift(1)
        df['down_move'] = df['low'].shift(1) - df['low']
        
        df['plus_dm'] = np.where((df['up_move'] > df['down_move']) & (df['up_move'] > 0), df['up_move'], 0)
        df['minus_dm'] = np.where((df['down_move'] > df['up_move']) & (df['down_move'] > 0), df['down_move'], 0)
        
        # Smoothing
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=14).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=14).mean() / df['atr'])
        
        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=14).mean()
        
        # Bollinger Bands for Compression
        df['std'] = df['close'].rolling(window=20).std()
        df['bb_upper'] = df['sma20'] + (df['std'] * 2)
        df['bb_lower'] = df['sma20'] - (df['std'] * 2)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['sma20']
        
        return df

    def detect_regime(self) -> Dict:
        """Analyze indicators to determine the current regime."""
        df = self.get_market_data()
        if df is None or len(df) < 50:
            return {
                "symbol": self.symbol, 
                "regime": "UNKNOWN", 
                "confidence": 0,
                "volatility": {"status": "UNKNOWN", "z_score": 0, "bb_width": 0},
                "institutional": {"alpha_efficiency": 0, "edge_ratio": 0},
                "metrics": {"adx": 0, "rsi": 0, "price_vs_sma20": 0}
            }

        indicators = self.calculate_indicators(df)
        last = indicators.iloc[-1]
        prev = indicators.iloc[-2]
        
        # Indicator Extraction
        adx = last['adx']
        rsi = last['rsi']
        price = last['close']
        sma20 = last['sma20']
        bb_width = last['bb_width']
        
        # --- AI IMPROVEMENTS (VALIDATED) ---
        # 1. Volatility Gate (ATR)
        avg_atr = indicators['atr'].rolling(window=20).mean().iloc[-1]
        vol_gate = last['atr'] > (avg_atr * 0.9)
        
        # 2. 2-Bar Confirmation (Whipsaw avoidance)
        regime_now = "BULLISH" if price > sma20 else "BEARISH"
        regime_prev = "BULLISH" if prev['close'] > prev['sma20'] else "BEARISH"
        confirmed = (regime_now == regime_prev)
        
        # Regime Identification Logic
        regime = "NEUTRAL"
        confidence = 0.5
        
        if adx > 25 and confirmed and vol_gate:
            regime = f"TRENDING_{regime_now}"
            confidence = min(0.9, (adx / 50) + 0.2)
        elif adx < 20:
            if 40 < rsi < 60:
                regime = "RANGING_CALM"
                confidence = 0.8
            elif rsi > 70 or rsi < 30:
                regime = "RANGING_EXTREME"
                confidence = 0.7
            else:
                regime = "RANGING"
                confidence = 0.6
                
        # Volatility Z-Score Calculation
        avg_bb_width = indicators['bb_width'].tail(20).mean()
        std_bb_width = indicators['bb_width'].tail(100).std()
        z_score = (bb_width - avg_bb_width) / std_bb_width if std_bb_width > 0 else 0
        
        if bb_width < (avg_bb_width * 0.8):
            status = "COMPRESSED"
        elif bb_width > (avg_bb_width * 1.5):
            status = "EXPANDED"
        else:
            status = "NORMAL"
            
        # Institutional Efficiency (Alpha)
        # Point and Spread calculations
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info:
            spread = symbol_info.spread
            point = symbol_info.point if symbol_info.point > 0 else 0.00001
            spread_pips = spread # Spread in points
            avg_h1_range = indicators['tr'].tail(24).mean() / point
            alpha_score = (avg_h1_range - spread) / spread if spread > 0 else 0
            edge_ratio = avg_h1_range / spread if spread > 0 else 0
        else:
            alpha_score = 0
            edge_ratio = 0
            
        return {
            "symbol": self.symbol,
            "regime": regime,
            "confidence": round(confidence, 2),
            "volatility": {
                "status": status,
                "z_score": round(z_score, 2),
                "bb_width": round(bb_width, 4)
            },
            "institutional": {
                "alpha_efficiency": round(alpha_score, 2),
                "edge_ratio": round(edge_ratio, 2)
            },
            "metrics": {
                "adx": round(adx, 2),
                "rsi": round(rsi, 2),
                "price_vs_sma20": round((price - sma20) / price * 100, 2)
            },
            "timestamp": datetime.now().isoformat()
        }

def test_regime():
    """Quick test on key symbols."""
    if not mt5.initialize():
        print("MT5 Init Failed")
        return
        
    for sym in ["GOLD", "BTCUSD", "US100Cash", "EURUSD"]:
        detector = RegimeDetector(sym)
        result = detector.detect_regime()
        print(f"\n{sym.upper()} Analysis:")
        print(f"  Regime: {result['regime']} (Conf: {result['confidence']})")
        print(f"  Volatility: {result['volatility']['status']} (Z-Score: {result['volatility']['z_score']})")
        print(f"  Institutional Alpha: {result['institutional']['alpha_efficiency']}x")
        print(f"  Edge Ratio: {result['institutional']['edge_ratio']} (Range/Spread)")
        print(f"  ADX: {result['metrics']['adx']} | RSI: {result['metrics']['rsi']}")
        
    mt5.shutdown()

if __name__ == "__main__":
    test_regime()
