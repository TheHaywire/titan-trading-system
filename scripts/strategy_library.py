"""
INSTITUTIONAL STRATEGY LIBRARY
===============================
10 comprehensive trading strategies for backtesting validation.
Each strategy implements: generate_signals(), get_name(), get_description()
"""

import pandas as pd
import numpy as np
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self, stop_loss_atr=2.0, take_profit_atr=3.0):
        self.stop_loss_atr = stop_loss_atr
        self.take_profit_atr = take_profit_atr
    
    @abstractmethod
    def generate_signals(self, df):
        """
        Generate buy/sell signals from data.
        Returns: DataFrame with 'signal' column (1=buy, -1=sell, 0=hold)
        """
        pass
    
    @abstractmethod
    def get_name(self):
        """Strategy name."""
        pass
    
    @abstractmethod
    def get_description(self):
        """Strategy description."""
        pass

# ========== MOMENTUM STRATEGIES ==========

class TopGainersVolume(BaseStrategy):
    """Strategy 1: Top Gainers + High Volume"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: Strong 3-bar move + volume surge
        condition = (
            (df['Change_3bar'] > 2.0) &  # 2%+ move in 3 bars
            (df['Rel_Volume'] > 2.0) &    # 2x volume
            (df['RSI'] < 70)              # Not overbought
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "Top Gainers + Volume"
    
    def get_description(self):
        return "Buy strong momentum with institutional volume confirmation"

class NewHighContinuation(BaseStrategy):
    """Strategy 2: New High Momentum Continuation"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: Near 52-bar high + volume + not extended
        condition = (
            (df['Near_High_52'] == 1) &
            (df['Rel_Volume'] > 1.5) &
            (df['Distance_SMA_20'] < 5.0)  # Not more than 5% above SMA20
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "New High Continuation"
    
    def get_description(self):
        return "Buy breakouts to new highs with volume confirmation"

class VolatilityBreakout(BaseStrategy):
    """Strategy 3: High Volatility Scalp"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: High ATR + tight BB squeeze breaking
        condition = (
            (df['ATR_Pct'] > df['ATR_Pct'].rolling(20).mean() * 1.5) &  # High volatility
            (df['BB_Width'] < df['BB_Width'].rolling(20).mean() * 0.8) &  # Squeeze
            (df['close'] > df['BB_Upper'])  # Breakout up
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "Volatility Breakout"
    
    def get_description(self):
        return "Scalp high-volatility breakouts from Bollinger squeeze"

# ========== MEAN REVERSION STRATEGIES ==========

class RSIOversoldBounce(BaseStrategy):
    """Strategy 4: RSI Oversold in Uptrend"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: RSI oversold + in uptrend
        condition = (
            (df['RSI'] < 30) &
            (df['Trend'] == 'Uptrend') &
            (df['close'] > df['SMA_200'])
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "RSI Oversold Bounce"
    
    def get_description(self):
        return "Buy oversold dips in confirmed uptrends"

class RSIOverboughtFade(BaseStrategy):
    """Strategy 5: RSI Overbought Fade"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: RSI overbought + at resistance (near high)
        condition = (
            (df['RSI'] > 75) &
            (df['Near_High_20'] == 1) &
            (df['Rel_Volume'] < 1.0)  # Volume dying (exhaustion)
        )
        df.loc[condition, 'signal'] = -1  # Short signal
        
        return df
    
    def get_name(self):
        return "RSI Overbought Fade"
    
    def get_description(self):
        return "Fade overbought rallies at resistance"

class BollingerMeanReversion(BaseStrategy):
    """Strategy 6: Bollinger Band Mean Reversion"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: Touch lower BB + RSI oversold
        condition = (
            (df['close'] < df['BB_Lower']) &
            (df['RSI'] < 35) &
            (df['Trend'] == 'Uptrend')
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "Bollinger Mean Reversion"
    
    def get_description(self):
        return "Buy lower Bollinger Band touches in uptrends"

# ========== TREND FOLLOWING STRATEGIES ==========

class GoldenCross(BaseStrategy):
    """Strategy 7: SMA Golden Cross"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: 50 SMA crosses above 200 SMA
        df.loc[df['Golden_Cross'] == 1, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "SMA Golden Cross"
    
    def get_description(self):
        return "Buy when 50 SMA crosses above 200 SMA"

class ChannelBreakout(BaseStrategy):
    """Strategy 8: Channel Breakout"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: Break above 20-day high
        condition = (
            (df['Near_High_20'] == 1) &
            (df['ADX'] > 20)  # Trending market
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "Channel Breakout"
    
    def get_description(self):
        return "Buy breakouts of 20-day channels in trends"

class ADXTrendFollowing(BaseStrategy):
    """Strategy 9: ADX Trend Following"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: Strong trend (ADX > 25) + price above 50 SMA + pullback
        condition = (
            (df['ADX'] > 25) &
            (df['close'] > df['SMA_50']) &
            (df['RSI'] > 40) & (df['RSI'] < 60)  # Pullback not oversold
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "ADX Trend Following"
    
    def get_description(self):
        return "Buy pullbacks in strong ADX trends"

# ========== COMBINED STRATEGIES ==========

class AdrenalineSMC(BaseStrategy):
    """Strategy 10: Adrenaline + SMC Combo"""
    
    def generate_signals(self, df):
        df = df.copy()
        df['signal'] = 0
        
        # Entry: High volume + near high + trend alignment
        condition = (
            (df['Rel_Volume'] > 1.5) &      # Institutional volume
            (df['Near_High_20'] == 1) &     # Breakout
            (df['close'] > df['SMA_50']) &  # Trend
            (df['RSI'] > 50)                # Momentum
        )
        df.loc[condition, 'signal'] = 1
        
        return df
    
    def get_name(self):
        return "Adrenaline + SMC"
    
    def get_description(self):
        return "Combined volume + momentum + trend alignment"

# ========== STRATEGY REGISTRY ==========

def get_all_strategies():
    """Return list of all strategy instances."""
    return [
        TopGainersVolume(),
        NewHighContinuation(),
        VolatilityBreakout(),
        RSIOversoldBounce(),
        RSIOverboughtFade(),
        BollingerMeanReversion(),
        GoldenCross(),
        ChannelBreakout(),
        ADXTrendFollowing(),
        AdrenalineSMC()
    ]

if __name__ == "__main__":
    print("📊 Institutional Strategy Library")
    print("=" * 60)
    
    strategies = get_all_strategies()
    
    for i, strategy in enumerate(strategies, 1):
        print(f"{i:2}. {strategy.get_name()}")
        print(f"    {strategy.get_description()}")
    
    print(f"\n✅ {len(strategies)} strategies loaded and ready for backtesting")
