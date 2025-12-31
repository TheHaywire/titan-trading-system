"""
H1 TIMEFRAME BACKTEST - Ernest Chan Methodology
================================================
Test if wider timeframe makes mean reversion profitable

WHY H1:
- Fewer trades = less total spread cost
- Wider stops = spread smaller % of move
- Less noise = better signals
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

class H1Backtest:
    """Test on H1 timeframe"""
    
    SPREADS = {
        'EURUSD': 0.8,
        'GBPUSD': 1.2,
        'USDJPY': 1.0,
        'GOLD': 2.0,
        'US500': 0.5,
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
        """Get 1 year H1 data"""
        # 365 days × 24 hours = ~8760 bars
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 8760)
        if rates is None:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    
    def add_indicators(self, df):
        """RSI and ATR"""
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain / loss.replace(0, 0.0001)))
        
        # ATR
        high, low, close = df['high'], df['low'], df['close']
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(14).mean()
        
        return df
    
    def backtest(self, df, symbol):
        """Simple RSI mean reversion on H1"""
        trades = []
        
        info = mt5.symbol_info(symbol)
        if not info:
            return []
        
        point = info.point
        spread = self.SPREADS.get(symbol, 1.0)
        total_cost = spread + self.SLIPPAGE
        
        for i in range(50, len(df) - 50):
            curr = df.iloc[i]
            
            # RSI extremes
            if curr['RSI'] < 30:
                direction = "BUY"
            elif curr['RSI'] > 70:
                direction = "SELL"
            else:
                continue
            
            entry = curr['close']
            atr = curr['ATR']
            
            # ATR stops (same 2x/3x but on H1 = wider absolute values)
            sl_dist = atr * 2
            tp_dist = atr * 3
            
            if direction == "BUY":
                sl, tp = entry - sl_dist, entry + tp_dist
            else:
                sl, tp = entry + sl_dist, entry - tp_dist
            
            # Find exit
            for j in range(i+1, min(i+100, len(df))):
                bar = df.iloc[j]
                
                if direction == "BUY":
                    if bar['low'] <= sl:
                        exit_price = sl
                        break
                    elif bar['high'] >= tp:
                        exit_price = tp
                        break
                else:
                    if bar['high'] >= sl:
                        exit_price = sl
                        break
                    elif bar['low'] <= tp:
                        exit_price = tp
                        break
            else:
                continue
            
            profit_gross = (exit_price - entry) / point if direction == "BUY" else (entry - exit_price) / point
            profit_net = profit_gross - total_cost
            
            trades.append({
                'profit_gross': profit_gross,
                'profit_net': profit_net,
                'win': 1 if profit_net > 0 else 0
            })
        
        return trades
    
    def analyze(self, trades, symbol):
        """Analyze results"""
        if not trades:
            return None
        
        gross = [t['profit_gross'] for t in trades]
        net = [t['profit_net'] for t in trades]
        
        return {
            'symbol': symbol,
            'trades': len(trades),
            'gross_total': sum(gross),
            'gross_avg': np.mean(gross),
            'net_total': sum(net),
            'net_avg': np.mean(net),
            'net_wr': len([t for t in trades if t['win']]) / len(trades) * 100,
            'profitable': sum(net) > 0
        }
    
    def test_symbol(self, symbol):
        """Test one symbol"""
        print(f"📊 {symbol}")
        
        df = self.get_data(symbol)
        if df is None:
            print("  ❌ No data\n")
            return
        
        df = self.add_indicators(df)
        
        trades = self.backtest(df, symbol)
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
    print("\n🚀 H1 TIMEFRAME BACKTEST")
    print("Testing if wider timeframe makes strategy profitable\n")
    print("="*70 + "\n")
    
    tester = H1Backtest()
    if not tester.initialize():
        return
    
    # Focus on best candidates
    symbols = ['EURUSD', 'GBPUSD', 'GOLD', 'US500']
    
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
        for r in profitable:
            print(f"  {r['symbol']}: {r['net_total']:.1f} pips ({r['net_avg']:.2f} avg)")
        
        print("\n🎯 H1 timeframe WORKS! Strategy is viable.")
    else:
        print("❌ NO PROFITABLE SYMBOLS on H1")
        print("\nMean reversion doesn't work even on H1.")
        print("Need to try momentum strategies instead.\n")
    
    print("="*70 + "\n")
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
