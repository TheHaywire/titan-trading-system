"""
WALK-FORWARD ANALYSIS (Detailed) - Futures Momentum
===================================================
Year-by-Year breakdown to identify regime dependence.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

class WalkForwardTester:
    
    SPREADS = {
        'TU': 0.1, 'ES': 0.25, 'GC': 0.5,
    }
    SLIPPAGE = 0.2
    
    def __init__(self):
        if not mt5.initialize():
            print("❌ MT5 failed")
            sys.exit()

    def find_symbol(self, base_name):
        symbols = mt5.symbols_get()
        # Prioritize exact futures
        matches = [s.name for s in symbols if base_name in s.name and ('FUT' in s.description.upper() or 'FUTURE' in s.description.upper())]
        if matches: return matches[0]
        
        # Fallback
        matches = [s.name for s in symbols if base_name in s.name]
        # Filter out obvious wrong ones like HGCOP for GC if possible
        if base_name == 'GC':
             gold_matches = [m for m in matches if 'GOLD' in mt5.symbol_info(m).description.upper()]
             if gold_matches: return gold_matches[0]
             
        return matches[0] if matches else None

    def get_data(self, symbol, bars=5000):
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, bars)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def run_walk_forward(self, base_name):
        print(f"\n🏃 ANALYZING: {base_name}")
        symbol = self.find_symbol(base_name)
        if not symbol:
            print(f"❌ Symbol not found for {base_name}")
            return
            
        desc = mt5.symbol_info(symbol).description
        print(f"   Symbol: {symbol} ({desc})")

        df = self.get_data(symbol)
        if df is None:
            print("❌ No Data")
            return
            
        print(f"   History: {len(df)} days ({df['time'].iloc[0].date()} to {df['time'].iloc[-1].date()})")

        LOOKBACK = 250
        HOLD_DAYS = 25
        cost = self.SPREADS.get(base_name, 0.3) + self.SLIPPAGE
        point = mt5.symbol_info(symbol).point
        
        trades = []
        yearly_results = {}
        
        # Walk Forward
        for i in range(LOOKBACK, len(df) - HOLD_DAYS, HOLD_DAYS):
            
            # Date of execution
            trade_date = df.iloc[i]['time']
            year = trade_date.year
            
            current = df.iloc[i]['close']
            past = df.iloc[i - LOOKBACK]['close']
            
            direction = 0
            if current > past: direction = 1
            elif current < past: direction = -1
            
            pips = 0
            if direction != 0:
                entry = df.iloc[i]['close']
                exit_price = df.iloc[i + HOLD_DAYS]['close']
                
                if direction == 1:
                    gross = (exit_price - entry) / point
                else:
                    gross = (entry - exit_price) / point
                    
                pips = gross - cost
                trades.append(pips)
            else:
                trades.append(0)
            
            # Accumulate yearly
            if year not in yearly_results:
                yearly_results[year] = []
            yearly_results[year].append(pips)

        # Print Yearly Breakdown
        print("\n   📅 YEARLY BREAKDOWN:")
        print(f"   {'Year':<6} | {'Pips':<10} | {'Trades':<6} | {'Avg/Trade':<10} | {'Win Rate':<8}")
        print("-" * 55)
        
        sorted_years = sorted(yearly_results.keys())
        for y in sorted_years:
            res = yearly_results[y]
            net = sum(res)
            count = len(res)
            avg = net / count if count > 0 else 0
            wins = len([r for r in res if r > 0])
            wr = (wins/count*100) if count > 0 else 0
            
            status = "✅" if net > 0 else "❌"
            print(f"   {y:<6} | {net:<10.1f} | {count:<6} | {avg:<10.1f} | {wr:<5.1f}% {status}")

def main():
    tester = WalkForwardTester()
    print("YEAR-BY-YEAR MOMENTUM ANALYSIS")
    print("="*60)
    
    for f in ['TU', 'ES', 'GC']:
        tester.run_walk_forward(f)
        
    mt5.shutdown()

if __name__ == "__main__":
    main()
