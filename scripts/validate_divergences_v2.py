import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from titan_system.backtest.engine import BacktestEngine, Trade, BacktestResult
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
from bisect import bisect_right

# --- UTILS ---

def get_pivots(series, window=5):
    """Find local peaks and troughs with a fixed window."""
    peaks = (series > series.shift(1)) & (series > series.shift(-1))
    troughs = (series < series.shift(1)) & (series < series.shift(-1))
    for i in range(1, window + 1):
        peaks &= (series > series.shift(i)) & (series > series.shift(-i))
        troughs &= (series < series.shift(i)) & (series < series.shift(-i))
    return peaks, troughs

def add_advanced_indicators(df):
    """Adds Stochastic, Williams %R, OBV, and Volume Profile metrics."""
    df = add_indicators(df) # Common ones
    
    # Awesome Oscillator (AO)
    median = (df['high'] + df['low']) / 2
    df['ao'] = median.rolling(5).mean() - median.rolling(34).mean()
    
    # Stochastic (14, 3, 3)
    low_min = df['low'].rolling(14).min()
    high_max = df['high'].rolling(14).max()
    df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
    df['stoch_d'] = df['stoch_k'].rolling(3).mean()
    
    # Williams %R
    df['williams_r'] = -100 * (high_max - df['close']) / (high_max - low_min)
    
    # OBV (On-Balance Volume)
    df['obv'] = (np.sign(df['close'].diff()) * df['tick_volume']).fillna(0).cumsum()
    
    # Volume Profile (Simple Approximation: POC = Price with highest volume in last 100 bars)
    # This is a heavy calculation, we'll simplify for backtest
    df['poc'] = df['close'].rolling(100).apply(lambda x: x.iloc[np.argmax(df['tick_volume'].iloc[x.index.start:x.index.stop])], raw=False)
    
    return df

# --- ADVANCED DIVERGENCE STRATEGY ---

class AdvancedDivergence_Strategy(BaseStrategy):
    def __init__(self, 
                 indicators=['rsi'], 
                 mode='any', # 'any' or 'all' for multivariate
                 div_type='regular', # 'regular' or 'hidden'
                 vol_filter=False,
                 mtf_filter=False):
        
        name = f"AdvDiv_{'_'.join(indicators)}_{mode}_{div_type}"
        if vol_filter: name += "_Vol"
        if mtf_filter: name += "_MTF"
        
        super().__init__(name)
        self.target_indicators = indicators
        self.mode = mode
        self.div_type = div_type
        self.vol_filter = vol_filter
        self.mtf_filter = mtf_filter
        
        self.pivot_window = 3
        self.p_troughs = []
        self.p_peaks = []
        
    def calculate_indicators(self, df):
        df = add_advanced_indicators(df)
        
        # Price pivots
        p_p, p_t = get_pivots(df['close'], self.pivot_window)
        self.p_troughs = df[p_t].index.tolist()
        self.p_peaks = df[p_p].index.tolist()
        
        # Weekly Trend (Approximate using 200 EMA on 5x current data)
        # Note: In a real MTF engine this is cleaner, here we simulate
        df['weekly_ema'] = df['close'].ewm(span=200*5).mean()
        
        return df

    def analyze(self, df):
        idx = len(df) - 1
        if idx < 100: return None
        curr = df.iloc[-1]
        
        # 1. MTF Check
        if self.mtf_filter:
            if self.div_type == 'hidden': # Continuation
                if curr['close'] < curr['weekly_ema']: return None # Only buy in uptrend
        
        # 2. Volume Filter (POC)
        if self.vol_filter:
            # Only buy if close is near or below POC (Value)
            if curr['close'] > curr['poc'] * 1.01: return None 
            
        results = []
        for ind_name in self.target_indicators:
            col = self._get_col(ind_name)
            sig = self._check_divergence(df, col, idx)
            results.append(sig)
            
        # Multivariate Logic
        if self.mode == 'all':
            combined_sig = results[0] if all(r and r == results[0] for r in results) else None
        else: # 'any'
            combined_sig = next((r for r in results if r), None)
            
        if combined_sig:
            direction = 'BUY' if 'Bullish' in combined_sig else 'SELL'
            return {
                'direction': direction,
                'stop_loss': df['low'].tail(20).min() - curr['atr'] if direction == 'BUY' else df['high'].tail(20).max() + curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 3 if direction == 'BUY' else curr['close'] - curr['atr'] * 3,
                'reason': f"{combined_sig} ({self.mode})"
            }
            
        return None

    def _get_col(self, name):
        mapping = {
            'rsi': 'rsi',
            'macd': 'macd_hist',
            'ao': 'ao',
            'stoch': 'stoch_k',
            'williams': 'williams_r',
            'obv': 'obv'
        }
        return mapping.get(name, 'rsi')

    def _check_divergence(self, df, col, current_idx):
        # Only use pivots that are already confirmed (at least pivot_window bars in the past)
        confirmed_troughs = [t for t in self.p_troughs if t <= current_idx - self.pivot_window]
        
        # Bullish
        if len(confirmed_troughs) >= 2:
            idx1, idx2 = confirmed_troughs[-2], confirmed_troughs[-1]
            # Window check: signal must be fresh (within 5 bars of confirmation)
            # We check distance from current_idx to the bar where it was confirmed (idx2 + window)
            if current_idx - (idx2 + self.pivot_window) <= 5:
                p1, p2 = df.iloc[idx1], df.iloc[idx2]
                ind1, ind2 = p1[col], p2[col]
                if self.div_type == 'regular' and p2['close'] < p1['close'] and ind2 > ind1:
                    return "Bullish Regular"
                if self.div_type == 'hidden' and p2['close'] > p1['close'] and ind2 < ind1:
                    return "Bullish Hidden"
                    
        # Bearish
        confirmed_peaks = [p for p in self.p_peaks if p <= current_idx - self.pivot_window]
        if len(confirmed_peaks) >= 2:
            idx1, idx2 = confirmed_peaks[-2], confirmed_peaks[-1]
            if current_idx - (idx2 + self.pivot_window) <= 5:
                p1, p2 = df.iloc[idx1], df.iloc[idx2]
                ind1, ind2 = p1[col], p2[col]
                if self.div_type == 'regular' and p2['close'] > p1['close'] and ind2 < ind1:
                    return "Bearish Regular"
                if self.div_type == 'hidden' and p2['close'] < p1['close'] and ind2 > ind1:
                    return "Bearish Hidden"
                    
        return None

