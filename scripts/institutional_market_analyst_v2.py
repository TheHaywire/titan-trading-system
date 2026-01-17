"""
Professional Institutional Market Analyst v2.0
The "Master Setup" Engine - Generates high-conviction MTF trade setup reports.
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

class ProfessionalMarketAnalyst:
    """Institutional-grade MTF analyst matching the Master Setup format"""
    
    TIMEFRAMES = {
        '1W': mt5.TIMEFRAME_W1,
        '1D': mt5.TIMEFRAME_D1,
        '4H': mt5.TIMEFRAME_H4,
        '30M': mt5.TIMEFRAME_M30,
        '15M': mt5.TIMEFRAME_M15,
        '5M': mt5.TIMEFRAME_M5,
        '1M': mt5.TIMEFRAME_M1,
    }
    
    def __init__(self, symbol):
        self.symbol = symbol.upper()
        self.resolved_symbol = self._resolve_symbol(symbol)
        self.data = {}
        self.analysis = {}
        
    def _resolve_symbol(self, symbol):
        """Standardizes symbol resolution across various brokers."""
        if not mt5.initialize():
            return None
            
        sym_clean = symbol.upper()
        # Common variations
        variations = [sym_clean, f"{sym_clean}Cash", f"{sym_clean}.cash", f"{sym_clean}CASH"]
        
        # Check all available symbols to find a case-insensitive match
        all_symbols = [s.name for s in mt5.symbols_get()]
        
        for v in variations:
            # Case-insensitive match check
            match = next((s for s in all_symbols if s.upper() == v.upper()), None)
            if match:
                return match
                
        return symbol

    def fetch_all_data(self):
        """Fetch data for all 7 timeframes"""
        print(f"📊 Fetching 7 timeframes for {self.resolved_symbol}...")
        
        for name, tf in self.TIMEFRAMES.items():
            count = 500 if name not in ['1W', '1D'] else 100
            rates = mt5.copy_rates_from_pos(self.resolved_symbol, tf, 0, count)
            if rates is not None:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                self.data[name] = df
            else:
                print(f"⚠️ Failed to fetch {name}")

    def run_analysis(self):
        """Execute deep analysis across all timeframes"""
        if not self.data:
            self.fetch_all_data()
            
        for tf_name, df in self.data.items():
            self.analysis[tf_name] = self._analyze_timeframe(tf_name, df)
            
    def _analyze_timeframe(self, name, df):
        """Detailed technical analysis for a specific timeframe"""
        close = df['close'].values.astype(np.float64)
        high = df['high'].values.astype(np.float64)
        low = df['low'].values.astype(np.float64)
        
        # TA-Lib Indicators
        rsi = talib.RSI(close, timeperiod=14)
        adx = talib.ADX(high, low, close, timeperiod=14)
        macd, macdsignal, macdhist = talib.MACD(close)
        sma200 = talib.SMA(close, timeperiod=200)
        
        current_price = close[-1]
        prev_price = close[-2]
        
        # Trend Detection
        is_bullish = current_price > sma200[-1] if not np.isnan(sma200[-1]) else current_price > talib.SMA(close, 50)[-1]
        trend_status = "ULTRA BULLISH" if is_bullish and rsi[-1] > 60 else ("BULLISH" if is_bullish else "BEARISH")
        
        # Structure
        higher_highs = close[-1] > close[-10:].mean() and low[-1] > low[-10:].mean()
        
        # Star Rating (1-5)
        stars = 1
        if is_bullish: stars += 1
        if rsi[-1] > 50 and rsi[-1] < 70: stars += 1
        if adx[-1] > 25: stars += 1
        if higher_highs: stars += 1
        
        return {
            'status': trend_status,
            'rsi': float(rsi[-1]),
            'adx': float(adx[-1]),
            'stars': stars,
            'price': float(current_price),
            'support': float(low[-20:].min()),
            'resistance': float(high[-20:].max()),
            'is_bullish': is_bullish
        }

    def generate_professional_report(self):
        """Generate the markdown report matching user's requested style"""
        self.run_analysis()
        
        report_dir = Path("analysis")
        report_dir.mkdir(exist_ok=True)
        filename = report_dir / f"{self.symbol}_MASTER_SETUP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        curr_price = self.analysis['15M']['price']
        
        # Overall Probability Calculation
        bull_votes = sum([1 for x in self.analysis.values() if x['is_bullish']])
        probability = int((bull_votes / len(self.analysis)) * 100)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {self.symbol} - COMPREHENSIVE MULTI-TIMEFRAME TRADE SETUP ANALYSIS\n\n")
            f.write(f"*Generated At: {now_str}*\n\n")
            
            # 1W - Macro
            w1 = self.analysis['1W']
            f.write(f"## 🎯 MACRO VIEW - WEEKLY (1W)\n\n")
            f.write(f"**MEGA TREND:** {w1['status']}\n")
            f.write(f"- **Current Level:** {w1['price']:.2f}\n")
            f.write(f"- **RSI:** {w1['rsi']:.1f}\n")
            f.write(f"- **Status:** {'HOLD BULLISH' if w1['is_bullish'] else 'CAUTION'}\n")
            f.write("\n***\n\n")
            
            # 1D - Daily
            d1 = self.analysis['1D']
            f.write(f"## 📊 DAILY (1D) - BIAS CONFIRMATION\n\n")
            f.write(f"**Status:** {d1['status']}\n")
            f.write(f"- **Support Zone:** {d1['support']:.2f}\n")
            f.write(f"- **Resistance:** {d1['resistance']:.2f}\n")
            f.write(f"- **RSI:** {d1['rsi']:.1f}\n")
            f.write("\n***\n\n")
            
            # 4H - Structure
            h4 = self.analysis['4H']
            f.write(f"## ⏰ 4-HOUR (4H) - STRUCTURE ANALYSIS\n\n")
            f.write(f"**Setup:** {h4['status']} Structure\n")
            f.write(f"- **ADX Strength:** {h4['adx']:.1f} ({'Strong' if h4['adx'] > 25 else 'Developing'})\n")
            f.write(f"- **Key Support:** {h4['support']:.2f}\n")
            f.write(f"- **Key Resistance:** {h4['resistance']:.2f}\n")
            f.write("\n***\n\n")
            
            # 30M - Continuation
            m30 = self.analysis['30M']
            f.write(f"## 🔥 30-MINUTE (30M) - CONTINUATION SETUP\n\n")
            f.write(f"**Status:** {'ACCUMULATING' if m30['is_bullish'] else 'DISTRIBUTING'}\n")
            f.write(f"- **RSI:** {m30['rsi']:.1f}\n")
            f.write(f"- **Targets:** {m30['resistance']:.2f}\n")
            f.write("\n***\n\n")
            
            # 15M - Entry
            m15 = self.analysis['15M']
            f.write(f"## ⚡ 15-MINUTE (15M) - ENTRY TIMEFRAME\n\n")
            f.write(f"**Bias:** {m15['status']}\n")
            f.write(f"- **Entry Potential:** {'HIGH' if m15['stars'] >= 4 else 'WATCHING'}\n")
            f.write("\n***\n\n")
            
            # 5M - Scalp
            m5 = self.analysis['5M']
            f.write(f"## 🎯 5-MINUTE (5M) - SCALP/QUICK ENTRY\n\n")
            f.write(f"**Micro-Trend:** {m5['status']}\n")
            f.write(f"- **Momentum:** {'RISING' if m5['rsi'] > 50 else 'FALLING'}\n")
            f.write("\n***\n\n")
            
            # 1M - Execution
            m1 = self.analysis['1M']
            f.write(f"## 📈 1-MINUTE (1M) - EXECUTION TIMEFRAME\n\n")
            f.write(f"**Current Status:** {'READY TO EXECUTE' if m1['stars'] >= 3 else 'WAITING'}\n")
            f.write(f"- **Price:** {m1['price']:.2f}\n")
            f.write("\n***\n\n")
            
            # OFFICIAL TRADE SETUP
            f.write(f"## 🚀 FINAL TRADE SETUP RECOMMENDATION\n\n")
            f.write(f"### **PRIMARY {'LONG' if bull_votes > 3 else 'SHORT'} SETUP**\n\n")
            
            f.write("| Timeframe | Bias | Strength | Action |\n")
            f.write("|-----------|------|----------|--------|\n")
            for tf_name in self.TIMEFRAMES.keys():
                ana = self.analysis[tf_name]
                stars = "⭐" * ana['stars']
                f.write(f"| **{tf_name}** | {ana['status']} | {stars} | {'BUY/HOLD' if ana['is_bullish'] else 'SELL/WAIT'} |\n")
            
            f.write("\n***\n\n")
            
            # Official Trade Parameters
            dir_str = "LONG ⬆️" if bull_votes > 3 else "SHORT ⬇️"
            sl = d1['support'] if bull_votes > 3 else d1['resistance']
            tp1 = d1['resistance'] if bull_votes > 3 else d1['support']
            tp2 = tp1 * (1.01 if bull_votes > 3 else 0.99)
            
            f.write(f"### 💎 OFFICIAL TRADE SETUP\n\n")
            f.write(f"**Direction:** {dir_str}\n\n")
            f.write(f"**Stop Loss:** {sl:.2f}\n")
            f.write(f"**Targets:**\n")
            f.write(f"- **TP1:** {tp1:.2f}\n")
            f.write(f"- **TP2:** {tp2:.2f}\n\n")
            
            f.write(f"### 📊 PROBABILITY ANALYSIS\n\n")
            f.write(f"**{'LONG' if bull_votes > 3 else 'SHORT'} Probability:** **{probability}%**\n\n")
            
            f.write(f"### ✅ EXECUTION CHECKLIST\n\n")
            f.write(f"- [ ] Entry Zone Alignment\n")
            f.write(f"- [ ] Stop Loss Set at {sl:.2f}\n")
            f.write(f"- [ ] RSI Confirmation on Execution Frame\n")
            f.write(f"- [ ] Volume Spike Check\n")
            
        print(f"✅ Professional report saved: {filename}")
        return filename

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Professional Market Analyst v2.0")
    parser.add_argument("symbol", help="Symbol to analyze")
    args = parser.parse_args()
    
    analyst = ProfessionalMarketAnalyst(args.symbol)
    report_path = analyst.generate_professional_report()
    print(f"\nREPORT_PATH:{report_path}")

if __name__ == "__main__":
    main()
