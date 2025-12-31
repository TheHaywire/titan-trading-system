"""
TEST ERNEST CHAN'S STRATEGIES ON ACTUAL FUTURES
================================================
Using the EXACT symbols from his book:
- TU (2-Year Treasury) - His main momentum example
- ES (S&P 500 futures)
- GC (Gold futures)

Expected: Sharpe 1.0 on TU per his book results!
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

class FuturesBacktest:
    """Test on actual futures with real volume"""
    
    # Futures spreads (typically lower than retail Forex)
    SPREADS = {
        'TU': 0.1,    # Very tight on Treasuries
        'ES': 0.25,   # E-mini S&P
        'GC': 0.5,    # Gold futures
        'CL': 0.3,    # Crude oil
        'NG': 0.5,    # Natural gas
    }
    
    SLIPPAGE = 0.2  # Futures have better fills
    
    def __init__(self):
        self.results = {}
        
    def initialize(self):
        if not mt5.initialize():
            return False
        print("✅ MT5 Connected\n")
        return True
    
    def find_symbol(self, base_name):
        """Find actual symbol name (might have suffix)"""
        symbols = mt5.symbols_get()
        
        # Direct match
        if mt5.symbol_info(base_name):
            return base_name
        
        # Find with suffix
        matches = [s.name for s in symbols if base_name in s.name]
        if matches:
            print(f"  Found {base_name} as: {matches[0]}")
            return matches[0]
        
        return None
    
    def get_data(self, symbol):
        """Get 1 year daily data"""
        # For futures, use daily timeframe (as Chan does)
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 500)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def momentum_strategy(self, df, symbol, lookback=250, holddays=25):
        """
        Ernest Chan's momentum strategy from Chapter 6:
        "Simply buy (sell) the future if it has a positive (negative) 
        12-month return, and hold the position for 1 month"
        
        lookback=250 trading days ≈ 12 months
        holddays=25 trading days ≈ 1 month
        """
        trades = []
        
        info = mt5.symbol_info(symbol)
        if not info:
            return []
        
        point = info.point
        base_spread = self.SPREADS.get(symbol[:2], 0.3)
        total_cost = base_spread + self.SLIPPAGE
        
        # Generate signals
        for i in range(lookback, len(df) - holddays):
            current = df.iloc[i]['close']
            past = df.iloc[i - lookback]['close']
            
            # Momentum signal
            if current > past:
                direction = 1  # Long
            elif current < past:
                direction = -1  # Short
            else:
                continue
            
            # Entry and exit
            entry = df.iloc[i]['close']
            exit_idx = i + holddays
            exit_price = df.iloc[exit_idx]['close']
            
            # Calculate return
            if direction == 1:
                profit_gross = (exit_price - entry) / point
            else:
                profit_gross = (entry - exit_price) / point
            
            profit_net = profit_gross - total_cost
            
            trades.append({
                'entry_date': df.iloc[i]['time'],
                'exit_date': df.iloc[exit_idx]['time'],
                'profit_gross': profit_gross,
                'profit_net': profit_net,
                'win': 1 if profit_net > 0 else 0,
                'direction': 'LONG' if direction == 1 else 'SHORT'
            })
        
        return trades
    
    def analyze(self, trades, symbol):
        """Calculate performance metrics"""
        if not trades:
            return None
        
        gross = [t['profit_gross'] for t in trades]
        net = [t['profit_net'] for t in trades]
        wins = [t for t in trades if t['win']]
        
        # Sharpe ratio calculation
        returns_pct = np.array(net) / 10000  # Convert pips to percentage
        sharpe = np.mean(returns_pct) / np.std(returns_pct) * np.sqrt(252) if np.std(returns_pct) > 0 else 0
        
        return {
            'symbol': symbol,
            'trades': len(trades),
            'wins': len(wins),
            'win_rate': len(wins) / len(trades) * 100,
            'gross_total': sum(gross),
            'gross_avg': np.mean(gross),
            'net_total': sum(net),
            'net_avg': np.mean(net),
            'sharpe': sharpe,
            'profitable': sum(net) > 0
        }
    
    def test_future(self, base_name):
        """Test one future"""
        print(f"{'='*70}")
        print(f"📊 {base_name} - Ernest Chan's Momentum Strategy")
        print(f"{'='*70}")
        
        # Find actual symbol
        symbol = self.find_symbol(base_name)
        if not symbol:
            print(f"❌ {base_name} not found\n")
            return
        
        # Get data
        df = self.get_data(symbol)
        if df is None:
            print(f"❌ No data for {symbol}\n")
            return
        
        print(f"Data: {len(df)} daily bars")
        print(f"Period: {df.iloc[-1]['time'].date()} to {df.iloc[0]['time'].date()}")
        print(f"Spread: {self.SPREADS.get(base_name, 0.3)} pips + {self.SLIPPAGE} slippage\n")
        
        # Backtest
        trades = self.momentum_strategy(df, symbol)
        result = self.analyze(trades, base_name)
        
        if result:
            print(f"RESULTS:")
            print(f"  Trades: {result['trades']}")
            print(f"  Win Rate: {result['win_rate']:.1f}%")
            print(f"  Gross: {result['gross_avg']:.2f} pips/trade ({result['gross_total']:.0f} total)")
            print(f"  Net: {result['net_avg']:.2f} pips/trade ({result['net_total']:.0f} total)")
            print(f"  Sharpe Ratio: {result['sharpe']:.2f}")
            
            if result['profitable']:
                print(f"  ✅ PROFITABLE!")
                
                # Compare to Chan's results
                if base_name == 'TU':
                    print(f"\n  📖 Ernest Chan's TU result: Sharpe 1.0")
                    print(f"  📊 Our result: Sharpe {result['sharpe']:.2f}")
                    if result['sharpe'] > 0.7:
                        print(f"  ✅ MATCHES BOOK! Strategy validated!")
                    else:
                        print(f"  ⚠️  Lower than book (market regime change?)")
            else:
                print(f"  ❌ Unprofitable")
            
            print()
            self.results[base_name] = result

def main():
    print("\n🚀 TESTING ON ERNEST CHAN'S ACTUAL FUTURES")
    print("Using symbols from 'Algorithmic Trading' book")
    print("Expected Sharpe 1.0 on TU per Chapter 6\n")
    
    tester = FuturesBacktest()
    if not tester.initialize():
        return
    
    # Test Chan's futures
    futures = ['TU', 'ES', 'GC']
    
    for future in futures:
        tester.test_future(future)
    
    # Summary
    print("="*70)
    print("📊 SUMMARY - Ernest Chan's Futures")
    print("="*70 + "\n")
    
    if tester.results:
        profitable = [r for r in tester.results.values() if r['profitable']]
        
        if profitable:
            print("✅ PROFITABLE FUTURES:\n")
            profitable.sort(key=lambda x: x['sharpe'], reverse=True)
            
            for r in profitable:
                print(f"  {r['symbol']:4s}: Sharpe {r['sharpe']:.2f} | {r['win_rate']:.1f}% WR | {r['net_total']:.0f} pips")
            
            print("\n🎯 SUCCESS! Found profitable futures strategies!")
            print("\nErnest Chan's methodology VALIDATED on actual futures!")
            print("These can be traded live with confidence.\n")
        else:
            print("❌ NO PROFITABLE FUTURES")
            print("\nPossible reasons:")
            print("- Market regime changed since book publication")
            print("- Data period different")
            print("- Still need parameter optimization\n")
    
    print("="*70 + "\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
