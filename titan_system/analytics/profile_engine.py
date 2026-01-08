"""
TITAN PROFILE ENGINE
====================
Calculates Market Profile (TPO) and Volume Profile for institutional context.
Helps identify Value Areas, Points of Control (POC), and High/Low Volume Nodes.

Features:
1. TPO Profile (Time Price Opportunity)
2. Volume Profile (Volume at Price)
3. Session-Specific Profiles (Asian, London, NY)
4. Contextual Analysis (Value Area status, POC proximity)
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger("Titan.Profile")

class ProfileEngine:
    """
    Institutional Profile Engine for TPO and Volume analysis.
    """
    
    def __init__(self, tick_size: float = 0.1):
        """
        Args:
            tick_size: Price bin size (e.g., 0.1 for GOLD, 0.0001 for EURUSD)
        """
        self.tick_size = tick_size

    def calculate_volume_profile(self, df: pd.DataFrame, bins: int = 50) -> Dict:
        """
        Calculate Volume Profile (Volume at Price)
        """
        if df.empty or 'tick_volume' not in df.columns:
            return {}

        min_price = df['low'].min()
        max_price = df['high'].max()
        
        # Create bins
        price_bins = np.linspace(min_price, max_price, bins + 1)
        df['bin'] = pd.cut(df['close'], bins=price_bins)
        
        # Aggregate volume
        profile = df.groupby('bin')['tick_volume'].sum().reset_index()
        profile['price'] = profile['bin'].apply(lambda x: x.mid)
        
        # Find VPOC (Volume Point of Control)
        vpoc_idx = profile['tick_volume'].idxmax()
        vpoc = profile.loc[vpoc_idx, 'price']
        
        # Calculate Value Area (70% of volume)
        total_volume = profile['tick_volume'].sum()
        target_volume = total_volume * 0.70
        
        sorted_profile = profile.sort_values(by='tick_volume', ascending=False)
        cumulative_vol = 0
        va_prices = []
        
        for _, row in sorted_profile.iterrows():
            cumulative_vol += row['tick_volume']
            va_prices.append(row['price'])
            if cumulative_vol >= target_volume:
                break
        
        vvah = max(va_prices)
        vval = min(va_prices)
        
        return {
            'vpoc': vpoc,
            'vvah': vvah,
            'vval': vval,
            'total_volume': total_volume,
            'profile': profile.to_dict(orient='records')
        }

    def calculate_tpo_profile(self, df: pd.DataFrame, bins: int = 50) -> Dict:
        """
        Calculate TPO Profile (Time Price Opportunity)
        """
        if df.empty:
            return {}

        min_price = df['low'].min()
        max_price = df['high'].max()
        
        price_bins = np.linspace(min_price, max_price, bins + 1)
        
        tpo_counts = np.zeros(bins)
        
        for _, row in df.iterrows():
            # For each bar, mark all price bins it covered
            b_low = row['low']
            b_high = row['high']
            
            indices = np.where((price_bins[:-1] <= b_high) & (price_bins[1:] >= b_low))[0]
            tpo_counts[indices] += 1
            
        prices = (price_bins[:-1] + price_bins[1:]) / 2
        
        # POC (Point of Control)
        poc_idx = np.argmax(tpo_counts)
        poc = prices[poc_idx]
        
        # Value Area (70% of TPOs)
        total_tpos = np.sum(tpo_counts)
        target_tpos = total_tpos * 0.70
        
        # Simple VA calculation: expand from POC
        va_idx = [poc_idx]
        current_tpos = tpo_counts[poc_idx]
        
        l_idx = poc_idx - 1
        r_idx = poc_idx + 1
        
        while current_tpos < target_tpos and (l_idx >= 0 or r_idx < bins):
            l_val = tpo_counts[l_idx] if l_idx >= 0 else 0
            r_val = tpo_counts[r_idx] if r_idx < bins else 0
            
            if l_val >= r_val:
                current_tpos += l_val
                va_idx.append(l_idx)
                l_idx -= 1
            else:
                current_tpos += r_val
                va_idx.append(r_idx)
                r_idx += 1
                
        vah = prices[max(va_idx)]
        val = prices[min(va_idx)]
        
        # Initial Balance (Typical first hour of trading - depends on timeframe)
        # Assuming H1 data for simplicity, IB is first row.
        # For M5 data, IB would be first 12 rows.
        ib_high = df['high'].iloc[0]
        ib_low = df['low'].iloc[0]

        return {
            'poc': poc,
            'vah': vah,
            'val': val,
            'ib_high': ib_high,
            'ib_low': ib_low,
            'tpo_count': total_tpos
        }

    def get_session_context(self, df: pd.DataFrame, symbol: str = "GOLD") -> Dict:
        """
        Analyze current price in context of Volume and TPO profiles
        """
        if df.empty:
            return {}
            
        current_price = df['close'].iloc[-1]
        
        # 1. Overall Profile (Recent Context)
        lookback = min(len(df), 300)
        recent_df = df.iloc[-lookback:].copy()
        
        v_profile = self.calculate_volume_profile(recent_df)
        t_profile = self.calculate_tpo_profile(recent_df)
        
        # 2. Session Slicing (Institutional Perspective)
        # Assuming H1 or M15 data with time column
        session_profiles = {}
        if 'time' in df.columns:
            recent_df['dt'] = pd.to_datetime(recent_df['time'], unit='s')
            recent_df['hour'] = recent_df['dt'].dt.hour
            
            sessions = {
                'asian': (22, 8),
                'london': (8, 16),
                'ny': (13, 21)
            }
            
            for s_name, (start, end) in sessions.items():
                if start > end: # Crossover
                    s_df = recent_df[(recent_df['hour'] >= start) | (recent_df['hour'] < end)]
                else:
                    s_df = recent_df[(recent_df['hour'] >= start) & (recent_df['hour'] < end)]
                
                if not s_df.empty:
                    session_profiles[s_name] = {
                        'volume': self.calculate_volume_profile(s_df),
                        'tpo': self.calculate_tpo_profile(s_df),
                        'range': (s_df['low'].min(), s_df['high'].max())
                    }

        context = {
            'current_price': current_price,
            'volume_profile': v_profile,
            'tpo_profile': t_profile,
            'session_profiles': session_profiles,
            'status': 'neutral',
            'bias': 'neutral'
        }
        
        # Determine status relative to TPO Value Area
        vah = t_profile.get('vah', 999999)
        val = t_profile.get('val', 0)
        
        if current_price > vah:
            context['status'] = 'above_value'
            context['bias'] = 'bullish_extension'
        elif current_price < val:
            context['status'] = 'below_value'
            context['bias'] = 'bearish_extension'
        else:
            context['status'] = 'inside_value'
            context['bias'] = 'mean_reverting'
                
        # Proximity to POC
        poc = v_profile.get('vpoc', 0)
        dist_to_poc = abs(current_price - poc) / current_price * 100
        context['poc_proximity_pct'] = dist_to_poc
        
        return context

# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    import MetaTrader5 as mt5
    
    print("=" * 60)
    print("TITAN PROFILE ENGINE - TEST")
    print("=" * 60)
    
    if not mt5.initialize():
        print("MT5 failed")
        exit()
        
    symbol = "GOLD"
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 300)
    mt5.shutdown()
    
    if rates is None:
        print("No data")
        exit()
        
    df = pd.DataFrame(rates)
    
    engine = ProfileEngine(tick_size=0.1)
    context = engine.get_session_context(df, symbol)
    
    print(f"\nSymbol: {symbol} | Current Price: ${context['current_price']:.2f}")
    print(f"Market Status: {context['status']} | Bias: {context['bias']}")
    
    tp = context['tpo_profile']
    print("\n[DAILY PROFILE]")
    print(f"  TPO POC:  ${tp['poc']:.2f} | VA: ${tp['val']:.2f} - ${tp['vah']:.2f}")
    
    vp = context['volume_profile']
    print(f"  VOL POC:  ${vp['vpoc']:.2f} | VA: ${vp['vval']:.2f} - ${vp['vvah']:.2f}")
    
    print("\n[SESSION PROFILES]")
    for s_name, s_data in context['session_profiles'].items():
        print(f"  {s_name.upper()}:")
        print(f"    POC: ${s_data['tpo']['poc']:.2f} | Range: ${s_data['range'][0]:.2f} - ${s_data['range'][1]:.2f}")
        print(f"    VPOC: ${s_data['volume']['vpoc']:.2f}")
    
    print(f"\nDist to POC: {context['poc_proximity_pct']:.4f}%")
    
    print("\nSUCCESS: Profile Engine working!")