# --- RUNNER ---

def run_advanced_lab():
    print("🚀 Starting Advanced Divergence Validation (Divergence 2.0)...")
    if not mt5.initialize(): 
        print("MT5 Init Failed")
        return
    
    symbol = "GOLD"
    timeframes = {"H4": mt5.TIMEFRAME_H4, "D1": mt5.TIMEFRAME_D1} # Deep dive on high timeframes
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 1, 1)
    
    test_cases = [
        # 1. New Indicators
        {'ind': ['stoch'], 'mode': 'any', 'type': 'regular'},
        {'ind': ['stoch'], 'mode': 'any', 'type': 'hidden'},
        {'ind': ['williams'], 'mode': 'any', 'type': 'regular'},
        {'ind': ['obv'], 'mode': 'any', 'type': 'regular'},
        
        # 2. Multivariate Confluence
        {'ind': ['rsi', 'macd'], 'mode': 'all', 'type': 'regular'},
        {'ind': ['rsi', 'macd'], 'mode': 'all', 'type': 'hidden'},
        {'ind': ['macd', 'ao'], 'mode': 'all', 'type': 'hidden'},
        
        # 3. Institutional Layering
        {'ind': ['macd'], 'mode': 'any', 'type': 'hidden', 'vol': True},
        {'ind': ['macd'], 'mode': 'any', 'type': 'hidden', 'mtf': True},
        {'ind': ['macd'], 'mode': 'any', 'type': 'hidden', 'vol': True, 'mtf': True},
    ]
    
    results = []
    
    for tf_name, tf_val in timeframes.items():
        print(f"\n--- Timeframe: {tf_name} ---")
        engine = BacktestEngine(symbol, tf_val, start_date, end_date)
        
        for case in test_cases:
            strategy = AdvancedDivergence_Strategy(
                indicators=case['ind'],
                mode=case['mode'],
                div_type=case['type'],
                vol_filter=case.get('vol', False),
                mtf_filter=case.get('mtf', False)
            )
            
            print(f"Testing {strategy.name}...")
            try:
                res = engine.run_backtest(strategy)
                results.append({
                    'TF': tf_name,
                    'Strategy': strategy.name,
                    'Trades': res.total_trades,
                    'WinRate': f"{res.win_rate:.1f}%",
                    'Sharpe': res.sharpe_ratio,
                    'Return%': f"{res.total_return_pct:.1f}%",
                    'MDD%': f"{res.max_drawdown_pct:.1f}%"
                })
            except Exception as e:
                print(f"Error: {e}")

    df_results = pd.DataFrame(results)
    print("\n📊 Advanced Divergence Summary:")
    print(df_results.to_string(index=False))
    
    df_results.to_markdown("ADVANCED_DIVERGENCE_REPORT.md", index=False)
    mt5.shutdown()

if __name__ == "__main__":
    run_advanced_lab()
