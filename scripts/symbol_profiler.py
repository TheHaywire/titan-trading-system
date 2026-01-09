"""
Symbol Intelligence Profiler
Generates comprehensive analysis reports with historical stats, 
time patterns, and trading intelligence for any symbol.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

class SymbolProfiler:
    """Complete symbol intelligence analysis"""
    
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.initialize_mt5()
        
    def initialize_mt5(self):
        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")
    
    def generate_profile(self):
        """Generate complete symbol profile"""
        print(f"\n🔬 Generating Complete Profile for {self.symbol}...")
        
        # Fetch comprehensive historical data
        data = self._fetch_historical_data()
        
        # Run all analyses
        profile = {
            'symbol': self.symbol,
            'generated_at': datetime.now().isoformat(),
            'price_history': self._analyze_price_history(data),
            'time_patterns': self._analyze_time_patterns(data),
            'volatility_profile': self._analyze_volatility(data),
            'trading_intelligence': self._generate_trading_intelligence(data),
            'current_state': self._get_current_state()
        }
        
        # Generate markdown report
        report_path = self._generate_report(profile)
        
        return report_path
    
    def _fetch_historical_data(self):
        """Fetch maximum available historical data"""
        print("📊 Fetching historical data...")
        
        # Fetch multiple timeframes for comprehensive analysis
        data = {}
        
        # Daily data for long-term analysis
        daily = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_D1, 0, 365)
        if daily is not None:
            data['daily'] = pd.DataFrame(daily)
            data['daily']['time'] = pd.to_datetime(data['daily']['time'], unit='s')
        
        # 1H data for intraday patterns
        h1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 1000)
        if h1 is not None:
            data['h1'] = pd.DataFrame(h1)
            data['h1']['time'] = pd.to_datetime(data['h1']['time'], unit='s')
        
        return data
    
    def _analyze_price_history(self, data):
        """Analyze historical price movements"""
        if 'daily' not in data:
            return {}
        
        df = data['daily']
        
        return {
            'all_time_high': float(df['high'].max()),
            'all_time_low': float(df['low'].min()),
            'current_price': float(df['close'].iloc[-1]),
            'distance_from_ath_pct': float(((df['close'].iloc[-1] - df['high'].max()) / df['high'].max()) * 100),
            'ytd_return_pct': float(((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100),
            'avg_daily_range_pct': float((df['high'] - df['low']).mean() / df['close'].mean() * 100),
            'max_drawdown_pct': float(self._calculate_max_drawdown(df['close']))
        }
    
    def _analyze_time_patterns(self, data):
        """Analyze best/worst times to trade"""
        if 'h1' not in data:
            return {}
        
        df = data['h1'].copy()
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        df['returns'] = df['close'].pct_change()
        
        # Hour-of-day analysis
        hourly_stats = df.groupby('hour')['returns'].agg(['mean', 'std', 'count'])
        best_hours = hourly_stats.nlargest(3, 'mean')
        worst_hours = hourly_stats.nsmallest(3, 'mean')
        
        # Day-of-week analysis
        daily_stats = df.groupby('day_of_week')['returns'].agg(['mean', 'std', 'count'])
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        return {
            'best_hours': [{'hour': int(idx), 'avg_return': float(row['mean'] * 100)} 
                          for idx, row in best_hours.iterrows()],
            'worst_hours': [{'hour': int(idx), 'avg_return': float(row['mean'] * 100)} 
                           for idx, row in worst_hours.iterrows()],
            'best_day': day_names[int(daily_stats['mean'].idxmax())],
            'worst_day': day_names[int(daily_stats['mean'].idxmin())]
        }
    
    def _analyze_volatility(self, data):
        """Analyze volatility characteristics"""
        if 'daily' not in data:
            return {}
        
        df = data['daily']
        df['atr'] = self._calculate_atr(df, period=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        
        # Classify volatility regimes
        atr_mean = df['atr_pct'].mean()
        atr_std = df['atr_pct'].std()
        
        high_vol_days = len(df[df['atr_pct'] > atr_mean + atr_std])
        low_vol_days = len(df[df['atr_pct'] < atr_mean - atr_std])
        
        return {
            'avg_atr_pct': float(atr_mean),
            'current_atr_pct': float(df['atr_pct'].iloc[-1]),
            'high_volatility_days_pct': float((high_vol_days / len(df)) * 100),
            'low_volatility_days_pct': float((low_vol_days / len(df)) * 100),
            'volatility_state': 'HIGH' if df['atr_pct'].iloc[-1] > atr_mean else 'NORMAL'
        }
    
    def _generate_trading_intelligence(self, data):
        """Generate actionable trading insights"""
        # Simple recommendations based on analysis
        price_hist = self._analyze_price_history(data)
        vol_profile = self._analyze_volatility(data)
        
        recommendations = []
        
        # Volatility-based recommendations
        if vol_profile.get('volatility_state') == 'HIGH':
            recommendations.append("⚠️ High volatility - Use wider stops (3-4% SL)")
            recommended_sl = 3.5
        else:
            recommendations.append("✅ Normal volatility - Standard stops OK (2% SL)")
            recommended_sl = 2.0
        
        # Trend recommendations
        if abs(price_hist.get('distance_from_ath_pct', 0)) < 5:
            recommendations.append("📈 Near all-time high - Watch for resistance/continuation")
        
        return {
            'recommendations': recommendations,
            'optimal_sl_pct': recommended_sl,
            'optimal_tp_multiplier': 3.0,
            'best_timeframe': '4H' if vol_profile.get('avg_atr_pct', 1) < 1.5 else '1H'
        }
    
    def _get_current_state(self):
        """Get current market state"""
        tick = mt5.symbol_info_tick(self.symbol)
        if tick is None:
            return {}
        
        return {
            'bid': float(tick.bid),
            'ask': float(tick.ask),
            'spread': float(tick.ask - tick.bid),
            'last_update': datetime.fromtimestamp(tick.time).isoformat()
        }
    
    def _calculate_max_drawdown(self, prices):
        """Calculate maximum drawdown"""
        cummax = prices.expanding().max()
        drawdown = ((prices - cummax) / cummax) * 100
        return drawdown.min()
    
    def _calculate_atr(self, df, period=14):
        """Calculate Average True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _generate_report(self, profile):
        """Generate markdown report"""
        Path("intelligence").mkdir(exist_ok=True)
        
        filename = f"intelligence/{self.symbol}_PROFILE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 📊 COMPLETE SYMBOL PROFILE: {self.symbol}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## Executive Summary\n\n")
            price = profile['price_history']
            vol = profile['volatility_profile']
            intel = profile['trading_intelligence']
            
            f.write(f"- **Current Price**: ${price.get('current_price', 0):.2f}\n")
            f.write(f"- **Avg Daily Range**: {price.get('avg_daily_range_pct', 0):.2f}%\n")
            f.write(f"- **Volatility State**: {vol.get('volatility_state', 'UNKNOWN')}\n")
            f.write(f"- **Recommended SL**: {intel.get('optimal_sl_pct', 2.0):.1f}%\n")
            f.write(f"- **Best Timeframe**: {intel.get('best_timeframe', '4H')}\n\n")
            
            # Price History
            f.write("## 📈 Price History\n\n")
            f.write(f"- **All-Time High**: ${price.get('all_time_high', 0):.2f}\n")
            f.write(f"- **All-Time Low**: ${price.get('all_time_low', 0):.2f}\n")
            f.write(f"- **Distance from ATH**: {price.get('distance_from_ath_pct', 0):.2f}%\n")
            f.write(f"- **YTD Return**: {price.get('ytd_return_pct', 0):.2f}%\n")
            f.write(f"- **Max Drawdown**: {price.get('max_drawdown_pct', 0):.2f}%\n\n")
            
            # Time Patterns
            if profile.get('time_patterns'):
                f.write("## ⏰ Time-Based Patterns\n\n")
                time_pat = profile['time_patterns']
                
                f.write("**Best Hours** (UTC):\n")
                for item in time_pat.get('best_hours', []):
                    f.write(f"- {item['hour']:02d}:00 - Avg: {item['avg_return']:.3f}%\n")
                
                f.write(f"\n**Best Day**: {time_pat.get('best_day', 'Unknown')}\n")
                f.write(f"**Worst Day**: {time_pat.get('worst_day', 'Unknown')}\n\n")
            
            # Trading Intelligence
            f.write("## 🎯 Trading Intelligence\n\n")
            for rec in intel.get('recommendations', []):
                f.write(f"{rec}\n")
            f.write("\n")
            
            f.write("**Optimal Strategy**:\n")
            f.write(f"- Stop Loss: {intel.get('optimal_sl_pct', 2.0):.1f}%\n")
            f.write(f"- Take Profit: {intel.get('optimal_tp_multiplier', 3.0):.1f}x Risk\n")
            f.write(f"- Best Timeframe: {intel.get('best_timeframe', '4H')}\n\n")
            
            f.write("---\n\n")
            f.write("*Generated by Titan Symbol Intelligence Profiler*\n")
        
        print(f"\n✅ Profile saved: {filename}")
        return filename

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Titan Symbol Profiler")
    parser.add_argument("symbol", help="Symbol to profile (e.g., GOLD, BTCUSD)")
    
    args = parser.parse_args()
    
    profiler = SymbolProfiler(args.symbol)
    report_path = profiler.generate_profile()
    
    print(f"\nREPORT_PATH:{report_path}")

if __name__ == "__main__":
    main()
