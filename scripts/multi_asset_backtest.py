"""
COMPREHENSIVE MULTI-ASSET BACKTEST
===================================
Test all book concepts across different asset categories to find
which strategies work best for which markets.

Categories:
- Forex (EURUSD, GBPUSD, USDJPY)
- Commodities (GOLD, SILVER)
- Crypto (BTCUSD, ETHUSD)
- Indices (US500, US30)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime

class MultiAssetBacktest:
    def __init__(self):
        self.results = {}
        
    def initialize(self):
        if not mt5.initialize():
            print(f"❌ MT5 init failed")
            return False
        print("✅ MT5 Connected\n")
        return True
    
    def get_data(self, symbol, bars=2880):
        """Get historical data"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, bars)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def calculate_indicators(self, df):
        """Calculate all indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
        
        # Volume
        df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
        df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)
        
        # ATR & ADX
        high = df['high']
        low = df['low']
        close = df['close']
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        atr_adx = tr.rolling(14).mean()
        plus_di = 100 * (plus_dm.rolling(14).mean() / atr_adx)
        minus_di = 100 * (minus_dm.rolling(14).mean() / atr_adx)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        df['ADX'] = dx.rolling(14).mean()
        
        # EMA
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        df['MOM'] = df['close'].pct_change(5) * 100
        
        return df
    
    def backtest_strategy(self, df, symbol, strategy_name, filter_func):
        """Backtest a strategy"""
        trades = []
        info = mt5.symbol_info(symbol)
        if not info:
            return []
        
        point = info.point
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            
            # Apply filter
            if not filter_func(curr):
                continue
            
            # Determine direction
            if curr['RSI'] < 30:
                direction = "BUY"
            elif curr['RSI'] > 70:
                direction = "SELL"
            else:
                continue
            
            # Entry
            entry = curr['close']
            
            # Dynamic stops based on ATR
            atr = curr['ATR']
            sl_distance = atr * 2
            tp_distance = atr * 3
            
            if direction == "BUY":
                sl = entry - sl_distance
                tp = entry + tp_distance
            else:
                sl = entry + sl_distance
                tp = entry - tp_distance
            
            # Find exit
            for j in range(i+1, min(i+100, len(df))):
                bar = df.iloc[j]
                
                hit_sl = False
                hit_tp = False
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        hit_sl = True
                        exit_price = sl
                    elif bar['high'] >= tp:
                        hit_tp = True
                        exit_price = tp
                else:
                    if bar['high'] >= sl:
                        hit_sl = True
                        exit_price = sl
                    elif bar['low'] <= tp:
                        hit_tp = True
                        exit_price = tp
                
                if hit_sl or hit_tp:
                    profit_pips = (exit_price - entry) / point if direction == "BUY" else (entry - exit_price) / point
                    trades.append({
                        'profit': profit_pips,
                        'win': 1 if profit_pips > 0 else 0,
                        'bars_held': j - i
                    })
                    break
        
        return trades
    
    def analyze_trades(self, trades):
        """Analyze trade results"""
        if not trades:
            return None
        
        profits = [t['profit'] for t in trades]
        wins = [t for t in trades if t['win'] == 1]
        
        return {
            'total_trades': len(trades),
            'wins': len(wins),
            'win_rate': len(wins) / len(trades) * 100,
            'avg_profit': np.mean(profits),
            'total_profit': sum(profits),
            'avg_win': np.mean([t['profit'] for t in wins]) if wins else 0,
            'avg_loss': np.mean([t['profit'] for t in trades if t['win'] == 0]) if len(wins) < len(trades) else 0,
            'avg_bars': np.mean([t['bars_held'] for t in trades])
        }
    
    def test_symbol(self, symbol, category):
        """Test all strategies on one symbol"""
        print(f"\n{'='*60}")
        print(f"📊 {symbol} ({category})")
        print(f"{'='*60}")
        
        # Get data
        df = self.get_data(symbol)
        if df is None:
            print(f"❌ No data available")
            return
        
        df = self.calculate_indicators(df)
        
        # Define strategies
        strategies = {
            'Baseline': lambda curr: True,
            '+ VPA': lambda curr: curr['VOL_RATIO'] > 0.8,
            '+ VPA + ADX': lambda curr: curr['VOL_RATIO'] > 0.8 and curr['ADX'] > 20,
            '+ VPA + ADX + MOM': lambda curr: (
                curr['VOL_RATIO'] > 0.8 and 
                curr['ADX'] > 20 and
                ((curr['RSI'] < 30 and curr['MOM'] > 0.3) or
                 (curr['RSI'] > 70 and curr['MOM'] < -0.3))
            ),
        }
        
        results = {}
        
        for name, filter_func in strategies.items():
            trades = self.backtest_strategy(df, symbol, name, filter_func)
            analysis = self.analyze_trades(trades)
            
            if analysis:
                results[name] = analysis
                print(f"\n{name}:")
                print(f"  Trades: {analysis['total_trades']}")
                print(f"  Win Rate: {analysis['win_rate']:.1f}%")
                print(f"  Avg: {analysis['avg_profit']:.2f} pips")
                print(f"  Total: {analysis['total_profit']:.1f} pips")
        
        # Best strategy for this symbol
        if results:
            best = max(results.items(), key=lambda x: x[1]['win_rate'])
            print(f"\n🏆 BEST for {symbol}: {best[0]} ({best[1]['win_rate']:.1f}% WR)")
        
        self.results[symbol] = {
            'category': category,
            'strategies': results
        }
    
    def print_summary(self):
        """Print category-wise summary"""
        print("\n\n" + "="*60)
        print("📊 CATEGORY SUMMARY")
        print("="*60)
        
        categories = {}
        for symbol, data in self.results.items():
            cat = data['category']
            if cat not in categories:
                categories[cat] = []
            categories[cat].append((symbol, data['strategies']))
        
        for category, symbols_data in categories.items():
            print(f"\n📈 {category.upper()}")
            print("-" * 60)
            
            # Aggregate results
            for strategy_name in ['Baseline', '+ VPA', '+ VPA + ADX', '+ VPA + ADX + MOM']:
                total_trades = 0
                total_wins = 0
                
                for symbol, strategies in symbols_data:
                    if strategy_name in strategies:
                        total_trades += strategies[strategy_name]['total_trades']
                        total_wins += strategies[strategy_name]['wins']
                
                if total_trades > 0:
                    wr = total_wins / total_trades * 100
                    print(f"{strategy_name:20s}: {total_trades:4d} trades, {wr:5.1f}% WR")
        
        # Key insights
        print("\n\n" + "="*60)
        print("🎯 KEY INSIGHTS")
        print("="*60)
        
        insights = []
        
        # Which category benefits most from filters?
        for category, symbols_data in categories.items():
            baseline_wr = 0
            enhanced_wr = 0
            count = 0
            
            for symbol, strategies in symbols_data:
                if 'Baseline' in strategies and '+ VPA + ADX' in strategies:
                    baseline_wr += strategies['Baseline']['win_rate']
                    enhanced_wr += strategies['+ VPA + ADX']['win_rate']
                    count += 1
            
            if count > 0:
                avg_baseline = baseline_wr / count
                avg_enhanced = enhanced_wr / count
                improvement = avg_enhanced - avg_baseline
                
                insights.append({
                    'category': category,
                    'improvement': improvement,
                    'baseline_wr': avg_baseline,
                    'enhanced_wr': avg_enhanced
                })
        
        # Sort by improvement
        insights.sort(key=lambda x: x['improvement'], reverse=True)
        
        print("\n1. Which markets benefit MOST from book concepts:")
        for i, insight in enumerate(insights[:3], 1):
            print(f"   {i}. {insight['category']:12s}: {insight['baseline_wr']:.1f}% → {insight['enhanced_wr']:.1f}% (+{insight['improvement']:.1f}%)")
        
        print("\n2. Overall recommendation:")
        total_improvement = sum(i['improvement'] for i in insights) / len(insights) if insights else 0
        if total_improvement > 2:
            print(f"   ✅ Book concepts add {total_improvement:.1f}% avg improvement - ADOPT!")
        elif total_improvement > 0:
            print(f"   ⚠️  Book concepts add {total_improvement:.1f}% - Consider selective adoption")
        else:
            print(f"   ❌ No improvement - Keep baseline")

def main():
    print("\n🚀 COMPREHENSIVE MULTI-ASSET BACKTEST")
    print("Testing 9 books concepts across asset classes\n")
    
    tester = MultiAssetBacktest()
    
    if not tester.initialize():
        return
    
    # Define test universe
    test_symbols = {
        'Forex': ['EURUSD', 'GBPUSD', 'USDJPY'],
        'Commodities': ['GOLD'],  # SILVER often not available
        'Crypto': ['BTCUSD'],     # ETHUSD often not available
        'Indices': ['US500', 'US30']
    }
    
    # Test each symbol
    for category, symbols in test_symbols.items():
        for symbol in symbols:
            # Check if symbol exists
            info = mt5.symbol_info(symbol)
            if info is None:
                print(f"⚠️  {symbol} not available")
                continue
            
            tester.test_symbol(symbol, category)
    
    # Print summary
    tester.print_summary()
    
    print("\n" + "="*60)
    print("✅ BACKTEST COMPLETE")
    print("="*60 + "\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
