
import MetaTrader5 as mt5
import pandas as pd
import pandas_ta as ta

class RegimeDetector:
    """
    Classifies market conditions into regimes:
    - TRENDING_HIGH_VOL (Best for scalping)
    - TRENDING_LOW_VOL (Cautious)
    - RANGING (Do not trade)
    """
    
    def __init__(self):
        pass
        
    def detect(self, symbol: str) -> dict:
        """
        Analyzes H1 data to determine regime.
        Returns dict: {regime, adx, atr, trade_scalping}
        """
        
        # Fetch H1 Data (Trend Context)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        
        if rates is None or len(rates) < 30:
            return {
                "regime": "UNKNOWN",
                "adx": 0,
                "atr": 0,
                "trade_scalping": False
            }
            
        df = pd.DataFrame(rates)
        
        # Calculate ADX (Trend Strength)
        # Using pandas_ta for reliability
        try:
            # ADX requires High, Low, Close
            # Handle key variations if needed, but MT5 returns lowercase 'high', 'low', 'close'
            adx_df = df.ta.adx(high=df['high'], low=df['low'], close=df['close'], length=14)
            # adx_df usually contains ADX_14, DMP_14, DMN_14
            adx_col = f"ADX_14"
            if adx_col not in adx_df.columns:
                 # Fallback if column name differs
                 adx_col = adx_df.columns[0]
            
            current_adx = adx_df[adx_col].iloc[-1]
            
            # Calculate ATR (Volatility)
            df['atr'] = df.ta.atr(high=df['high'], low=df['low'], close=df['close'], length=14)
            current_atr = df['atr'].iloc[-1]
            
            # Determine Regime
            regime = "RANGING"
            trade_scalping = False
            
            if current_adx >= 25:
                # Strong Trend
                if current_atr > (current_atr * 0.8): # Simplified check, ideally compare to MA of ATR
                    regime = "TRENDING_HIGH_VOL"
                    trade_scalping = True
                else:
                    regime = "TRENDING_LOW_VOL"
                    trade_scalping = True # Can trade but maybe reduced size
            else:
                # Weak Trend / Ranging
                regime = "RANGING"
                trade_scalping = False
                
            return {
                "regime": regime,
                "adx": current_adx,
                "atr": current_atr,
                "trade_scalping": trade_scalping
            }
            
        except Exception as e:
            print(f"Error in RegimeDetector: {e}")
            return {
                "regime": "ERROR",
                "adx": 0,
                "atr": 0,
                "trade_scalping": False
            }
