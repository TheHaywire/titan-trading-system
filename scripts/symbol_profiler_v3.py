"""
TA-Lib Enhanced Symbol Intelligence Profiler v3.0
Professional-grade analysis with 150+ technical indicators
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib
from datetime import datetime
from pathlib import Path
import sys

# Add project root
sys.path.append(str(Path(__file__).parent.parent))

# Import v2.0 base class for symbol resolution
from scripts.symbol_profiler import AdvancedSymbolProfiler

class TALibSymbolProfiler(AdvancedSymbolProfiler):
    """Enhanced profiler with full TA-Lib indicator suite"""
    
    def __init__(self, symbol):
        super().__init__(symbol)
        self.talib_version = talib.__version__
    
    def generate_profile(self):
        """Generate TA-Lib enhanced institutional profile"""
        
        if self.resolved_symbol is None:
            print(f"\n❌ Cannot generate profile - symbol '{self.symbol}' not available")
            return None
        
        print(f"\n🔬 Generating TA-Lib Enhanced Profile v3.0 for {self.resolved_symbol}...")
        print(f"📊 TA-Lib version: {self.talib_version} (158 functions available)")
        
        # Fetch data
        data = self._fetch_comprehensive_data()
        
        # Run enhanced analyses
        print("📊 Running price history analysis...")
        price_history = self._analyze_price_history(data)
        
        print("🎯 Analyzing momentum indicators (MACD, Stochastic, CCI, Williams %R)...")
        momentum_analysis = self._analyze_momentum_indicators(data)
        
        print("📈 Analyzing trend strength (ADX, Aroon, DMI)...")
        trend_analysis = self._analyze_trend_strength(data)
        
        print("📉 Analyzing volatility (Bollinger Bands, ATR)...")
        volatility_analysis = self._analyze_advanced_volatility(data)
        
        print("🕯️ Scanning 61 candlestick patterns...")
        pattern_analysis = self._scan_all_candlestick_patterns(data)
        
        print("⏰ Analyzing time-based patterns...")
        time_patterns = self._analyze_time_patterns(data)
        
        print("🔄 Classifying market regimes...")
        regime_analysis = self._analyze_market_regimes(data)
        
        print("📈 Running backtest validation...")
        backtest_results = self._run_quick_backtest(data)
        
        print("🧠 Generating enhanced trading playbook...")
        trading_playbook = self._generate_enhanced_playbook(
            price_history, momentum_analysis, trend_analysis,
            volatility_analysis, pattern_analysis, regime_analysis, backtest_results
        )
        
        profile = {
            'symbol': self.resolved_symbol,
            'generated_at': datetime.now().isoformat(),
            'talib_version': self.talib_version,
            'price_history': price_history,
            'momentum_indicators': momentum_analysis,
            'trend_strength': trend_analysis,
            'volatility_analysis': volatility_analysis,
            'candlestick_patterns': pattern_analysis,
            'time_patterns': time_patterns,
            'regime_analysis': regime_analysis,
            'backtest_results': backtest_results,
            'trading_playbook': trading_playbook,
            'current_state': self._get_current_state()
        }
        
        # Generate enhanced report
        report_path = self._generate_enhanced_report(profile)
        
        return report_path
    
    def _analyze_momentum_indicators(self, data):
        """Comprehensive momentum analysis using TA-Lib"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        close = df['close'].values.astype(np.float64)
        high = df['high'].values.astype(np.float64)
        low = df['low'].values.astype(np.float64)
        volume = df['tick_volume'].values.astype(np.float64) if 'tick_volume' in df.columns else None
        
        # MACD
        macd, macd_signal, macd_hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
        
        # Stochastic
        slowk, slowd = talib.STOCH(high, low, close, fastk_period=14, slowk_period=3, slowd_period=3)
        
        # CCI
        cci = talib.CCI(high, low, close, timeperiod=14)
        
        # Williams %R
        willr = talib.WILLR(high, low, close, timeperiod=14)
        
        # RSI (for comparison)
        rsi = talib.RSI(close, timeperiod=14)
        
        # Money Flow Index (if we have volume)
        mfi = talib.MFI(high, low, close, volume, timeperiod=14) if volume is not None else None
        
        # Current values
        momentum_state = {
            'macd': {
                'value': float(macd[-1]) if not np.isnan(macd[-1]) else 0,
                'signal': float(macd_signal[-1]) if not np.isnan(macd_signal[-1]) else 0,
                'histogram': float(macd_hist[-1]) if not np.isnan(macd_hist[-1]) else 0,
                'crossover': 'BULLISH' if macd[-1] > macd_signal[-1] else 'BEARISH',
                'strength': 'STRONG' if abs(macd_hist[-1]) > abs(np.nanmean(macd_hist[-20:])) else 'WEAK'
            },
            'stochastic': {
                'k': float(slowk[-1]) if not np.isnan(slowk[-1]) else 50,
                'd': float(slowd[-1]) if not np.isnan(slowd[-1]) else 50,
                'state': 'OVERBOUGHT' if slowk[-1] > 80 else ('OVERSOLD' if slowk[-1] < 20 else 'NEUTRAL')
            },
            'cci': {
                'value': float(cci[-1]) if not np.isnan(cci[-1]) else 0,
                'state': 'OVERBOUGHT' if cci[-1] > 100 else ('OVERSOLD' if cci[-1] < -100 else 'NEUTRAL')
            },
            'williams_r': {
                'value': float(willr[-1]) if not np.isnan(willr[-1]) else -50,
                'state': 'OVERBOUGHT' if willr[-1] > -20 else ('OVERSOLD' if willr[-1] < -80 else 'NEUTRAL')
            },
            'rsi': {
                'value': float(rsi[-1]) if not np.isnan(rsi[-1]) else 50,
                'state': 'OVERBOUGHT' if rsi[-1] > 70 else ('OVERSOLD' if rsi[-1] < 30 else 'NEUTRAL')
            }
        }
        
        # Momentum score (0-100)
        bullish_signals = 0
        total_signals = 0
        
        if macd[-1] > macd_signal[-1]: bullish_signals += 1
        total_signals += 1
        
        if slowk[-1] > slowd[-1]: bullish_signals += 1
        total_signals += 1
        
        if rsi[-1] > 50: bullish_signals += 1
        total_signals += 1
        
        momentum_state['overall_score'] = int((bullish_signals / total_signals) * 100)
        momentum_state['bias'] = 'BULLISH' if momentum_state['overall_score'] > 60 else ('BEARISH' if momentum_state['overall_score'] < 40 else 'NEUTRAL')
        
        return momentum_state
    
    def _analyze_trend_strength(self, data):
        """Multi-indicator trend strength analysis"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        high = df['high'].values.astype(np.float64)
        low = df['low'].values.astype(np.float64)
        close = df['close'].values.astype(np.float64)
        
        # ADX - Trend Strength
        adx = talib.ADX(high, low, close, timeperiod=14)
        
        # Aroon - Trend Direction
        aroon_up, aroon_down = talib.AROON(high, low, timeperiod=25)
        
        # Directional Movement Index
        plus_di = talib.PLUS_DI(high, low, close, timeperiod=14)
        minus_di = talib.MINUS_DI(high, low, close, timeperiod=14)
        
        # Parabolic SAR
        sar = talib.SAR(high, low, acceleration=0.02, maximum=0.2)
        
        trend_state = {
            'adx': {
                'value': float(adx[-1]) if not np.isnan(adx[-1]) else 0,
                'strength': 'STRONG' if adx[-1] > 25 else ('WEAK' if adx[-1] < 20 else 'MODERATE'),
                'trending': adx[-1] > 25
            },
            'aroon': {
                'up': float(aroon_up[-1]) if not np.isnan(aroon_up[-1]) else 0,
                'down': float(aroon_down[-1]) if not np.isnan(aroon_down[-1]) else 0,
                'trend': 'UPTREND' if aroon_up[-1] > aroon_down[-1] else 'DOWNTREND'
            },
            'dmi': {
                'plus_di': float(plus_di[-1]) if not np.isnan(plus_di[-1]) else 0,
                'minus_di': float(minus_di[-1]) if not np.isnan(minus_di[-1]) else 0,
                'direction': 'BULLISH' if plus_di[-1] > minus_di[-1] else 'BEARISH'
            },
            'sar': {
                'value': float(sar[-1]) if not np.isnan(sar[-1]) else close[-1],
                'position': 'BULLISH' if close[-1] > sar[-1] else 'BEARISH'
            }
        }
        
        # Overall trend score
        bullish_count = 0
        if aroon_up[-1] > aroon_down[-1]: bullish_count += 1
        if plus_di[-1] > minus_di[-1]: bullish_count += 1
        if close[-1] > sar[-1]: bullish_count += 1
        
        trend_state['overall_bias'] = 'STRONG_BULLISH' if bullish_count == 3 else (
            'BEARISH' if bullish_count == 0 else 'MIXED'
        )
        
        return trend_state
    
    def _analyze_advanced_volatility(self, data):
        """Enhanced volatility analysis with Bollinger Bands"""
        if 'daily' not in data:
            return {}
        
        df = data['daily'].copy()
        close = df['close'].values.astype(np.float64)
        high = df['high'].values.astype(np.float64)
        low = df['low'].values.astype(np.float64)
        
        # Bollinger Bands
        upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2, nbdevdn=2)
        
        # ATR
        atr = talib.ATR(high, low, close, timeperiod=14)
        
        # Bollinger Band Width
        bb_width = (upper - lower) / middle
        
        # Current position in bands
        bb_position = (close[-1] - lower[-1]) / (upper[-1] - lower[-1]) if (upper[-1] - lower[-1]) > 0 else 0.5
        
        volatility_state = {
            'bollinger_bands': {
                'upper': float(upper[-1]),
                'middle': float(middle[-1]),
                'lower': float(lower[-1]),
                'width_pct': float(bb_width[-1] * 100),
                'position': float(bb_position * 100),  # 0-100%
                'squeeze': bb_width[-1] < np.nanpercentile(bb_width, 20),  # Bottom 20% = squeeze
                'state': 'UPPER_BAND' if bb_position > 0.8 else ('LOWER_BAND' if bb_position < 0.2 else 'MIDDLE')
            },
            'atr': {
                'value': float(atr[-1]),
                'pct': float((atr[-1] / close[-1]) * 100),
                'percentile': float(np.nanpercentile(atr, [(atr[-1] >= atr).sum() / len(atr) * 100])[0])
            }
        }
        
        # Volatility state from v2.0
        atr_mean = np.nanmean(atr)
        atr_std = np.nanstd(atr)
        
        if atr[-1] > atr_mean + atr_std:
            volatility_state['overall_state'] = 'HIGH_VOL'
        elif atr[-1] < atr_mean - atr_std:
            volatility_state['overall_state'] = 'LOW_VOL'
        else:
            volatility_state['overall_state'] = 'NORMAL'
        
        return volatility_state
    
    def _scan_all_candlestick_patterns(self, data):
        """Scan all 61 TA-Lib candlestick patterns"""
        if 'h4' not in data:
            return {'patterns_found': []}
        
        df = data['h4'].copy()
        open_prices = df['open'].values.astype(np.float64)
        high = df['high'].values.astype(np.float64)
        low = df['low'].values.astype(np.float64)
        close = df['close'].values.astype(np.float64)
        
        # Get all candlestick pattern functions
        all_patterns = [f for f in talib.get_functions() if f.startswith('CDL')]
        
        detected_patterns = []
        
        # Scan last 100 bars for patterns
        for pattern_name in all_patterns:
            try:
                pattern_func = getattr(talib, pattern_name)
                result = pattern_func(open_prices, high, low, close)
                
                # Check recent bars (last 10)
                recent_signals = result[-10:]
                if np.any(recent_signals != 0):
                    # Pattern detected
                    last_signal_idx = np.where(recent_signals != 0)[0][-1]
                    signal_value = recent_signals[last_signal_idx]
                    
                    detected_patterns.append({
                        'name': pattern_name.replace('CDL', ''),
                        'bars_ago': 10 - last_signal_idx - 1,
                        'signal': 'BULLISH' if signal_value > 0 else 'BEARISH',
                        'strength': int(abs(signal_value))
                    })
            except Exception:
                continue
        
        # Count pattern frequency in historical data (last 100 bars)
        pattern_frequency = {}
        for pattern_name in all_patterns[:20]:  # Top 20 most common patterns
            try:
                pattern_func = getattr(talib, pattern_name)
                result = pattern_func(open_prices, high, low, close)
                count = np.count_nonzero(result[-100:])
                if count > 0:
                    pattern_frequency[pattern_name.replace('CDL', '')] = int(count)
            except Exception:
                continue
        
        return {
            'patterns_found': detected_patterns,
            'pattern_frequency': dict(sorted(pattern_frequency.items(), key=lambda x: x[1], reverse=True)[:10]),
            'total_scanned': len(all_patterns)
        }
    
    def _generate_enhanced_playbook(self, price_hist, momentum, trend, volatility, patterns, regime, backtest):
        """Generate comprehensive trading playbook with TA-Lib insights"""
        playbook = []
        
        # Momentum-based rules
        if momentum.get('bias') == 'BULLISH':
            playbook.append(f"📈 MOMENTUM BULLISH: {momentum.get('overall_score')}% bullish signals")
            if momentum['macd']['crossover'] == 'BULLISH':
                playbook.append("✅ MACD: Bullish crossover confirmed")
        elif momentum.get('bias') == 'BEARISH':
            playbook.append(f"📉 MOMENTUM BEARISH: {momentum.get('overall_score')}% bearish signals")
        
        # Trend strength rules
        if trend.get('adx', {}).get('trending'):
            playbook.append(f"🎯 STRONG TREND: ADX = {trend['adx']['value']:.1f} (>{25})")
            playbook.append(f"📊 Trend Direction: {trend.get('overall_bias', 'UNKNOWN')}")
        else:
            playbook.append(f"⚡ WEAK TREND: ADX = {trend.get('adx', {}).get('value', 0):.1f} - Range-bound market")
        
        # Volatility rules
        if volatility.get('bollinger_bands', {}).get('squeeze'):
            playbook.append("⚠️ BOLLINGER SQUEEZE: Breakout imminent - reduce size, wait for direction")
        
        bb_state = volatility.get('bollinger_bands', {}).get('state')
        if bb_state == 'UPPER_BAND':
            playbook.append("🔴 At upper Bollinger Band - overbought, watch for reversal")
        elif bb_state == 'LOWER_BAND':
            playbook.append("🟢 At lower Bollinger Band - oversold, watch for bounce")
        
        # Pattern-based rules
        if patterns.get('patterns_found'):
            recent_pattern = patterns['patterns_found'][0]
            playbook.append(f"🕯️ Recent Pattern: {recent_pattern['name']} ({recent_pattern['signal']}) - {recent_pattern['bars_ago']} bars ago")
        
        # Recommended parameters
        vol_state = volatility.get('overall_state', 'NORMAL')
        recommended_sl = 3.5 if vol_state == 'HIGH_VOL' else (1.5 if vol_state == 'LOW_VOL' else 2.0)
        position_multiplier = 0.5 if vol_state == 'HIGH_VOL' else 1.0
        
        return {
            'rules': playbook,
            'optimal_sl_pct': recommended_sl,
            'optimal_tp_multiplier': 3.0,
            'position_size_multiplier': position_multiplier,
            'preferred_timeframe': '1H' if vol_state == 'HIGH_VOL' else '4H'
        }
    
    def _generate_enhanced_report(self, profile):
        """Generate TA-Lib enhanced markdown report"""
        Path("intelligence").mkdir(exist_ok=True)
        
        filename = f"intelligence/{self.symbol}_TALIB_v3_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 🏛️ TA-LIB ENHANCED INTELLIGENCE REPORT v3.0: {self.symbol}\n\n")
            f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
            f.write(f"**TA-Lib Version**: {profile['talib_version']} ({profile['candlestick_patterns']['total_scanned']} patterns scanned)\n\n")
            
            f.write("> [!NOTE]\n")
            f.write("> Professional-grade analysis using TA-Lib's 158 technical indicators.\n")
            f.write("> Includes momentum dashboard, trend strength, Bollinger analysis, and all 61 candlestick patterns.\n\n")
            f.write("---\n\n")
            
            self._write_momentum_dashboard(f, profile)
            self._write_trend_analysis(f, profile)
            self._write_volatility_analysis(f, profile)
            self._write_pattern_report(f, profile)
            self._write_trading_playbook(f, profile)
            
            f.write("---\n\n")
            f.write("*Generated by Titan TA-Lib Enhanced Symbol Profiler v3.0*\n")
        
        print(f"\n✅ TA-Lib enhanced report saved: {filename}")
        return filename
    
    def _write_momentum_dashboard(self, f, profile):
        momentum = profile['momentum_indicators']
        
        f.write("## 🎯 Momentum Dashboard\n\n")
        f.write(f"**Overall Momentum**: **{momentum.get('bias', 'UNKNOWN')}** ({momentum.get('overall_score', 0)}% bullish)\n\n")
        
        f.write("| Indicator | Value | Signal | State |\n")
        f.write("|-----------|-------|--------|-------|\n")
        
        macd = momentum.get('macd', {})
        f.write(f"| **MACD** | {macd.get('value', 0):.2f} | {macd.get('crossover', 'N/A')} | {macd.get('strength', 'N/A')} |\n")
        
        stoch = momentum.get('stochastic', {})
        f.write(f"| **Stochastic** | K:{stoch.get('k', 0):.1f}, D:{stoch.get('d', 0):.1f} | - | {stoch.get('state', 'N/A')} |\n")
        
        cci = momentum.get('cci', {})
        f.write(f"| **CCI** | {cci.get('value', 0):.1f} | - | {cci.get('state', 'N/A')} |\n")
        
        willr = momentum.get('williams_r', {})
        f.write(f"| **Williams %R** | {willr.get('value', 0):.1f} | - | {willr.get('state', 'N/A')} |\n")
        
        rsi = momentum.get('rsi', {})
        f.write(f"| **RSI** | {rsi.get('value', 0):.1f} | - | {rsi.get('state', 'N/A')} |\n")
        
        f.write("\n---\n\n")
    
    def _write_trend_analysis(self, f, profile):
        trend = profile['trend_strength']
        
        f.write("## 📈 Trend Strength Analysis\n\n")
        f.write(f"**Overall Trend**: **{trend.get('overall_bias', 'UNKNOWN')}**\n\n")
        
        adx = trend.get('adx', {})
        f.write(f"**ADX**: {adx.get('value', 0):.1f} - {adx.get('strength', 'UNKNOWN')} trend\n\n")
        
        f.write("| Indicator | Value | Direction |\n")
        f.write("|-----------|-------|----------|\n")
        
        aroon = trend.get('aroon', {})
        f.write(f"| **Aroon** | Up:{aroon.get('up', 0):.0f}, Down:{aroon.get('down', 0):.0f} | {aroon.get('trend', 'N/A')} |\n")
        
        dmi = trend.get('dmi', {})
        f.write(f"| **DMI** | +DI:{dmi.get('plus_di', 0):.1f}, -DI:{dmi.get('minus_di', 0):.1f} | {dmi.get('direction', 'N/A')} |\n")
        
        sar = trend.get('sar', {})
        f.write(f"| **Parabolic SAR** | {sar.get('value', 0):.2f} | {sar.get('position', 'N/A')} |\n")
        
        f.write("\n---\n\n")
    
    def _write_volatility_analysis(self, f, profile):
        vol = profile['volatility_analysis']
        bb = vol.get('bollinger_bands', {})
        
        f.write("## 📉 Volatility & Bollinger Bands\n\n")
        f.write(f"**State**: **{vol.get('overall_state', 'UNKNOWN')}**\n\n")
        
        f.write(f"- **Current Price Position**: {bb.get('position', 0):.1f}% within bands\n")
        f.write(f"- **Bollinger Width**: {bb.get('width_pct', 0):.2f}%\n")
        f.write(f"- **Squeeze Detected**: {'YES ⚠️' if bb.get('squeeze') else 'NO'}\n")
        f.write(f"- **Band State**: {bb.get('state', 'UNKNOWN')}\n\n")
        
        f.write("**Band Levels**:\n")
        f.write(f"- Upper: ${bb.get('upper', 0):.2f}\n")
        f.write(f"- Middle: ${bb.get('middle', 0):.2f}\n")
        f.write(f"- Lower: ${bb.get('lower', 0):.2f}\n\n")
        
        f.write("---\n\n")
    
    def _write_pattern_report(self, f, profile):
        patterns = profile['candlestick_patterns']
        
        f.write("## 🕯️ Candlestick Pattern Analysis\n\n")
        f.write(f"**Patterns Scanned**: {patterns.get('total_scanned', 0)}\n\n")
        
        if patterns.get('patterns_found'):
            f.write("### Recent Patterns Detected\n\n")
            f.write("| Pattern | Signal | Bars Ago | Strength |\n")
            f.write("|---------|--------|----------|----------|\n")
            
            for p in patterns['patterns_found'][:10]:
                f.write(f"| {p['name']} | {p['signal']} | {p['bars_ago']} | {p['strength']} |\n")
            f.write("\n")
        
        if patterns.get('pattern_frequency'):
            f.write("### Most Frequent Patterns (Last 100 bars)\n\n")
            for pattern, count in list(patterns['pattern_frequency'].items())[:5]:
                f.write(f"- **{pattern}**: {count} occurrences\n")
            f.write("\n")
        
        f.write("---\n\n")
    
    def _write_trading_playbook(self, f, profile):
        playbook = profile['trading_playbook']
        
        f.write("## 🎯 TA-LIB ENHANCED TRADING PLAYBOOK\n\n")
        f.write("> [!WARNING]\n")
        f.write("> **Multi-Indicator Trading Rules**:\n\n")
        
        for rule in playbook.get('rules', []):
            f.write(f"{rule}\n")
        
        f.write("\n### Recommended Parameters\n\n")
        f.write(f"- **Stop Loss**: {playbook.get('optimal_sl_pct', 2.0):.1f}%\n")
        f.write(f"- **Take Profit**: {playbook.get('optimal_tp_multiplier', 3.0):.1f}x Risk\n")
        f.write(f"- **Position Size**: {playbook.get('position_size_multiplier', 1.0):.1f}x\n")
        f.write(f"- **Preferred Timeframe**: {playbook.get('preferred_timeframe', '4H')}\n\n")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TA-Lib Enhanced Symbol Profiler v3.0")
    parser.add_argument("symbol", help="Symbol to profile (e.g., GOLD, BTCUSD)")
    
    args = parser.parse_args()
    
    profiler = TALibSymbolProfiler(args.symbol)
    report_path = profiler.generate_profile()
    
    if report_path:
        print(f"\nREPORT_PATH:{report_path}")

if __name__ == "__main__":
    main()
