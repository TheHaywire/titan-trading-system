"""
ONE YEAR BACKTEST - Statistical Validation
===========================================
Test all book concepts on 1 year of data (~35,000 M15 bars)
This provides statistically significant sample size.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class OneYearBacktest:
    def __init__(self):
        self.results = {}
        
    def initialize(self):
        if not mt5.initialize():
            print("❌ MT5 failed")
            return False
        print("✅ MT5 Connected")
        return True
    
    def get_year_data(self, symbol):
        """Get 1 year of M15 data"""
        # 365 days × 96 bars/day = ~35,040 bars
        bars_needed = 365 * 96
        
        print(f"📥 Loading {symbol} - 1 year data...")
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, bars_needed)
        
        if rates is None:
            print(f"❌ Failed to get data")
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        print(f"✅ Loaded {len(df):,} bars from {df.iloc[-1]['time'].date()} to {df.iloc[0]['time'].date()}")
        return df
    
    def add_indicators(self, df):
        """Add all indicators"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
        
        # Volume
        df['VOL_MA'] = df['tick_volume'].rolling(20).mean()
        df['VOL_RATIO'] = df['tick_volume'] / df['VOL_MA'].replace(0, 1.0)
        
        # ATR & ADX
        high, low, close = df['high'], df['low'], df['close']
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
        
        return df
    
    def backtest(self, df, symbol, strategy_name, filter_func):
        """Run backtest"""
        trades = []
        info = mt5.symbol_info(symbol)
        if not info:
            return []
        
        point = info.point
        
        for i in range(100, len(df) - 100):
            curr = df.iloc[i]
            
            # Filter
            if not filter_func(curr):
                continue
            
            # Signal
            if curr['RSI'] < 30:
                direction = "BUY"
            elif curr['RSI'] > 70:
                direction = "SELL"
            else:
                continue
            
            # Entry
            entry = curr['close']
            atr = curr['ATR']
            
            # Dynamic stops
            sl_dist = atr * 2
            tp_dist = atr * 3
            
            if direction == "BUY":
                sl = entry - sl_dist
                tp = entry + tp_dist
            else:
                sl = entry + sl_dist
                tp = entry - tp_dist
            
            # Find exit
            exit_price = None
            exit_idx = None
            
            for j in range(i+1, min(i+200, len(df))):
                bar = df.iloc[j]
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['high'] >= tp:
                        exit_price = tp
                        exit_idx = j
                        break
                else:
                    if bar['high'] >= sl:
                        exit_price = sl
                        exit_idx = j
                        break
                    elif bar['low'] <= tp:
                        exit_price = tp
                        exit_idx = j
                        break
            
            if exit_price:
                profit = (exit_price - entry) / point if direction == "BUY" else (entry - exit_price) / point
                
                trades.append({
                    'entry_date': curr['time'],
                    'exit_date': df.iloc[exit_idx]['time'] if exit_idx else None,
                    'profit': profit,
                    'win': 1 if profit > 0 else 0,
                    'direction': direction
                })
        
        return trades
    
    def analyze(self, trades, name):
        """Analyze results"""
        if not trades:
            return None
        
        profits = [t['profit'] for t in trades]
        wins = [t for t in trades if t['win'] == 1]
        losses = [t for t in trades if t['win'] == 0]
        
        win_rate = len(wins) / len(trades) * 100
        avg_win = np.mean([t['profit'] for t in wins]) if wins else 0
        avg_loss = np.mean([t['profit'] for t in losses]) if losses else 0
        total = sum(profits)
        expectancy = np.mean(profits)
        
        profit_factor = abs(sum([t['profit'] for t in wins]) / sum([t['profit'] for t in losses])) if losses and wins else 0
        
        return {
            'name': name,
            'trades': len(trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'total_pips': total,
            'expectancy': expectancy,
            'profit_factor': profit_factor
        }
    
    def test_symbol(self, symbol):
        """Test all strategies on symbol"""
        print(f"\n{'='*70}")
        print(f"📊 {symbol} - ONE YEAR BACKTEST")
        print(f"{'='*70}")
        
        df = self.get_year_data(symbol)
        if df is None:
            return
        
        df = self.add_indicators(df)
        
        # Strategies
        strategies = [
            ("Baseline (RSI 30/70)", lambda c: True),
            ("+ VPA (Vol>0.8)", lambda c: c['VOL_RATIO'] > 0.8),
            ("+ VPA + ADX (>20)", lambda c: c['VOL_RATIO'] > 0.8 and c['ADX'] > 20),
            ("+ VPA + ADX (>25)", lambda c: c['VOL_RATIO'] > 0.8 and c['ADX'] > 25),
        ]
        
        results = []
        
        for name, filter_func in strategies:
            print(f"\nTesting: {name}...")
            trades = self.backtest(df, symbol, name, filter_func)
            analysis = self.analyze(trades, name)
            
            if analysis:
                results.append(analysis)
                print(f"  ✅ {analysis['trades']} trades, {analysis['win_rate']:.1f}% WR, {analysis['total_pips']:.0f} pips")
        
        # Print detailed results
        print(f"\n{'='*70}")
        print(f"DETAILED RESULTS - {symbol}")
        print(f"{'='*70}")
        
        for r in results:
            print(f"\n{r['name']}:")
            print(f"  Trades: {r['trades']}")
            print(f"  Wins: {r['wins']} | Losses: {r['losses']}")
            print(f"  Win Rate: {r['win_rate']:.2f}%")
            print(f"  Avg Win: {r['avg_win']:.1f} pips")
            print(f"  Avg Loss: {r['avg_loss']:.1f} pips")
            print(f"  Total: {r['total_pips']:.1f} pips")
            print(f"  Expectancy: {r['expectancy']:.2f} pips/trade")
            print(f"  Profit Factor: {r['profit_factor']:.2f}")
        
        # Save results
        self.results[symbol] = results
        
        return results

def main():
    print("\n🚀 ONE YEAR BACKTEST - Statistical Validation")
    print("Testing all concepts on 365 days of data\n")
    
    tester = OneYearBacktest()
    
    if not tester.initialize():
        return
    
    # Test EURUSD first (most liquid)
    tester.test_symbol("EURUSD")
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 SUMMARY")
    print(f"{'='*70}")
    
    if "EURUSD" in tester.results:
        baseline = tester.results["EURUSD"][0]
        enhanced = tester.results["EURUSD"][2]  # VPA + ADX
        
        print(f"\nBASELINE:")
        print(f"  {baseline['trades']} trades, {baseline['win_rate']:.1f}% WR")
        
        print(f"\nENHANCED (VPA + ADX):")
        print(f"  {enhanced['trades']} trades, {enhanced['win_rate']:.1f}% WR")
        
        improvement = enhanced['win_rate'] - baseline['win_rate']
        print(f"\n🎯 IMPROVEMENT: {improvement:+.1f}% win rate")
        
        if improvement > 2:
            print("✅ VALIDATED: Book concepts improve performance!")
        elif improvement > 0:
            print("⚠️  MARGINAL: Small improvement, consider selective use")
        else:
            print("❌ NOT VALIDATED: Stick to baseline")
    
    print(f"\n{'='*70}")
    print("✅ ONE YEAR BACKTEST COMPLETE")
    print(f"{'='*70}\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
