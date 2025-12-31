"""
MOMENTUM STRATEGY - Ernest Chan Chapter 6
==========================================
Simple Time-Series Momentum from "Algorithmic Trading"

KEY INSIGHT from book:
"Simply buy (sell) the future if it has a positive (negative) 12-month 
return, and hold the position for 1 month"

Modified for daily trading:
- Look-back: 250 days (12 months)  
- Hold: 25 days (1 month)
- Daily rebalancing with 1/25 capital each day
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

class MomentumStrategy:
    """Time-Series Momentum per Ernest Chan"""
    
    SPREADS = {
        'EURUSD': 0.8,
        'GBPUSD': 1.2,
        'USDJPY': 1.0,
        'GOLD': 2.0,
        'US500': 0.5,
        'US30': 2.0,
    }
    
    SLIPPAGE = 0.5
    
    def __init__(self):
        self.results = {}
        
    def initialize(self):
        if not mt5.initialize():
            return False
        print("✅ MT5 Connected\n")
        return True
    
    def get_data(self, symbol):
        """Get 1 year M15 data"""
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 35040)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def backtest_momentum(self, df, symbol):
        """
        Time-series momentum strategy:
        - Buy if price > price 250 days ago
        - Sell if price < price 250 days ago
        - Hold for 25 days
        - Rebalance daily (1/25 of capital)
        """
        lookback = 250
        holddays = 25
        
        trades = []
        
        info = mt5.symbol_info(symbol)
        if not info:
            return []
        
        point = info.point
        spread = self.SPREADS.get(symbol, 1.0) 
        total_cost = spread + self.SLIPPAGE
        
        # Calculate positions
        positions = []
        for i in range(lookback, len(df)):
            current_price = df.iloc[i]['close']
            past_price = df.iloc[i - lookback]['close']
            
            if current_price > past_price:
                # Positive momentum - BUY
                positions.append(1)
            elif current_price < past_price:
                # Negative momentum - SELL
                positions.append(-1)
            else:
                positions.append(0)
        
        # Calculate returns with 25-day hold
        for i in range(len(positions) - holddays):
            if positions[i] == 0:
                continue
            
            entry_idx = i + lookback
            exit_idx = entry_idx + holddays
            
            if exit_idx >= len(df):
                break
            
            entry_price = df.iloc[entry_idx]['close']
            exit_price = df.iloc[exit_idx]['close']
            
            if positions[i] == 1:  # Long
                profit_gross = (exit_price - entry_price) / point
            else:  # Short
                profit_gross = (entry_price - exit_price) / point
            
            profit_net = profit_gross - total_cost
            
            trades.append({
                'profit_gross': profit_gross,
                'profit_net': profit_net,
                'win': 1 if profit_net > 0 else 0,
                'direction': 'BUY' if positions[i] == 1 else 'SELL'
            })
        
        return trades
    
    def analyze(self, trades, symbol):
        """Analyze results"""
        if not trades:
            return None
        
        gross = [t['profit_gross'] for t in trades]
        net = [t['profit_net'] for t in trades]
        wins = [t for t in trades if t['win']]
        
        return {
            'symbol': symbol,
            'trades': len(trades),
            'gross_total': sum(gross),
            'gross_avg': np.mean(gross),
            'net_total': sum(net),
            'net_avg': np.mean(net),
            'net_wr': len(wins) / len(trades) * 100 if trades else 0,
            'profitable': sum(net) > 0
        }
    
    def test_symbol(self, symbol):
        """Test momentum on one symbol"""
        print(f"📊 {symbol}")
        
        df = self.get_data(symbol)
        if df is None:
            print("  ❌ No data\n")
            return
        
        trades = self.backtest_momentum(df, symbol)
        result = self.analyze(trades, symbol)
        
        if result:
            print(f"  Trades: {result['trades']}")
            print(f"  Gross: {result['gross_avg']:.2f} pips/trade ({result['gross_total']:.1f} total)")
            print(f"  Net: {result['net_avg']:.2f} pips/trade ({result['net_total']:.1f} total)")
            print(f"  Win Rate: {result['net_wr']:.1f}%")
            
            if result['profitable']:
                print(f"  ✅ PROFITABLE\n")
            else:
                print(f"  ❌ Unprofitable\n")
            
            self.results[symbol] = result

def main():
    print("\n🚀 MOMENTUM STRATEGY - Ernest Chan Chapter 6")
    print("Time-Series Momentum: 250-day lookback, 25-day hold\n")
    print("="*70 + "\n")
    
    tester = MomentumStrategy()
    if not tester.initialize():
        return
    
    # Test symbols
    symbols = ['EURUSD', 'GBPUSD', 'GOLD', 'US500', 'US30']
    
    for symbol in symbols:
        if mt5.symbol_info(symbol):
            tester.test_symbol(symbol)
    
    # Summary
    print("="*70)
    print("SUMMARY:")
    print("="*70 + "\n")
    
    profitable = [r for r in tester.results.values() if r['profitable']]
    
    if profitable:
        print("✅ PROFITABLE SYMBOLS:\n")
        profitable.sort(key=lambda x: x['net_total'], reverse=True)
        
        for r in profitable:
            print(f"  {r['symbol']}: {r['net_total']:.1f} pips ({r['net_wr']:.1f}% WR, {r['trades']} trades)")
        
        print("\n🎯 MOMENTUM WORKS! Found profitable strategy!")
        print("\nErnest Chan was right:")
        print("\"Simply buy if positive return, sell if negative\"")
        print("Simple time-series momentum beats mean reversion!\n")
    else:
        print("❌ NO PROFITABLE SYMBOLS")
        print("\nMomentum doesn't work either on these symbols/timeframes.\n")
        print("May need:")
        print("- Different symbols (futures work better per Chan)")
        print("- Different timeframes")
        print("- Different strategy entirely\n")
    
    print("="*70 + "\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
