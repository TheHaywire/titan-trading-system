import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
from bisect import bisect_right

def get_pivots(series, window=5):
    peaks = (series > series.shift(1)) & (series > series.shift(-1))
    troughs = (series < series.shift(1)) & (series < series.shift(-1))
    for i in range(1, window + 1):
        peaks &= (series > series.shift(i)) & (series > series.shift(-i))
        troughs &= (series < series.shift(i)) & (series < series.shift(-i))
    return peaks, troughs

class ComprehensiveDivergence_Strategy(BaseStrategy):
    def __init__(self, indicator_name='rsi', div_type='regular', lookup_period=60, pivot_window=3):
        super().__init__(f"Div_{indicator_name}_{div_type}")
        self.indicator_name = indicator_name
        self.div_type = div_type
        self.lookup_period = lookup_period
        self.pivot_window = pivot_window
        self.p_troughs = []
        self.p_peaks = []
        
    def calculate_indicators(self, df):
        df = add_indicators(df)
        if 'ao' not in df.columns:
            median = (df['high'] + df['low']) / 2
            df['ao'] = median.rolling(5).mean() - median.rolling(34).mean()
        
        col = 'rsi' if self.indicator_name == 'rsi' else 'macd_hist' if self.indicator_name == 'macd' else 'ao'
        p_p, p_t = get_pivots(df['close'], self.pivot_window)
        
        self.p_troughs = df[p_t].index.tolist()
        self.p_peaks = df[p_p].index.tolist()
        return df

    def analyze(self, df):
        idx = len(df) - 1
        if idx < self.lookup_period: return None
        curr = df.iloc[-1]
        col = 'rsi' if self.indicator_name == 'rsi' else 'macd_hist' if self.indicator_name == 'macd' else 'ao'
        
        # Bullish
        sig = self._check_bullish(df, col, idx)
        if sig:
            return {'direction': 'BUY', 'stop_loss': df['low'].tail(20).min() - curr['atr'], 
                    'take_profit': curr['close'] + curr['atr'] * 3, 'reason': f"{self.indicator_name} Bullish {sig}"}
        
        # Bearish
        sig = self._check_bearish(df, col, idx)
        if sig:
            return {'direction': 'SELL', 'stop_loss': df['high'].tail(20).max() + curr['atr'], 
                    'take_profit': curr['close'] - curr['atr'] * 3, 'reason': f"{self.indicator_name} Bearish {sig}"}
        return None

    def _check_bullish(self, df, col, current_idx):
        pos = bisect_right(self.p_troughs, current_idx)
        if pos < 2: return None
        idx1, idx2 = self.p_troughs[pos-2], self.p_troughs[pos-1]
        if current_idx - idx2 > 5: return None
        
        p1, p2 = df.iloc[idx1], df.iloc[idx2]
        ind1, ind2 = p1[col], p2[col]
        
        if self.div_type in ['regular', 'both'] and p2['close'] < p1['close'] and ind2 > ind1:
            return "Regular"
        if self.div_type in ['hidden', 'both'] and p2['close'] > p1['close'] and ind2 < ind1:
            return "Hidden"
        return None

    def _check_bearish(self, df, col, current_idx):
        pos = bisect_right(self.p_peaks, current_idx)
        if pos < 2: return None
        idx1, idx2 = self.p_peaks[pos-2], self.p_peaks[pos-1]
        if current_idx - idx2 > 5: return None
        
        p1, p2 = df.iloc[idx1], df.iloc[idx2]
        ind1, ind2 = p1[col], p2[col]
        
        if self.div_type in ['regular', 'both'] and p2['close'] > p1['close'] and ind2 < ind1:
            return "Regular"
        if self.div_type in ['hidden', 'both'] and p2['close'] < p1['close'] and ind2 > ind1:
            return "Hidden"
        return None

def run_divergence_lab():
    print("🚀 Starting Optimized Divergence Validation Lab...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    timeframes = {"M15": mt5.TIMEFRAME_M15, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1}
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 1, 1)
    
    indicators = ['rsi', 'macd', 'ao']
    div_types = ['regular', 'hidden']
    results_summary = []
    
    for tf_name, tf_val in timeframes.items():
        print(f"\n--- Testing Timeframe: {tf_name} ---")
        engine = BacktestEngine(symbol, tf_val, start_date, end_date)
        for ind in indicators:
            for d_type in div_types:
                strategy = ComprehensiveDivergence_Strategy(indicator_name=ind, div_type=d_type)
                print(f"Testing {ind.upper()} {d_type.capitalize()} Divergence...")
                try:
                    result = engine.run_backtest(strategy)
                    results_summary.append({
                        'TF': tf_name, 'Indicator': ind.upper(), 'Type': d_type.capitalize(),
                        'Trades': result.total_trades, 'WinRate': f"{result.win_rate:.1f}%",
                        'Sharpe': f"{result.sharpe_ratio:.2f}", 'Return%': f"{result.total_return_pct:.1f}%",
                        'MDD%': f"{result.max_drawdown_pct:.1f}%"
                    })
                except Exception as e:
                    print(f"Error {ind} {d_type} on {tf_name}: {e}")

    df_results = pd.DataFrame(results_summary)
    print("\n📊 Divergence Validation Summary:\n", df_results.to_string(index=False))
    df_results.to_markdown("DIVERGENCE_VALIDATION_REPORT.md", index=False)
    mt5.shutdown()

if __name__ == "__main__":
    run_divergence_lab()
