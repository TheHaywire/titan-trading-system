import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
import time

# --- REUSING RSI ULTRA INDICATOR LOGIC ---

def add_ultra_rsi_indicators(df):
    """Adds specialized RSI variants and VFI."""
    df = add_indicators(df)
    
    rsi = df['rsi']
    # StochRSI
    rsi_low = rsi.rolling(14).min()
    rsi_high = rsi.rolling(14).max()
    df['stoch_rsi'] = 100 * (rsi - rsi_low) / (rsi_high - rsi_low)
    df['stoch_rsi_k'] = df['stoch_rsi'].rolling(3).mean()
    
    # Smoothed RSI
    df['ema_close'] = df['close'].ewm(span=5).mean()
    delta = df['ema_close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['smoothed_rsi'] = 100 - (100 / (1 + rs))
    
    # Volume Flow (Simplified)
    typical = (df['high'] + df['low'] + df['close']) / 3
    inter = typical.diff()
    v_avg = df['tick_volume'].rolling(130).mean()
    mf = (df['tick_volume'] * np.sign(inter)) / v_avg
    df['vfi'] = mf.ewm(span=130).mean()
    
    return df

def detect_rsi_trendline_break(df, col='rsi', window=20):
    res = pd.Series(index=df.index, data=False)
    if len(df) < window: return res
    rsi_peaks = df[col].rolling(window).max().shift(1)
    res = (df[col] > rsi_peaks) & (df[col].shift(1) <= rsi_peaks)
    return res

class RSI_Ultra_Strategy(BaseStrategy):
    def __init__(self, variant='stoch_rsi', use_trendline=False):
        name = f"Scalp_{variant}"
        if use_trendline: name += "_TL"
        super().__init__(name)
        self.variant = variant
        self.use_trendline = use_trendline
        self.pivot_window = 3
        self.p_troughs = []
        
    def calculate_indicators(self, df):
        df = add_ultra_rsi_indicators(df)
        peaks, troughs = self._get_pivots(df['close'], self.pivot_window)
        self.p_troughs = df[troughs].index.tolist()
        col = 'stoch_rsi_k' if self.variant == 'stoch_rsi' else 'smoothed_rsi'
        df['tl_break'] = detect_rsi_trendline_break(df, col)
        return df

    def _get_pivots(self, series, window=5):
        peaks = (series > series.shift(1)) & (series > series.shift(-1))
        troughs = (series < series.shift(1)) & (series < series.shift(-1))
        for i in range(1, window + 1):
            peaks &= (series > series.shift(i)) & (series > series.shift(-i))
            troughs &= (series < series.shift(i)) & (series < series.shift(-i))
        return peaks, troughs

    def analyze(self, df):
        idx = len(df) - 1
        if idx < 100: return None
        curr = df.iloc[-1]
        
        col = 'stoch_rsi_k' if self.variant == 'stoch_rsi' else 'smoothed_rsi'
        
        # Check Hidden Divergence
        confirmed_troughs = [t for t in self.p_troughs if t <= idx - self.pivot_window]
        if len(confirmed_troughs) >= 2:
            idx1, idx2 = confirmed_troughs[-2], confirmed_troughs[-1]
            if idx - (idx2 + self.pivot_window) <= 7:
                p1, p2 = df.iloc[idx1], df.iloc[idx2]
                if p2['close'] > p1['close'] and p2[col] < p1[col]:
                    
                    # Trendline Trigger Check
                    if self.use_trendline:
                        if not curr['tl_break']: return None
                    
                    return {
                        'direction': 'BUY',
                        'stop_loss': df['low'].tail(20).min() - curr['atr'],
                        'take_profit': curr['close'] + curr['atr'] * 3, # 3:1 RR for scalping
                        'reason': 'Hidden Scalp'
                    }
        return None

def run_scalping_test():
    print("🚀 Starting SCALPING STRESS TEST (M1-H1)...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    
    # USER REQUESTED TIMEFRAMES
    timeframes = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "H1": mt5.TIMEFRAME_H1
    }
    
    start_date = datetime(2025, 6, 1) # Short duration for M1 scalping speed
    end_date = datetime(2026, 1, 1)
    
    test_cases = [
        {'variant': 'stoch_rsi', 'tl': True}, # Precision Entry
        {'variant': 'smoothed', 'tl': False}, # Trend Entry
    ]
    
    results = []
    
    for tf_name, tf_val in timeframes.items():
        print(f"\nScanning Timeframe: {tf_name}")
        engine = BacktestEngine(symbol, tf_val, start_date, end_date)
        
        for case in test_cases:
            strategy = RSI_Ultra_Strategy(case['variant'], case['tl'])
            print(f"Testing {strategy.name} on {tf_name}...")
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
                print(f"Failed: {e}")
                
    df = pd.DataFrame(results)
    print("\n📊 SCALPING RESULTS:")
    print(df.to_string(index=False))
    df.to_markdown("SCALPING_RESULTS.md", index=False)
    mt5.shutdown()

if __name__ == "__main__":
    run_scalping_test()
