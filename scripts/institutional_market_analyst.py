"""
Institutional Market Analyst - Comprehensive Multi-Timeframe Analysis
Generates professional-grade market analysis reports across all timeframes
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Technical Analysis
from scipy.signal import argrelextrema
from collections import defaultdict

# Pattern Recognition
try:
    from technical_patterns import detect_candlestick_patterns, detect_chart_patterns, detect_divergences
except ImportError:
    # Manual definition if not found (shouldn't happen in our repo)
    def detect_candlestick_patterns(df): return []
    def detect_chart_patterns(df): return []
    def detect_divergences(df): return []


class InstitutionalMarketAnalyst:
    """Professional-grade multi-timeframe market analysis engine"""
    
    TIMEFRAMES = {
        '1M': mt5.TIMEFRAME_M1,
        '5M': mt5.TIMEFRAME_M5,
        '15M': mt5.TIMEFRAME_M15,
        '30M': mt5.TIMEFRAME_M30,
        '1H': mt5.TIMEFRAME_H1,
        '4H': mt5.TIMEFRAME_H4,
        '1D': mt5.TIMEFRAME_D1,
        '1W': mt5.TIMEFRAME_W1,
    }
    
    BARS_TO_FETCH = {
        '1M': 500,
        '5M': 500,
        '15M': 500,
        '30M': 500,
        '1H': 500,
        '4H': 1000,
        '1D': 500,
        '1W': 200,
    }
    
    def __init__(self, symbol: str, generate_charts: bool = True):
        self.symbol = symbol
        self.data = {}
        self.analysis = {}
        self.generate_charts = generate_charts and CHARTS_AVAILABLE
        self.chart_paths = {}
        
    def initialize_mt5(self):
        """Initialize MT5 connection"""
        if not mt5.initialize():
            raise ConnectionError(f"MT5 initialization failed: {mt5.last_error()}")
        
        # Verify symbol exists
        symbol_info = mt5.symbol_info(self.symbol)
        if symbol_info is None:
            mt5.shutdown()
            raise ValueError(f"Symbol {self.symbol} not found in MT5")
        
        # Enable symbol for trading
        if not symbol_info.visible:
            if not mt5.symbol_select(self.symbol, True):
                mt5.shutdown()
                raise ValueError(f"Failed to enable symbol {self.symbol}")
    
    def fetch_data(self):
        """Fetch data for all timeframes"""
        print(f"📊 Fetching data for {self.symbol}...")
        
        for tf_name, tf_value in self.TIMEFRAMES.items():
            bars = self.BARS_TO_FETCH[tf_name]
            rates = mt5.copy_rates_from_pos(self.symbol, tf_value, 0, bars)
            
            if rates is None or len(rates) == 0:
                print(f"⚠️  No data for {tf_name}")
                continue
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calculate technical indicators
            df = self._calculate_indicators(df)
            
            self.data[tf_name] = df
            print(f"✅ {tf_name}: {len(df)} bars")
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators"""
        
        # Moving Averages
        df['SMA_9'] = df['close'].rolling(9).mean()
        df['SMA_21'] = df['close'].rolling(21).mean()
        df['SMA_55'] = df['close'].rolling(55).mean()
        df['SMA_200'] = df['close'].rolling(200).mean()
        
        df['EMA_9'] = df['close'].ewm(span=9, adjust=False).mean()
        df['EMA_21'] = df['close'].ewm(span=21, adjust=False).mean()
        df['EMA_55'] = df['close'].ewm(span=55, adjust=False).mean()
        
        # RSI
        df['RSI'] = self._calculate_rsi(df['close'], 14)
        
        # ATR for volatility
        df['ATR'] = self._calculate_atr(df)
        
        # ADX for trend strength
        df['ADX'] = self._calculate_adx(df)
        
        # Volume analysis
        df['Volume_SMA_20'] = df['tick_volume'].rolling(20).mean()
        df['Volume_Ratio'] = df['tick_volume'] / df['Volume_SMA_20']
        
        # Bollinger Bands
        df['BB_Middle'] = df['close'].rolling(20).mean()
        bb_std = df['close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Middle'] + (2 * bb_std)
        df['BB_Lower'] = df['BB_Middle'] - (2 * bb_std)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ADX"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        
        tr = self._calculate_atr(df, period)
        
        plus_di = 100 * (plus_dm.ewm(alpha=1/period).mean() / tr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period).mean() / tr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.ewm(alpha=1/period).mean()
        
        return adx
    
    def analyze_timeframe(self, tf_name: str):
        """Perform comprehensive analysis for a single timeframe"""
        
        if tf_name not in self.data:
            return None
        
        df = self.data[tf_name]
        latest = df.iloc[-1]
        
        analysis = {
            'timeframe': tf_name,
            'current_price': latest['close'],
            'change_pct': ((latest['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close'] * 100),
            'rsi': latest['RSI'],
            'atr': latest['ATR'],
            'adx': latest['ADX'],
            'volume_ratio': latest['Volume_Ratio'],
        }
        
        # Trend Analysis
        analysis['trend'] = self._analyze_trend(df)
        analysis['ma_alignment'] = self._analyze_ma_alignment(df)
        
        # Support/Resistance
        analysis['support_resistance'] = self._find_support_resistance(df)
        
        # Patterns
        analysis['patterns'] = self._detect_patterns(df)
        
        # Candlestick Patterns (for latest bar)
        analysis['candlestick'] = self._detect_candlestick_patterns(df)
        
        # Order Flow Analysis
        analysis['order_flow'] = self._analyze_order_flow(df)
        
        # Divergences
        analysis['divergences'] = self._detect_divergences(df)
        
        # Fibonacci Levels
        analysis['fibonacci'] = self._calculate_fibonacci(df)
        
        # Market Regime
        analysis['regime'] = self._detect_market_regime(df)
        
        # Trade Signal
        analysis['signal'] = self._generate_signal(df, analysis)
        
        return analysis
    
    def _analyze_trend(self, df: pd.DataFrame) -> dict:
        """Analyze trend structure"""
        
        # Get last 50 bars for trend
        recent = df.tail(50)
        
        # Calculate trend slope
        prices = recent['close'].values
        x = np.arange(len(prices))
        slope = np.polyfit(x, prices, 1)[0]
        
        # Identify higher highs and higher lows
        highs = argrelextrema(recent['high'].values, np.greater, order=5)[0]
        lows = argrelextrema(recent['low'].values, np.less, order=5)[0]
        
        hh_trend = "UPTREND" if len(highs) >= 2 and recent['high'].iloc[highs[-1]] > recent['high'].iloc[highs[-2]] else "N/A"
        hl_trend = "UPTREND" if len(lows) >= 2 and recent['low'].iloc[lows[-1]] > recent['low'].iloc[lows[-2]] else "N/A"
        
        if slope > 0.1:
            direction = "🟢 STRONG UPTREND"
        elif slope > 0:
            direction = "🟢 WEAK UPTREND"
        elif slope < -0.1:
            direction = "🔴 STRONG DOWNTREND"
        elif slope < 0:
            direction = "🔴 WEAK DOWNTREND"
        else:
            direction = "🟡 SIDEWAYS"
        
        return {
            'direction': direction,
            'slope': slope,
            'structure': f"HH: {hh_trend}, HL: {hl_trend}",
            'swing_highs': highs.tolist() if len(highs) > 0 else [],
            'swing_lows': lows.tolist() if len(lows) > 0 else [],
        }
    
    def _analyze_ma_alignment(self, df: pd.DataFrame) -> str:
        """Check moving average alignment"""
        latest = df.iloc[-1]
        
        price = latest['close']
        sma9 = latest['SMA_9']
        sma21 = latest['SMA_21']
        sma55 = latest['SMA_55']
        sma200 = latest['SMA_200']
        
        if pd.isna(sma200):
            return "Insufficient data"
        
        if price > sma9 > sma21 > sma55 > sma200:
            return "🟢 PERFECT BULLISH (Golden Alignment)"
        elif price < sma9 < sma21 < sma55 < sma200:
            return "🔴 PERFECT BEARISH (Death Alignment)"
        elif price > sma200:
            return "🟢 BULLISH (Above 200 SMA)"
        elif price < sma200:
            return "🔴 BEARISH (Below 200 SMA)"
        else:
            return "🟡 MIXED"
    
    def _find_support_resistance(self, df: pd.DataFrame) -> dict:
        """Identify key support and resistance levels"""
        
        # Get recent swing points
        recent = df.tail(200)
        
        highs_idx = argrelextrema(recent['high'].values, np.greater, order=10)[0]
        lows_idx = argrelextrema(recent['low'].values, np.less, order=10)[0]
        
        resistance_levels = recent['high'].iloc[highs_idx].values if len(highs_idx) > 0 else []
        support_levels = recent['low'].iloc[lows_idx].values if len(lows_idx) > 0 else []
        
        # Cluster levels (within 0.5% of each other)
        current_price = df.iloc[-1]['close']
        
        resistance_levels = self._cluster_levels(resistance_levels, current_price)
        support_levels = self._cluster_levels(support_levels, current_price)
        
        # Sort and get closest levels
        resistance_levels = sorted([r for r in resistance_levels if r > current_price])[:3]
        support_levels = sorted([s for s in support_levels if s < current_price], reverse=True)[:3]
        
        return {
            'resistance': resistance_levels,
            'support': support_levels,
        }
    
    def _cluster_levels(self, levels: np.ndarray, reference_price: float) -> list:
        """Cluster levels that are close together"""
        if len(levels) == 0:
            return []
        
        clustered = []
        levels = sorted(levels)
        
        current_cluster = [levels[0]]
        
        for level in levels[1:]:
            if abs(level - current_cluster[-1]) / reference_price < 0.005:  # Within 0.5%
                current_cluster.append(level)
            else:
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]
        
        clustered.append(np.mean(current_cluster))
        
        return clustered
    
    def _detect_candlestick_patterns(self, df: pd.DataFrame) -> list:
        """Detect candlestick patterns using shared module"""
        return detect_candlestick_patterns(df)
    
    def _detect_chart_patterns(self, df: pd.DataFrame) -> list:
        """Detect chart patterns using shared module"""
        patterns = detect_chart_patterns(df)
        return patterns if patterns else ["No major patterns detected"]
    
    def _detect_patterns(self, df: pd.DataFrame) -> list:
        """Detect all patterns (candlestick + chart)"""
        candle_patterns = self._detect_candlestick_patterns(df)
        chart_patterns = self._detect_chart_patterns(df)
        return candle_patterns + chart_patterns
    
    def _detect_divergences(self, df: pd.DataFrame) -> list:
        """Detect price/RSI divergences using shared module"""
        divergences = detect_divergences(df)
        return divergences if divergences else ["No divergences detected"]
    
    def _analyze_order_flow(self, df: pd.DataFrame) -> dict:
        """Analyze order flow and identify likely stop/limit clusters"""
        
        latest = df.iloc[-1]
        recent = df.tail(50)
        
        current_price = latest['close']
        atr = latest['ATR']
        
        # Find swing highs and lows (likely stop areas)
        highs_idx = argrelextrema(recent['high'].values, np.greater, order=5)[0]
        lows_idx = argrelextrema(recent['low'].values, np.less, order=5)[0]
        
        # Stop loss clusters (above swing highs for shorts, below swing lows for longs)
        stop_clusters_above = recent['high'].iloc[highs_idx].values if len(highs_idx) > 0 else []
        stop_clusters_below = recent['low'].iloc[lows_idx].values if len(lows_idx) > 0 else []
        
        # Filter to relevant stops (within 3 ATR)
        stop_clusters_above = [s for s in stop_clusters_above if s > current_price and s < current_price + (3 * atr)]
        stop_clusters_below = [s for s in stop_clusters_below if s < current_price and s > current_price - (3 * atr)]
        
        # Round number clusters (psychological levels)
        round_numbers = []
        price_magnitude = 10 ** (len(str(int(current_price))) - 2)  # e.g., 100 for prices ~4400
        
        for i in range(-3, 4):
            round_num = round(current_price / price_magnitude) * price_magnitude + (i * price_magnitude)
            if abs(round_num - current_price) < (3 * atr):
                round_numbers.append(round_num)
        
        return {
            'sell_stops_above': sorted(stop_clusters_above)[:3],  # Top 3
            'buy_stops_below': sorted(stop_clusters_below, reverse=True)[:3],  # Top 3
            'round_numbers': sorted(round_numbers),
        }
    
    def _calculate_fibonacci(self, df: pd.DataFrame) -> dict:
        """Calculate Fibonacci retracement levels"""
        
        recent = df.tail(200)
        
        # Find major swing high and low
        swing_high = recent['high'].max()
        swing_low = recent['low'].min()
        
        diff = swing_high - swing_low
        
        fib_levels = {
            '0.0%': swing_high,
            '23.6%': swing_high - (0.236 * diff),
            '38.2%': swing_high - (0.382 * diff),
            '50.0%': swing_high - (0.500 * diff),
            '61.8%': swing_high - (0.618 * diff),
            '78.6%': swing_high - (0.786 * diff),
            '100.0%': swing_low,
        }
        
        # Extension levels
        fib_levels['161.8%'] = swing_high + (0.618 * diff)
        fib_levels['261.8%'] = swing_high + (1.618 * diff)
        
        return fib_levels
    
    def _detect_market_regime(self, df: pd.DataFrame) -> str:
        """Detect current market regime"""
        
        latest = df.iloc[-1]
        recent = df.tail(50)
        
        adx = latest['ADX']
        atr = latest['ATR']
        price_range = (recent['high'].max() - recent['low'].min()) / recent['close'].iloc[-1]
        
        if pd.isna(adx):
            return "🟡 UNKNOWN (Insufficient data)"
        
        # Trending market
        if adx > 25 and price_range > 0.02:
            return "📈 STRONG TRENDING"
        elif adx > 20:
            return "📊 TRENDING"
        
        # Ranging market
        elif price_range < 0.015:
            return "📦 TIGHT RANGE"
        elif adx < 20:
            return "🔄 RANGING/CONSOLIDATION"
        
        return "🟡 TRANSITIONAL"
    
    def _generate_signal(self, df: pd.DataFrame, analysis: dict) -> dict:
        """Generate trading signal based on analysis"""
        
        latest = df.iloc[-1]
        rsi = latest['RSI']
        price = latest['close']
        
        # Signal strength score
        score = 0
        reasons = []
        
        # Trend alignment
        if "UPTREND" in analysis['trend']['direction']:
            score += 2
            reasons.append("Uptrend confirmed")
        elif "DOWNTREND" in analysis['trend']['direction']:
            score -= 2
            reasons.append("Downtrend confirmed")
        
        # MA alignment
        if "PERFECT BULLISH" in analysis['ma_alignment']:
            score += 2
            reasons.append("Perfect MA alignment (bullish)")
        elif "PERFECT BEARISH" in analysis['ma_alignment']:
            score -= 2
            reasons.append("Perfect MA alignment (bearish)")
        
        # RSI
        if rsi < 30:
            score += 1
            reasons.append("RSI oversold")
        elif rsi > 70:
            score -= 1
            reasons.append("RSI overbought")
        
        # Divergences
        for div in analysis['divergences']:
            if "BULLISH" in div:
                score += 2
                reasons.append("Bullish divergence")
            elif "BEARISH" in div:
                score -= 2
                reasons.append("Bearish divergence")
        
        # Determine signal
        if score >= 3:
            signal = "🟢 STRONG BUY"
        elif score >= 1:
            signal = "🟢 BUY"
        elif score <= -3:
            signal = "🔴 STRONG SELL"
        elif score <= -1:
            signal = "🔴 SELL"
        else:
            signal = "🟡 NEUTRAL"
        
        return {
            'signal': signal,
            'score': score,
            'reasons': reasons,
        }
    
    def find_confluence_zones(self):
        """Find zones where multiple levels from different timeframes overlap"""
        
        all_levels = defaultdict(list)
        
        for tf_name, analysis in self.analysis.items():
            if analysis is None:
                continue
            
            sr = analysis.get('support_resistance', {})
            
            for level in sr.get('support', []):
                all_levels[round(level, 1)].append(f"{tf_name} Support")
            
            for level in sr.get('resistance', []):
                all_levels[round(level, 1)].append(f"{tf_name} Resistance")
        
        # Find confluence (3+ levels within 0.5%)
        confluence_zones = []
        current_price = self.data['1H'].iloc[-1]['close'] if '1H' in self.data else 0
        
        for level, sources in all_levels.items():
            if len(sources) >= 3:
                confluence_zones.append({
                    'level': level,
                    'count': len(sources),
                    'sources': sources,
                    'distance_pct': abs(level - current_price) / current_price * 100,
                })
        
        return sorted(confluence_zones, key=lambda x: x['distance_pct'])[:5]
    
    def generate_report(self) -> str:
        """Generate comprehensive markdown report"""
        
        # Analyze all timeframes
        print("\n🔍 Analyzing all timeframes...")
        for tf_name in self.TIMEFRAMES.keys():
            self.analysis[tf_name] = self.analyze_timeframe(tf_name)
        
        # Get current price
        current_price = self.data['1H'].iloc[-1]['close'] if '1H' in self.data else 0
        change_24h = self.analysis['1D']['change_pct'] if '1D' in self.analysis and self.analysis['1D'] else 0
        
        # Build report
        report = f"""# {self.symbol} - INSTITUTIONAL MARKET ANALYSIS
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC+5:30')}
**Current Price**: {current_price:.2f} | **24H Change**: {change_24h:+.2f}%

---

## 📊 EXECUTIVE SUMMARY

"""
        
        # Multi-timeframe trend summary
        report += "### Multi-Timeframe Trend Alignment\n\n"
        report += "| Timeframe | Trend | RSI | ADX | Regime | Signal |\n"
        report += "|-----------|-------|-----|-----|--------|--------|\n"
        
        for tf_name in ['1W', '1D', '4H', '1H', '30M', '15M', '5M', '1M']:
            analysis = self.analysis.get(tf_name)
            if analysis:
                trend_emoji = analysis['trend']['direction'].split()[0]
                signal_emoji = analysis['signal']['signal'].split()[0]
                
                report += f"| **{tf_name}** | {trend_emoji} {analysis['trend']['direction'].replace('🟢 ', '').replace('🔴 ', '').replace('🟡 ', '')} | "
                report += f"{analysis['rsi']:.1f} | {analysis['adx']:.1f} | "
                report += f"{analysis['regime']} | {signal_emoji} {analysis['signal']['signal'].replace('🟢 ', '').replace('🔴 ', '').replace('🟡 ', '')} |\n"
        
        report += "\n---\n\n"
        
        # Detailed timeframe analysis
        report += "## 🔍 DETAILED TIMEFRAME ANALYSIS\n\n"
        
        priority_timeframes = ['1W', '1D', '4H', '1H', '15M']
        
        for tf_name in priority_timeframes:
            analysis = self.analysis.get(tf_name)
            if not analysis:
                continue
            
            importance = "⭐⭐⭐" if tf_name in ['1W', '1D', '4H'] else "⭐⭐" if tf_name == '1H' else "⭐"
            
            report += f"### {tf_name} Timeframe {importance}\n\n"
            
            # Trend
            report += f"**Trend**: {analysis['trend']['direction']}\n"
            report += f"- Structure: {analysis['trend']['structure']}\n"
            report += f"- MA Alignment: {analysis['ma_alignment']}\n"
            report += f"- Market Regime: {analysis['regime']}\n\n"
            
            # Technical Indicators
            report += f"**Technical Indicators**:\n"
            report += f"- RSI: {analysis['rsi']:.2f}"
            if analysis['rsi'] > 70:
                report += " (⚠️ Overbought)"
            elif analysis['rsi'] < 30:
                report += " (✅ Oversold)"
            report += "\n"
            report += f"- ADX: {analysis['adx']:.2f} (Trend strength)\n"
            report += f"- ATR: {analysis['atr']:.2f} (Volatility)\n\n"
            
            # Support/Resistance
            sr = analysis['support_resistance']
            if sr['resistance']:
                report += f"**Resistance Levels**: {', '.join([f'{r:.2f}' for r in sr['resistance']])}\n"
            if sr['support']:
                report += f"**Support Levels**: {', '.join([f'{s:.2f}' for s in sr['support']])}\n"
            report += "\n"
            
            # Patterns
            if analysis['patterns']:
                report += f"**Patterns Detected**:\n"
                for pattern in analysis['patterns']:
                    report += f"- {pattern}\n"
                report += "\n"
            
            # Divergences
            if analysis['divergences'] and "No divergences" not in analysis['divergences'][0]:
                report += f"**⚡ DIVERGENCES**:\n"
                for div in analysis['divergences']:
                    report += f"- {div}\n"
                report += "\n"
            
            # Fibonacci (only for major timeframes)
            if tf_name in ['1D', '4H', '1H']:
                fib = analysis['fibonacci']
                report += f"**Fibonacci Retracement Levels** (from recent swing):\n"
                for level_name, level_value in list(fib.items())[:7]:  # Main retracement levels
                    report += f"- {level_name}: {level_value:.2f}\n"
                report += "\n"
            
            # Signal
            sig = analysis['signal']
            report += f"**Trading Signal**: {sig['signal']} (Score: {sig['score']})\n"
            if sig['reasons']:
                report += f"**Reasons**:\n"
                for reason in sig['reasons']:
                    report += f"- {reason}\n"
            
            report += "\n---\n\n"
        
        # Confluence Zones
        report += "## 🎯 CONFLUENCE ZONES (High Probability Areas)\n\n"
        confluence = self.find_confluence_zones()
        
        if confluence:
            report += "Zones where multiple support/resistance levels from different timeframes overlap:\n\n"
            report += "| Level | Confluence Count | Sources | Distance from Price |\n"
            report += "|-------|------------------|---------|---------------------|\n"
            
            for zone in confluence:
                sources_str = ", ".join(zone['sources'][:3])  # Show first 3
                if len(zone['sources']) > 3:
                    sources_str += f" +{len(zone['sources']) - 3} more"
                
                report += f"| **{zone['level']:.2f}** | {zone['count']} | {sources_str} | {zone['distance_pct']:.2f}% |\n"
        else:
            report += "*No major confluence zones identified in current market structure.*\n"
        
        report += "\n---\n\n"
        
        # Trading Strategy Recommendations
        report += "## 💡 TRADING STRATEGY RECOMMENDATIONS\n\n"
        
        # Overall bias from higher timeframes
        weekly_signal = self.analysis.get('1W', {}).get('signal', {}).get('signal', 'NEUTRAL')
        daily_signal = self.analysis.get('1D', {}).get('signal', {}).get('signal', 'NEUTRAL')
        h4_signal = self.analysis.get('4H', {}).get('signal', {}).get('signal', 'NEUTRAL')
        
        report += f"### 🎯 Primary Bias\n\n"
        report += f"- **Weekly**: {weekly_signal}\n"
        report += f"- **Daily**: {daily_signal}\n"
        report += f"- **4H**: {h4_signal}\n\n"
        
        # Determine overall recommendation
        bullish_count = sum([1 for s in [weekly_signal, daily_signal, h4_signal] if 'BUY' in s])
        bearish_count = sum([1 for s in [weekly_signal, daily_signal, h4_signal] if 'SELL' in s])
        
        if bullish_count >= 2:
            report += "> [!IMPORTANT]\n"
            report += "> **PRIMARY BIAS: BULLISH** ✅\n"
            report += "> Higher timeframes show bullish structure. Look for buying opportunities on pullbacks.\n\n"
        elif bearish_count >= 2:
            report += "> [!WARNING]\n"
            report += "> **PRIMARY BIAS: BEARISH** ⚠️\n"
            report += "> Higher timeframes show bearish structure. Look for selling opportunities on rallies.\n\n"
        else:
            report += "> [!NOTE]\n"
            report += "> **PRIMARY BIAS: NEUTRAL** 🟡\n"
            report += "> Mixed signals across timeframes. Wait for clearer directional bias.\n\n"
        
        # Key levels for trading
        report += "### 📈 Key Levels to Watch\n\n"
        
        # Get levels from 1D and 4H
        daily_sr = self.analysis.get('1D', {}).get('support_resistance', {})
        h4_sr = self.analysis.get('4H', {}).get('support_resistance', {})
        
        all_resistance = []
        all_support = []
        
        if daily_sr:
            all_resistance.extend(daily_sr.get('resistance', []))
            all_support.extend(daily_sr.get('support', []))
        
        if h4_sr:
            all_resistance.extend(h4_sr.get('resistance', []))
            all_support.extend(h4_sr.get('support', []))
        
        all_resistance = sorted(list(set([round(r, 1) for r in all_resistance])))[:3]
        all_support = sorted(list(set([round(s, 1) for s in all_support])), reverse=True)[:3]
        
        if all_resistance:
            report += f"**Resistance**: {' → '.join([f'{r:.2f}' for r in all_resistance])}\n"
        if all_support:
            report += f"**Support**: {' → '.join([f'{s:.2f}' for s in all_support])}\n"
        
        report += "\n### ⚠️ Risk Management\n\n"
        report += "- **Position Size**: Risk no more than 1-2% of capital per trade\n"
        report += "- **Stop Loss**: Place below key support (for longs) or above key resistance (for shorts)\n"
        report += "- **Take Profit**: Target next major resistance/support level or use trailing stops\n"
        
        report += "\n---\n\n"
        
        # Timestamp
        report += f"*Analysis generated by Institutional Market Analyst v1.0 at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return report
    
    def run_analysis(self, output_dir: str = "analysis"):
        """Run complete analysis and save report"""
        
        try:
            self.initialize_mt5()
            self.fetch_data()
            
            report = self.generate_report()
            
            # Save report
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output_path / f"{self.symbol}_{timestamp}.md"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n✅ Analysis complete! Report saved to: {filename}")
            
            return str(filename)
            
        finally:
            mt5.shutdown()


def main():
    if len(sys.argv) < 2:
        print("Usage: python institutional_market_analyst.py <SYMBOL>")
        print("Example: python institutional_market_analyst.py XAUUSD")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    
    print(f"\n{'='*60}")
    print(f"  INSTITUTIONAL MARKET ANALYST")
    print(f"  Symbol: {symbol}")
    print(f"{'='*60}\n")
    
    analyst = InstitutionalMarketAnalyst(symbol)
    report_path = analyst.run_analysis()
    
    print(f"\n📄 Opening report...\n")
    
    # Return path for workflow to open
    print(f"REPORT_PATH:{report_path}")


if __name__ == "__main__":
    main()
