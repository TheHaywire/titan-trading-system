"""
Data Intelligence Engine for Institutional Macro Trading.
Handles:
1. COT (Commitment of Traders) positioning research.
2. Historical Seasonality Analysis.
3. Open Interest (OI) Change tracking.
"""

import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os

import json

class DataIntelligence:
    def __init__(self):
        self.cot_file = os.path.join(os.path.dirname(__file__), 'cot_data.json')
        self.cot_data = self._load_cot_data()

    def _load_cot_data(self):
        if os.path.exists(self.cot_file):
            try:
                with open(self.cot_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def get_cot_positioning(self, symbol):
        """
        Retrieves COT positioning from cache or defaults to Mixed.
        """
        # Strip broker suffixes if any
        clean_symbol = symbol.replace("Cash", "").replace("!", "")
        
        if clean_symbol in self.cot_data:
            return self.cot_data[clean_symbol]['positioning']
        
        # Fallback for related pairs
        if "USD" in clean_symbol:
            # Check if any part of the symbol is in our keys
            for key in self.cot_data:
                if key in clean_symbol or clean_symbol in key:
                    return self.cot_data[key]['positioning']
        
        return "Mixed"

    def get_seasonality(self, symbol, month=None):
        """
        Calculates historical seasonality (avg return for the current month).
        Analyzes 5 years of daily data.
        """
        if month is None:
            month = datetime.now().month
            
        if not mt5.initialize():
            return "Neutral"
            
        # Fetch 5 years of daily data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 1260)
        if rates is None or len(rates) < 100:
            return "Neutral"
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['month'] = df['time'].dt.month
        df['year'] = df['time'].dt.year
        
        # Calculate monthly returns
        monthly_data = df.groupby(['year', 'month'])['close'].last().pct_change()
        monthly_data = monthly_data.reset_index()
        monthly_data.columns = ['year', 'month', 'return']
        
        target_month_returns = monthly_data[monthly_data['month'] == month]['return']
        
        if len(target_month_returns) == 0:
            return "Neutral"
            
        avg_return = target_month_returns.mean()
        win_rate = (target_month_returns > 0).mean()
        
        if avg_return > 0.01 and win_rate >= 0.6: # Strong positive tendency
            return "Strong Positive"
        elif avg_return > 0.005: 
            return "Positive"
        elif avg_return < -0.01 and win_rate <= 0.4:
            return "Strong Negative"
        elif avg_return < -0.005:
            return "Negative"
        else:
            return "Neutral"

    def get_oi_change(self, symbol):
        """
        Calculates Open Interest change. 
        Note: MT5 Forex doesn't have real OI, but Futures do.
        For Forex, we use Tick Volume Change as a proxy for institutional participation.
        """
        if not mt5.initialize():
            return 0.0
            
        # Get last 2 days of H1 data to compare volume
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 10)
        if rates is None or len(rates) < 2:
            return 0.0
            
        df = pd.DataFrame(rates)
        # Using tick_volume as proxy for intensity if real volume is not available
        vol_col = 'real_volume' if 'real_volume' in df.columns and df['real_volume'].sum() > 0 else 'tick_volume'
        
        last_vol = float(df[vol_col].iloc[-1])
        prev_vol = float(df[vol_col].iloc[-2])
        
        if prev_vol < 1.0: # Prevent division by zero or near-zero
            return 0.0
            
        oi_proxy_change = ((last_vol - prev_vol) / prev_vol) * 100
        
        # Cap at 500% to prevent extreme outliers from breaking reports
        return max(-500.0, min(500.0, oi_proxy_change))

if __name__ == "__main__":
    # Test
    intel = DataIntelligence()
    print(f"Testing EURUSD Seasonality: {intel.get_seasonality('EURUSD')}")
    print(f"Testing EURUSD Volume Proxy Change: {intel.get_oi_change('EURUSD'):.2f}%")
