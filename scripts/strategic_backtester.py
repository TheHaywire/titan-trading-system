"""
Titan AI Strategic Backtester
=============================
Replays historical data to find where our 'Sentinel' would have 
triggered, then uses AI to analyze why it worked or failed.
"""

import os
import sys
import json
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.regime_detector import RegimeDetector
from titan_system.core.news_intelligence import NewsIntelligence
from titan_system.core.alpha_feedback import AlphaFeedback

class StrategicBacktester:
    """Rigorous backtester with AI Post-Mortem."""
    
    def __init__(self, symbol: str, lookback_days: int = 5):
        self.symbol = symbol
        self.lookback_days = lookback_days
        self.news = NewsIntelligence()
        self.detector = RegimeDetector(symbol)
        
    def get_historical_data(self) -> Optional[pd.DataFrame]:
        """Fetch high-precision historical bars."""
        if not mt5.initialize():
            return None
        
        # M15 bars for execution simulation
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 96 * self.lookback_days)
        if rates is None or len(rates) == 0:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df

    def run_simulation(self):
        """Simulate the Sentinel's Layer 1-3 logic over historical data."""
        print(f"\n🧪 STARTING STRATEGIC BACKTEST: {self.symbol}...")
        df = self.get_historical_data()
        if df is None:
            print("❌ Data fetch failed.")
            return

        results = []
        
        # We simulate the sentinel check every 4 bars (1 hour)
        for i in range(50, len(df) - 8, 4): 
            current_time = df.iloc[i]['time']
            current_price = float(df.iloc[i]['close'])
            
            # 1. Technical Regime at this point in time
            # We must only give the detector data up to 'i'
            data_subset = df.iloc[max(0, i-100) : i+1].copy()
            indicators = self.detector.calculate_indicators(data_subset)
            
            # Simple manual detection logic for backtest
            last = indicators.iloc[-1]
            adx = last['adx']
            price = last['close']
            sma20 = last['sma20']
            
            regime = "NEUTRAL"
            if adx > 25:
                regime = "TRENDING_BULLISH" if price > sma20 else "TRENDING_BEARISH"
            
            # 2. Check Hypothetical Outcome (Next 8 bars / 2 hours)
            future_data = df.iloc[i+1 : i+9]
            close_future = float(df.iloc[i+8]['close'])
            
            outcome = "NEUTRAL"
            pnl_pips = 0.0
            
            if "BULLISH" in regime:
                pnl_pips = float(close_future - current_price)
                outcome = "WIN" if pnl_pips > 0 else "LOSS"
            elif "BEARISH" in regime:
                pnl_pips = float(current_price - close_future)
                outcome = "WIN" if pnl_pips > 0 else "LOSS"
                
            results.append({
                "time": str(current_time),
                "price": current_price,
                "regime": regime,
                "outcome": outcome,
                "pnl": pnl_pips
            })

        # Summary Analysis
        total = len(results)
        wins = sum(1 for r in results if r['outcome'] == 'WIN')
        losses = sum(1 for r in results if r['outcome'] == 'LOSS')
        valid_trades = wins + losses
        win_rate = (wins / valid_trades) * 100 if valid_trades > 0 else 0
        
        print(f"📊 Simulation Complete for {self.symbol}")
        print(f"   Signals: {valid_trades} | Win Rate: {win_rate:.2f}%")
        
        self.generate_report(results, win_rate)

    def generate_report(self, results, win_rate):
        """Save results for AI review."""
        os.makedirs("analysis", exist_ok=True)
        report_path = f"analysis/BACKTEST_{self.symbol}_{datetime.now().strftime('%H%M%S')}.json"
        
        # Filter for only valid trades to minimize JSON size
        valid_results = [r for r in results if r['outcome'] != 'NEUTRAL']
        
        with open(report_path, "w") as f:
            json.dump({
                "symbol": self.symbol,
                "win_rate": round(win_rate, 2),
                "trades": valid_results[:30] # Limit for AI ingestion
            }, f, indent=2)
        print(f"✅ Backtest data saved for AI Post-Mortem: {report_path}")

if __name__ == "__main__":
    import MetaTrader5 as mt5
    if not mt5.initialize():
        print("MT5 Init Failed")
        sys.exit()
        
    if len(sys.argv) > 1:
        tester = StrategicBacktester(sys.argv[1])
        tester.run_simulation()
    else:
        for sym in ["GOLD", "US100Cash"]:
            tester = StrategicBacktester(sym)
            tester.run_simulation()
    mt5.shutdown()
