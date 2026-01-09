"""
Institutional Backtesting Engine
Validates the institutional strategy logic against historical MT5 data.
"""

import os
import sys
import time
import argparse
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from scripts.institutional_market_analyst import InstitutionalMarketAnalyst
from scripts.technical_patterns import get_all_patterns

class BacktestEngine:
    def __init__(self, symbol, timeframe, bars=1000):
        self.symbol = symbol
        self.tf_str = timeframe
        self.bars = bars
        self.tf_val = self._map_tf(timeframe)
        self.initialize_mt5()
        
    def _map_tf(self, tf):
        tf_map = {
            "1M": mt5.TIMEFRAME_M1, "5M": mt5.TIMEFRAME_M5, "15M": mt5.TIMEFRAME_M15,
            "1H": mt5.TIMEFRAME_H1, "4H": mt5.TIMEFRAME_H4, "1D": mt5.TIMEFRAME_D1
        }
        return tf_map.get(tf, mt5.TIMEFRAME_H1)
        
    def initialize_mt5(self):
        if not mt5.initialize():
            print("❌ MT5 Initialization Failed")
            sys.exit(1)

    def run_backtest(self, start_idx=200, min_score=7):
        """
        Runs a rolling window backtest.
        Warning: This is computationally intensive as it runs the analyst logic for each bar.
        """
        print(f"🚀 Starting Backtest for {self.symbol} ({self.tf_str}) | Bars: {self.bars}")
        
        # Fetch historical data
        rates = mt5.copy_rates_from_pos(self.symbol, self.tf_val, 0, self.bars + start_idx)
        if rates is None or len(rates) < start_idx:
            print("❌ Not enough data for backtest")
            return
            
        df_full = pd.DataFrame(rates)
        df_full['time'] = pd.to_datetime(df_full['time'], unit='s')
        
        trades = []
        
        # Simulation Loop
        for i in range(start_idx, len(df_full)):
            # "Look-back" window
            df_slice = df_full.iloc[i-start_idx:i+1].copy()
            
            # Run pattern detection and scoring (Simplified Institutional Logic)
            # For a real heavy backtest, we'd use a vectorized version of the analyst.
            # Here we use the shared patterns to find opportunities.
            
            # 1. Add RSI for patterns
            delta = df_slice['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df_slice['RSI'] = 100 - (100 / (1 + rs))
            
            patterns = get_all_patterns(df_slice)
            
            # Simple scoring for backtest
            score = len(patterns) * 2
            if score >= min_score:
                entry_price = df_slice['close'].iloc[-1]
                entry_time = df_slice['time'].iloc[-1]
                
                # Determine direction (heuristic based on first pattern)
                direction = "BUY" if any(x in patterns[0].upper() for x in ["BULL", "HAMMER", "BOTTOM"]) else "SELL"
                
                # Dynamic SL/TP (e.g., 2% SL, 4% TP)
                sl = entry_price * (0.98 if direction == "BUY" else 1.02)
                tp = entry_price * (1.04 if direction == "BUY" else 0.96)
                
                # Check outcome in future bars
                trade_result = self._track_outcome(df_full, i, direction, sl, tp)
                
                if trade_result:
                    trades.append({
                        "time": entry_time,
                        "direction": direction,
                        "entry": entry_price,
                        "score": score,
                        "result": trade_result['status'],
                        "pips": trade_result['profit_pips']
                    })
                    print(f"🔔 Signal @ {entry_time} | {direction} | Score: {score} | Result: {trade_result['status']}")

        self._report_metrics(trades)

    def _track_outcome(self, df_full, current_idx, d, sl, tp):
        """Looks forward in time to see if SL or TP was hit"""
        for j in range(current_idx + 1, len(df_full)):
            high = df_full['high'].iloc[j]
            low = df_full['low'].iloc[j]
            close = df_full['close'].iloc[j]
            
            if d == "BUY":
                if low <= sl: return {"status": "LOSS", "profit_pips": -200} # simplified pips
                if high >= tp: return {"status": "WIN", "profit_pips": 400}
            else:
                if high >= sl: return {"status": "LOSS", "profit_pips": -200}
                if low <= tp: return {"status": "WIN", "profit_pips": 400}
        
        return None # Pending/Not closed in data range

    def _report_metrics(self, trades):
        if not trades:
            print("\n❌ No trades generated during backtest.")
            return
            
        df_trades = pd.DataFrame(trades)
        wins = len(df_trades[df_trades['result'] == 'WIN'])
        losses = len(df_trades[df_trades['result'] == 'LOSS'])
        total = wins + losses
        win_rate = (wins / total * 100) if total > 0 else 0
        
        print("\n" + "="*50)
        print("🏛️ INSTITUTIONAL BACKTEST REPORT")
        print("="*50)
        print(f"Symbol:     {self.symbol}")
        print(f"Timeframe:  {self.tf_str}")
        print(f"Total Signals: {len(df_trades)}")
        print(f"Total Trades:  {total}")
        print(f"Wins:          {wins}")
        print(f"Losses:        {losses}")
        print(f"Win Rate:      {win_rate:.1f}%")
        print(f"Profit (Est):  {df_trades['pips'].sum():.0f} pips")
        print("="*50 + "\n")

def main():
    parser = argparse.ArgumentParser(description="Titan Backtest Engine")
    parser.add_argument("symbol", help="e.g. GOLD, BTCUSD")
    parser.add_argument("--tf", default="1H", help="Timeframe (1M, 5M, 15M, 1H, 4H, 1D)")
    parser.add_argument("--bars", type=int, default=500, help="Number of bars to backtest")
    parser.add_argument("--score", type=int, default=7, help="Minimum score to trigger trade")
    
    args = parser.parse_args()
    
    engine = BacktestEngine(args.symbol, args.tf, args.bars)
    engine.run_backtest(min_score=args.score)

if __name__ == "__main__":
    main()
