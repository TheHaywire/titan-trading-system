"""
Titan Hypothesis Validator
==========================
Compares the baseline Sentinel logic against the AI-suggested 
improvements (2-bar confirmation + Volatility Gate).
"""

import os
import sys
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class HypothesisValidator:
    def __init__(self, symbol: str, days: int = 15):
        self.symbol = symbol
        self.days = days
        
    def get_data(self):
        if not mt5.initialize(): return None
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_H1, 0, 24 * self.days)
        if rates is None: return None
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate Indicators
        df['sma20'] = df['close'].rolling(20).mean()
        df['atr'] = self.calculate_atr(df)
        df['adx'] = self.calculate_adx(df)
        return df

    def calculate_atr(self, df, n=14):
        tr = pd.DataFrame()
        tr['h-l'] = df['high'] - df['low']
        tr['h-pc'] = abs(df['high'] - df['close'].shift())
        tr['l-pc'] = abs(df['low'] - df['close'].shift())
        tr['tr'] = tr[['h-l', 'h-pc', 'l-pc']].max(axis=1)
        return tr['tr'].rolling(n).mean()

    def calculate_adx(self, df, n=14):
        # Simplified ADX for validation
        plus_dm = df['high'].diff()
        minus_dm = df['low'].diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm > 0] = 0
        
        tr = self.calculate_atr(df, n)
        plus_di = 100 * (plus_dm.rolling(n).mean() / tr)
        minus_di = 100 * (abs(minus_dm).rolling(n).mean() / tr)
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di))
        return dx.rolling(n).mean()

    def run_comparison(self):
        df = self.get_data()
        if df is None: return
        
        baseline_stats = {"wins": 0, "losses": 0, "pnl": 0.0}
        titan_pro_stats = {"wins": 0, "losses": 0, "pnl": 0.0}
        
        for i in range(50, len(df) - 5):
            curr = df.iloc[i]
            prev = df.iloc[i-1]
            future_price = df.iloc[i+3]['close'] # 3-hour exit
            
            # --- BASELINE LOGIC ---
            baseline_regime = "NEUTRAL"
            if curr['adx'] > 25:
                baseline_regime = "LONG" if curr['close'] > curr['sma20'] else "SHORT"
            
            if baseline_regime != "NEUTRAL":
                pnl = (future_price - curr['close']) if baseline_regime == "LONG" else (curr['close'] - future_price)
                baseline_stats["pnl"] += pnl
                if pnl > 0: baseline_stats["wins"] += 1
                else: baseline_stats["losses"] += 1

            # --- TITAN PRO LOGIC (AI Hypothesis) ---
            # 1. Volatility Gate: ATR must be expanding or > average
            avg_atr = df['atr'].iloc[i-20:i].mean()
            vol_gate = curr['atr'] > avg_atr
            
            # 2. 2-Bar Confirmation: Regime must be the same for 2 bars
            regime_now = "LONG" if curr['close'] > curr['sma20'] else "SHORT"
            regime_prev = "LONG" if prev['close'] > prev['sma20'] else "SHORT"
            confirmed = (regime_now == regime_prev) and (curr['adx'] > 25)
            
            if confirmed and vol_gate:
                pnl = (future_price - curr['close']) if regime_now == "LONG" else (curr['close'] - future_price)
                titan_pro_stats["pnl"] += pnl
                if pnl > 0: titan_pro_stats["wins"] += 1
                else: titan_pro_stats["losses"] += 1

        report = []
        report.append(f"\n[HYPOTHESIS VALIDATION: {self.symbol} ({self.days} Days)]")
        report.append("-" * 50)
        report.append(self.format_stats("BASELINE (Current)", baseline_stats))
        report.append(self.format_stats("TITAN PRO (AI SUGGESTED)", titan_pro_stats))
        
        full_report = "\n".join(report)
        print(full_report)
        
        with open(f"analysis/VALIDATION_{self.symbol}.md", "w") as f:
            f.write(full_report)
        
    def format_stats(self, name, s):
        total = s['wins'] + s['losses']
        wr = (s['wins'] / total * 100) if total > 0 else 0
        return f"{name}:\n   Win Rate: {wr:.2f}% | Total Trades: {total} | PnL: {s['pnl']:.4f}"

if __name__ == "__main__":
    if not mt5.initialize():
        print("MT5 Init Failed")
        sys.exit()
    for sym in ["GOLD", "BTCUSD", "US100Cash"]:
        v = HypothesisValidator(sym, days=30)
        v.run_comparison()
    mt5.shutdown()
