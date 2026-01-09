"""
Advanced Symbol Intelligence Profiler
Generates institutional-grade research reports with backtesting,
pattern performance, regime analysis, and comprehensive trading playbooks.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

from scripts.technical_patterns import get_all_patterns

class AdvancedSymbolProfiler:
    """Professional-grade symbol intelligence with backtest validation"""
    
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.initialize_mt5()
        
    def initialize_mt5(self):
        if not mt5.initialize():
            raise RuntimeError("MT5 initialization failed")
    
    def generate_profile(self):
        """Generate comprehensive institutional-grade profile"""
        print(f"\n🔬 Generating Advanced Intelligence Profile for {self.symbol}...")
        
        # Fetch comprehensive data
        data = self._fetch_comprehensive_data()
        
        # Run exhaustive analyses
        print("📊 Running price history analysis...")
        price_history = self._analyze_price_history(data)
        
        print("⏰ Analyzing time-based patterns...")
        time_patterns = self._analyze_time_patterns(data)
        
        print("📉 Profiling volatility regimes...")
        volatility_profile = self._analyze_volatility_regimes(data)
        
        print("🎯 Analyzing pattern performance...")
        pattern_performance = self._analyze_pattern_performance(data)
        
        print("🔄 Classifying market regimes...")
        regime_analysis = self._analyze_market_regimes(data)
        
        print("📈 Running backtest validation...")
        backtest_results = self._run_quick_backtest(data)
        
        print("🧠 Generating trading playbook...")
        trading_playbook = self._generate_trading_playbook(
            data, price_history, volatility_profile, 
            pattern_performance, regime_analysis, backtest_results
        )
        
        profile = {
            'symbol': self.symbol,
            'generated_at': datetime.now().isoformat(),
            'price_history': price_history,
            'time_patterns': time_patterns,
            'volatility_profile': volatility_profile,
            'pattern_performance': pattern_performance,
            'regime_analysis': regime_analysis,
            'backtest_results': backtest_results,
            'trading_playbook': trading_playbook,
            'current_state': self._get_current_state()
        }
        
        # Generate professional report
        report_path = self._generate_professional_report(profile)
        
        return report_path
    
    def _fetch_comprehensive_data(self):
        """Fetch multi-timeframe historical data"""
        print("📊 Fetching comprehensive historical data...")
        
        data = {}
        
        # Weekly for macro trend
        weekly = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_W1, 0, 52)
        if weekly is not None:
            data['weekly'] = pd.DataFrame(weekly)
            data['weekly']['time'] = pd.to_datetime(data['weekly']['time'], unit='s')
        
        # Daily for main analysis
        daily = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_D1, 0, 365)
        if daily is not None:
            data['daily'] = pd.DataFrame(daily)
            data['daily']['time'] = pd.to_datetime(data['daily']['time'], unit='s')
        
        # 4H for regime analysis
        h4 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H4, 0, 500)
        if h4 is not None:
            data['h4'] = pd.DataFrame(h4)
            data['h4']['time'] = pd.to_datetime(data['h4']['time'], unit='s')
        
        # 1H for intraday patterns
        h1 = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 1000)
        if h1 is not None:
            data['h1'] = pd.DataFrame(h1)
            data['h1']['time'] = pd.to_datetime(data['h1']['time'], unit='s')
        
        return data
    
    def _analyze_price_history(self, data):
        """Comprehensive price history analysis"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        
        # Calculate various metrics
        current_price = float(df['close'].iloc[-1])
        ath = float(df['high'].max())
        atl = float(df['low'].min())
        
        # Price levels
        price_range = ath - atl
        current_position_in_range = ((current_price - atl) / price_range) * 100
        
        # Returns
        df['returns'] = df['close'].pct_change()
        
        # Monthly returns for seasonality
        df['month'] = df['time'].dt.month
        monthly_returns = df.groupby('month')['returns'].mean() * 100
        
        return {
            'all_time_high': ath,
            'all_time_low': atl,
            'current_price': current_price,
            'distance_from_ath_pct': float(((current_price - ath) / ath) * 100),
            'distance_from_atl_pct': float(((current_price - atl) / atl) * 100),
            'position_in_range_pct': float(current_position_in_range),
            'ytd_return_pct': float(((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100),
            'avg_daily_range_pct': float(((df['high'] - df['low']) / df['close']).mean() * 100),
            'max_drawdown_pct': float(self._calculate_max_drawdown(df['close'])),
            'avg_daily_return_pct': float(df['returns'].mean() * 100),
           'std_daily_return_pct': float(df['returns'].std() * 100),
            'best_month': int(monthly_returns.idxmax()),
            'worst_month': int(monthly_returns.idxmin()),
            'sharpe_ratio': float(df['returns'].mean() / df['returns'].std() * np.sqrt(252)) if df['returns'].std() > 0 else 0
        }
    
    def _analyze_time_patterns(self, data):
        """Advanced time-based pattern analysis"""
        if 'h1' not in data:
            return {}
        
        df = data['h1'].copy()
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek
        df['returns'] = df['close'].pct_change()
        df['range_pct'] = ((df['high'] - df['low']) / df['close']) * 100
        
        # Hour analysis with win rate
        hourly_stats = df.groupby('hour').agg({
            'returns': ['mean', 'std', 'count'],
            'range_pct': 'mean'
        })
        hourly_stats.columns = ['avg_return', 'std_return', 'count', 'avg_range']
        hourly_stats['win_rate'] = df.groupby('hour')['returns'].apply(lambda x: (x > 0).sum() / len(x) * 100)
        
        # Day of week analysis
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_stats = df.groupby('day_of_week').agg({
            'returns': ['mean', 'count'],
            'range_pct': 'mean'
        })
        daily_stats.columns = ['avg_return', 'count', 'avg_range']
        daily_stats['win_rate'] = df.groupby('day_of_week')['returns'].apply(lambda x: (x > 0).sum() / len(x) * 100)
        
        # Find best/worst trading windows
        best_hours = hourly_stats.nlargest(5, 'win_rate')
        worst_hours = hourly_stats.nsmallest(5, 'win_rate')
        
        return {
            'best_hours': [
                {
                    'hour': int(idx),
                    'avg_return': float(row['avg_return'] * 100),
                    'win_rate': float(row['win_rate']),
                    'avg_range': float(row['avg_range'])
                }
                for idx, row in best_hours.iterrows()
            ],
            'worst_hours': [
                {
                    'hour': int(idx),
                    'avg_return': float(row['avg_return'] * 100),
                    'win_rate': float(row['win_rate'])
                }
                for idx, row in worst_hours.iterrows()
            ],
            'best_day': day_names[int(daily_stats['win_rate'].idxmax())],
            'worst_day': day_names[int(daily_stats['win_rate'].idxmin())],
            'day_stats': [
                {
                    'day': day_names[i],
                    'avg_return': float(daily_stats.iloc[i]['avg_return'] * 100),
                    'win_rate': float(daily_stats.iloc[i]['win_rate'])
                }
                for i in range(len(daily_stats))
            ]
        }
    
    def _analyze_volatility_regimes(self, data):
        """Classify volatility states and their performance"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        df['atr'] = self._calculate_atr(df, period=14)
        df['atr_pct'] = (df['atr'] / df['close']) * 100
        df['returns'] = df['close'].pct_change()
        
        # Volatility regime classification
        atr_mean = df['atr_pct'].mean()
        atr_std = df['atr_pct'].std()
        
        df['regime'] = 'NORMAL'
        df.loc[df['atr_pct'] > atr_mean + atr_std, 'regime'] = 'HIGH_VOL'
        df.loc[df['atr_pct'] < atr_mean - atr_std, 'regime'] = 'LOW_VOL'
        
        # Performance by regime
        regime_stats = df.groupby('regime')['returns'].agg(['mean', 'std', 'count'])
        regime_stats['win_rate'] = df.groupby('regime')['returns'].apply(lambda x: (x > 0).sum() / len(x) * 100)
        
        return {
            'avg_atr_pct': float(atr_mean),
            'current_atr_pct': float(df['atr_pct'].iloc[-1]),
            'volatility_state': df['regime'].iloc[-1],
            'high_vol_days_pct': float((df['regime'] == 'HIGH_VOL').sum() / len(df) * 100),
            'normal_vol_days_pct': float((df['regime'] == 'NORMAL').sum() / len(df) * 100),
            'low_vol_days_pct': float((df['regime'] == 'LOW_VOL').sum() / len(df) * 100),
            'regime_performance': {
                regime: {
                    'avg_return': float(stats['mean'] * 100),
                    'win_rate': float(regime_stats.loc[regime, 'win_rate']),
                    'days': int(stats['count'])
                }
                for regime, stats in regime_stats.iterrows()
            }
        }
    
    def _analyze_pattern_performance(self, data):
        """Analyze which patterns work best historically"""
        if 'h4' not in data:
            return {}
        
        df = data['h4'].copy()
        
        # Add RSI for pattern detection
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Scan for patterns and track outcomes
        pattern_results = []
        
        for i in range(100, len(df) - 10):  # Leave room for outcome
            df_slice = df.iloc[i-100:i+1].copy()
            patterns = get_all_patterns(df_slice)
            
            if patterns:
                # Measure outcome (next 10 bars)
                entry_price = df['close'].iloc[i]
                future_high = df['high'].iloc[i+1:i+11].max()
                future_low = df['low'].iloc[i+1:i+11].min()
                
                upside = ((future_high - entry_price) / entry_price) * 100
                downside = ((entry_price - future_low) / entry_price) * 100
                
                for pattern in patterns[:1]:  # Use first pattern
                    pattern_results.append({
                        'pattern': pattern,
                        'upside': upside,
                        'downside': downside,
                        'outcome': 'WIN' if upside > downside else 'LOSS'
                    })
        
        # Aggregate by pattern
        pattern_df = pd.DataFrame(pattern_results)
        if len(pattern_df) == 0:
            return {'patterns_analyzed': 0}
        
        pattern_stats = pattern_df.groupby('pattern').agg({
            'outcome': lambda x: (x == 'WIN').sum() / len(x) * 100,
            'upside': 'mean',
            'downside': 'mean'
        }).reset_index()
        pattern_stats.columns = ['pattern', 'win_rate', 'avg_upside', 'avg_downside']
        pattern_stats = pattern_stats.sort_values('win_rate', ascending=False)
        
        return {
            'patterns_analyzed': len(pattern_df),
            'top_patterns': [
                {
                    'pattern': row['pattern'],
                    'win_rate': float(row['win_rate']),
                    'avg_upside': float(row['avg_upside']),
                    'avg_downside': float(row['avg_downside'])
                }
                for _, row in pattern_stats.head(5).iterrows()
            if row['win_rate'] > 50
            ]
        }
    
    def _analyze_market_regimes(self, data):
        """Classify trending vs ranging periods"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Simple ADX for trend strength
        df['returns'] = df['close'].pct_change()
        
        # Classify regimes
        df['regime'] = 'UNKNOWN'
        df.loc[(df['close'] > df['sma_200']) & (df['sma_50'] > df['sma_200']), 'regime'] = 'STRONG_UPTREND'
        df.loc[(df['close'] < df['sma_200']) & (df['sma_50'] < df['sma_200']), 'regime'] = 'STRONG_DOWNTREND'
        df.loc[(df['close'] > df['sma_200']) & (df['sma_50'] <= df['sma_200']), 'regime'] = 'WEAK_UPTREND'
        df.loc[(df['close'] < df['sma_200']) & (df['sma_50'] >= df['sma_200']), 'regime'] = 'WEAK_DOWNTREND'
        
        # Performance by regime
        regime_counts = df['regime'].value_counts()
        regime_returns = df.groupby('regime')['returns'].mean() * 100
        
        return {
            'current_regime': df['regime'].iloc[-1],
            'regime_distribution': {
                regime: {
                    'days': int(count),
                    'pct': float(count / len(df) * 100),
                    'avg_daily_return': float(regime_returns.get(regime, 0))
                }
                for regime, count in regime_counts.items()
            }
        }
    
    def _run_quick_backtest(self, data):
        """Run simple backtest on historical data"""
        if 'daily' not in data or 'h1' not in data:
            return {'backtested': False}
        
        # Use last 100 days for quick validation
        df_daily = data['daily'].tail(100).copy()
        df_daily['sma_200'] = df_daily['close'].rolling(window=50).mean()  # Use 50 for shorter period
        
        # Simulate simple trend-following
        trades = []
        for i in range(30, len(df_daily)):
            price = df_daily['close'].iloc[i]
            sma = df_daily['sma_200'].iloc[i]
            
            if pd.isna(sma):
                continue
            
            # Simple rule: buy if above SMA, measure outcome
            if price > sma:
                # Measure next 5 days
                future_return = ((df_daily['close'].iloc[min(i+5, len(df_daily)-1)] - price) / price) * 100
                trades.append({
                    'direction': 'BUY',
                    'return': future_return,
                    'outcome': 'WIN' if future_return > 0 else 'LOSS'
                })
        
        if len(trades) == 0:
            return {'backtested': False}
        
        trades_df = pd.DataFrame(trades)
        wins = (trades_df['outcome'] == 'WIN').sum()
        
        return {
            'backtested': True,
            'total_trades': len(trades),
            'wins': int(wins),
            'losses': int(len(trades) - wins),
            'win_rate': float(wins / len(trades) * 100),
            'avg_return': float(trades_df['return'].mean()),
            'best_trade': float(trades_df['return'].max()),
            'worst_trade': float(trades_df['return'].min())
        }
    
    def _generate_trading_playbook(self, data, price_hist, vol_profile, pattern_perf, regime_analysis, backtest):
        """Generate comprehensive trading playbook"""
        playbook = []
        
        # Volatility-based rules
        if vol_profile.get('volatility_state') == 'HIGH_VOL':
            playbook.append("⚠️ HIGH VOLATILITY: Use 3-4% SL, reduce position size by 50%")
            recommended_sl = 3.5
        elif vol_profile.get('volatility_state') == 'LOW_VOL':
            playbook.append("📉 LOW VOLATILITY: Tighten stops to 1.5% SL, breakout setups preferred")
            recommended_sl = 1.5
        else:
            playbook.append("✅ NORMAL VOLATILITY: Standard 2% SL, all setups valid")
            recommended_sl = 2.0
        
        # Trend-based rules
        current_regime = regime_analysis.get('current_regime', 'UNKNOWN')
        if 'STRONG_UPTREND' in current_regime:
            playbook.append("📈 STRONG UPTREND: Only BUY setups, avoid shorts")
            playbook.append("🎯 Entry: Pullbacks to 4H 50 SMA or support zones")
        elif 'STRONG_DOWNTREND' in current_regime:
            playbook.append("📉 STRONG DOWNTREND: Only SELL setups, avoid longs")
            playbook.append("🎯 Entry: Rallies to 4H 50 SMA or resistance zones")
        else:
            playbook.append("⚡ RANGING/WEAK TREND: Reduce size, use tighter stops")
        
        # Pattern recommendations
        if pattern_perf.get('top_patterns'):
            top_pattern = pattern_perf['top_patterns'][0]
            playbook.append(f"🔥 BEST PATTERN: {top_pattern['pattern']} ({top_pattern['win_rate']:.0f}% win rate)")
        
        # Time recommendations
        playbook.append("⏰ BEST TRADING HOURS: See time analysis below")
        
        # Price level warnings
        if abs(price_hist.get('distance_from_ath_pct', 0)) < 3:
            playbook.append("⚠️ NEAR ATH: Watch for resistance, reduce size on longs")
        elif abs(price_hist.get('distance_from_atl_pct', 0)) < 10:
            playbook.append("⚠️ NEAR ATL: Strong support zone, favors longs")
        
        return {
            'rules': playbook,
            'optimal_sl_pct': recommended_sl,
            'optimal_tp_multiplier': 3.0,
            'position_size_multiplier': 0.5 if vol_profile.get('volatility_state') == 'HIGH_VOL' else 1.0,
            'preferred_timeframe': '1H' if vol_profile.get('avg_atr_pct', 1) > 1.5 else '4H'
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
    
    def _generate_professional_report(self, profile):
        """Generate institutional-grade markdown report"""
        Path("intelligence").mkdir(exist_ok=True)
        
        filename = f"intelligence/{self.symbol}_INTEL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            self._write_report_header(f, profile)
            self._write_executive_summary(f, profile)
            self._write_price_analysis(f, profile)
            self._write_backtest_results(f, profile)
            self._write_regime_analysis(f, profile)
            self._write_pattern_performance(f, profile)
            self._write_time_intelligence(f, profile)
            self._write_volatility_profile(f, profile)
            self._write_trading_playbook(f, profile)
            self._write_footer(f)
        
        print(f"\n✅ Professional intelligence report saved: {filename}")
        return filename
    
    def _write_report_header(self, f, profile):
        f.write(f"# 🏛️ INSTITUTIONAL INTELLIGENCE REPORT: {self.symbol}\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        f.write("> [!NOTE]\n")
        f.write("> This is a comprehensive institutional-grade analysis combining historical statistics,\n")
        f.write("> backtest validation, pattern performance, and actionable trading intelligence.\n\n")
        f.write("---\n\n")
    
    def _write_executive_summary(self, f, profile):
        f.write("## 📊 Executive Summary\n\n")
        
        price = profile['price_history']
        vol = profile['volatility_profile']
        regime = profile['regime_analysis']
        playbook = profile['trading_playbook']
        backtest = profile['backtest_results']
        
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| **Current Price** | ${price.get('current_price', 0):.2f} |\n")
        f.write(f"| **Distance from ATH** | {price.get('distance_from_ath_pct', 0):.2f}% |\n")
        f.write(f"| **YTD Return** | {price.get('ytd_return_pct', 0):+.2f}% |\n")
        f.write(f"| **Sharpe Ratio** | {price.get('sharpe_ratio', 0):.2f} |\n")
        f.write(f"| **Volatility State** | {vol.get('volatility_state', 'UNKNOWN')} |\n")
        f.write(f"| **Current Regime** | {regime.get('current_regime', 'UNKNOWN')} |\n")
        f.write(f"| **Recommended SL** | {playbook.get('optimal_sl_pct', 2.0):.1f}% |\n")
        f.write(f"| **Best Timeframe** | {playbook.get('preferred_timeframe', '4H')} |\n")
        
        if backtest.get('backtested'):
            f.write(f"| **Backtest Win Rate** | {backtest.get('win_rate', 0):.1f}% |\n")
        
        f.write("\n")
    
    def _write_price_analysis(self, f, profile):
        price = profile['price_history']
        
        f.write("## 📈 Price History & Performance\n\n")
        
        f.write("### Key Levels\n\n")
        f.write(f"- **All-Time High**: ${price.get('all_time_high', 0):.2f}\n")
        f.write(f"- **All-Time Low**: ${price.get('all_time_low', 0):.2f}\n")
        f.write(f"- **Current Position in Range**: {price.get('position_in_range_pct', 0):.1f}%\n\n")
        
        f.write("### Returns & Risk\n\n")
        f.write(f"- **YTD Return**: {price.get('ytd_return_pct', 0):+.2f}%\n")
        f.write(f"- **Avg Daily Return**: {price.get('avg_daily_return_pct', 0):+.3f}%\n")
        f.write(f"- **Volatility (Std Dev)**: {price.get('std_daily_return_pct', 0):.3f}%\n")
        f.write(f"- **Max Drawdown**: {price.get('max_drawdown_pct', 0):.2f}%\n")
        f.write(f"- **Sharpe Ratio**: {price.get('sharpe_ratio', 0):.2f}\n\n")
        
        f.write("### Seasonality\n\n")
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        f.write(f"- **Best Month**: {month_names[price.get('best_month', 1) - 1]}\n")
        f.write(f"- **Worst Month**: {month_names[price.get('worst_month', 1) - 1]}\n\n")
        
        f.write("---\n\n")
    
    def _write_backtest_results(self, f, profile):
        backtest = profile['backtest_results']
        
        if not backtest.get('backtested'):
            return
        
        f.write("## 🧪 Backtest Validation\n\n")
        
        f.write("> [!IMPORTANT]\n")
        win_rate = backtest.get('win_rate', 0)
        if win_rate >= 60:
            f.write(f"> **Backtest shows {win_rate:.1f}% win rate** - Strategy is validated! ✅\n\n")
        elif win_rate >= 50:
            f.write(f"> **Backtest shows {win_rate:.1f}% win rate** - Strategy is marginally profitable.\n\n")
        else:
            f.write(f"> **Backtest shows {win_rate:.1f}% win rate** - Strategy needs refinement! ⚠️\n\n")
        
        f.write("**Results** (Last 100 days, Simple Trend-Following):\n\n")
        f.write(f"- Total Trades: {backtest.get('total_trades', 0)}\n")
        f.write(f"- Wins: {backtest.get('wins', 0)}\n")
        f.write(f"- Losses: {backtest.get('losses', 0)}\n")
        f.write(f"- Win Rate: **{win_rate:.1f}%**\n")
        f.write(f"- Avg Return: {backtest.get('avg_return', 0):+.2f}%\n")
        f.write(f"- Best Trade: +{backtest.get('best_trade', 0):.2f}%\n")
        f.write(f"- Worst Trade: {backtest.get('worst_trade', 0):.2f}%\n\n")
        
        f.write("---\n\n")
    
    def _write_regime_analysis(self, f, profile):
        regime = profile['regime_analysis']
        
        f.write("## 🔄 Market Regime Analysis\n\n")
        
        f.write(f"**Current Regime**: **{regime.get('current_regime', 'UNKNOWN')}**\n\n")
        
        f.write("### Historical Regime Distribution\n\n")
        f.write("| Regime | Days | % of Time | Avg Daily Return |\n")
        f.write("|--------|------|-----------|------------------|\n")
        
        for regime_name, stats in regime.get('regime_distribution', {}).items():
            f.write(f"| {regime_name} | {stats['days']} | {stats['pct']:.1f}% | {stats['avg_daily_return']:+.3f}% |\n")
        
        f.write("\n---\n\n")
    
    def _write_pattern_performance(self, f, profile):
        pattern = profile['pattern_performance']
        
        if pattern.get('patterns_analyzed', 0) == 0:
            return
        
        f.write("## 🎯 Pattern Performance Analysis\n\n")
        
        f.write(f"**Total Patterns Analyzed**: {pattern['patterns_analyzed']}\n\n")
        
        if pattern.get('top_patterns'):
            f.write("### Top Performing Patterns\n\n")
            f.write("| Pattern | Win Rate | Avg Upside | Avg Downside |\n")
            f.write("|---------|----------|------------|---------------|\n")
            
            for p in pattern['top_patterns']:
                f.write(f"| {p['pattern']} | **{p['win_rate']:.1f}%** | +{p['avg_upside']:.2f}% | -{p['avg_downside']:.2f}% |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
    
    def _write_time_intelligence(self, f, profile):
        time_pat = profile.get('time_patterns', {})
        
        if not time_pat:
            return
        
        f.write("## ⏰ Time-Based Trading Intelligence\n\n")
        
        f.write("### Best Trading Hours (UTC)\n\n")
        f.write("| Hour | Win Rate | Avg Return | Avg Range |\n")
        f.write("|------|----------|------------|------------|\n")
        
        for item in time_pat.get('best_hours', [])[:5]:
            f.write(f"| {item['hour']:02d}:00 | **{item['win_rate']:.1f}%** | {item['avg_return']:+.3f}% | {item['avg_range']:.2f}% |\n")
        
        f.write("\n### Day of Week Performance\n\n")
        f.write("| Day | Avg Return | Win Rate |\n")
        f.write("|-----|------------|----------|\n")
        
        for day_stat in time_pat.get('day_stats', []):
            f.write(f"| {day_stat['day']} | {day_stat['avg_return']:+.3f}% | {day_stat['win_rate']:.1f}% |\n")
        
        f.write(f"\n**Best Day**: {time_pat.get('best_day', 'Unknown')}\n")
        f.write(f"**Worst Day**: {time_pat.get('worst_day', 'Unknown')}\n\n")
        
        f.write("---\n\n")
    
    def _write_volatility_profile(self, f, profile):
        vol = profile['volatility_profile']
        
        f.write("## 📉 Volatility Profile\n\n")
        
        f.write(f"**Current State**: **{vol.get('volatility_state', 'UNKNOWN')}**\n\n")
        
        f.write(f"- Average ATR: {vol.get('avg_atr_pct', 0):.2f}%\n")
        f.write(f"- Current ATR: {vol.get('current_atr_pct', 0):.2f}%\n\n")
        
        f.write("### Regime Distribution\n\n")
        f.write(f"- High Volatility Days: {vol.get('high_vol_days_pct', 0):.1f}%\n")
        f.write(f"- Normal Volatility Days: {vol.get('normal_vol_days_pct', 0):.1f}%\n")
        f.write(f"- Low Volatility Days: {vol.get('low_vol_days_pct', 0):.1f}%\n\n")
        
        if vol.get('regime_performance'):
            f.write("### Performance by Volatility Regime\n\n")
            f.write("| Regime | Win Rate | Avg Return | Days |\n")
            f.write("|--------|----------|------------|------|\n")
            
            for regime_name, stats in vol['regime_performance'].items():
                f.write(f"| {regime_name} | {stats['win_rate']:.1f}% | {stats['avg_return']:+.3f}% | {stats['days']} |\n")
            
            f.write("\n")
        
        f.write("---\n\n")
    
    def _write_trading_playbook(self, f, profile):
        playbook = profile['trading_playbook']
        
        f.write("## 🎯 ACTIONABLE TRADING PLAYBOOK\n\n")
        
        f.write("> [!WARNING]\n")
        f.write("> **Critical Trading Rules** - Follow these to maximize edge:\n\n")
        
        for rule in playbook.get('rules', []):
            f.write(f"{rule}\n")
        
        f.write("\n### Recommended Parameters\n\n")
        f.write(f"- **Stop Loss**: {playbook.get('optimal_sl_pct', 2.0):.1f}%\n")
        f.write(f"- **Take Profit**: {playbook.get('optimal_tp_multiplier', 3.0):.1f}x Risk\n")
        f.write(f"- **Position Size Multiplier**: {playbook.get('position_size_multiplier', 1.0):.1f}x\n")
        f.write(f"- **Preferred Timeframe**: {playbook.get('preferred_timeframe', '4H')}\n\n")
        
        f.write("---\n\n")
    
    def _write_footer(self, f):
        f.write("## 📌 Disclaimer\n\n")
        f.write("*This intelligence report is generated by quantitative analysis of historical price data. ")
        f.write("Past performance does not guarantee future results. Always use proper risk management.*\n\n")
        f.write("---\n\n")
        f.write(f"*Generated by Titan Advanced Symbol Intelligence Profiler v2.0*\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Titan Advanced Symbol Profiler")
    parser.add_argument("symbol", help="Symbol to profile (e.g., GOLD, BTCUSD)")
    
    args = parser.parse_args()
    
    profiler = AdvancedSymbolProfiler(args.symbol)
    report_path = profiler.generate_profile()
    
    print(f"\nREPORT_PATH:{report_path}")

if __name__ == "__main__":
    main()
