import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
from bisect import bisect_right

# --- ADVANCED RSI CALCULATIONS ---

def add_ultra_rsi_indicators(df):
    """Adds specialized RSI variants and VFI."""
    df = add_indicators(df)
    
    # 1. StochRSI (14, 14, 3, 3)
    rsi = df['rsi']
    rsi_low = rsi.rolling(14).min()
    rsi_high = rsi.rolling(14).max()
    df['stoch_rsi'] = 100 * (rsi - rsi_low) / (rsi_high - rsi_low)
    df['stoch_rsi_k'] = df['stoch_rsi'].rolling(3).mean()
    
    # 2. Smoothed RSI (RSI of localized EMA)
    df['ema_close'] = df['close'].ewm(span=5).mean()
    # Simple RSI calculation for the EMA_Close
    delta = df['ema_close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['smoothed_rsi'] = 100 - (100 / (1 + rs))
    
    # 3. Multi-Period RSI
    df['rsi_9'] = df['close'].diff().rolling(9).apply(lambda x: 100 - (100 / (1 + (x[x > 0].mean() / -x[x < 0].mean()))), raw=False)
    df['rsi_21'] = df['close'].diff().rolling(21).apply(lambda x: 100 - (100 / (1 + (x[x > 0].mean() / -x[x < 0].mean()))), raw=False)

    # 4. Volume Flow Indicator (VFI) - Simplified
    # VFI = EMA( (Inter_Bar_Vol * Direction) / Avg_Vol, 130 )
    typical = (df['high'] + df['low'] + df['close']) / 3
    inter = typical.diff()
    v_avg = df['tick_volume'].rolling(130).mean()
    mf = (df['tick_volume'] * np.sign(inter)) / v_avg
    df['vfi'] = mf.ewm(span=130).mean()
    
    return df

# --- TRENDLINE DETECTION ---

def detect_rsi_trendline_break(df, col='rsi', window=20):
    """
    Detects if RSI has broken a trendline connecting its recent peaks/troughs.
    This is used as a timing trigger for divergence.
    """
    # Placeholder for geometric trendline logic
    # For backtest efficiency, we'll use a local peak break
    res = pd.Series(index=df.index, data=False)
    if len(df) < window: return res
    
    # If current RSI is above the high of the last 10 RSI peaks
    # We simulate a "Trendline Break" of the momentum resistance
    rsi_peaks = df[col].rolling(window).max().shift(1)
    res = (df[col] > rsi_peaks) & (df[col].shift(1) <= rsi_peaks)
    return res

# --- RSI ULTRA STRATEGY ---

class RSI_Ultra_Strategy(BaseStrategy):
    def __init__(self, 
                 variant='stoch_rsi', 
                 use_trendline=False, 
                 use_multi=False, 
                 use_vfi=False):
        
        name = f"RSIUltra_{variant}"
        if use_trendline: name += "_TL"
        if use_multi: name += "_Multi"
        if use_vfi: name += "_VFI"
        
        super().__init__(name)
        self.variant = variant
        self.use_trendline = use_trendline
        self.use_multi = use_multi
        self.use_vfi = use_vfi
        
        self.pivot_window = 3
        self.p_troughs = []
        self.p_peaks = []
        
    def calculate_indicators(self, df):
        df = add_ultra_rsi_indicators(df)
        
        # Determine target column
        col = 'stoch_rsi_k' if self.variant == 'stoch_rsi' else 'smoothed_rsi' if self.variant == 'smoothed' else 'rsi'
        
        # Price pivots
        peaks, troughs = self._get_pivots(df['close'], self.pivot_window)
        self.p_troughs = df[troughs].index.tolist()
        self.p_peaks = df[peaks].index.tolist()
        
        # Add trendline break signal
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
        
        col = 'stoch_rsi_k' if self.variant == 'stoch_rsi' else 'smoothed_rsi' if self.variant == 'smoothed' else 'rsi'
        
        # 1. Multi-Period RSI Confluence
        if self.use_multi:
            # Check if RSI 9, 14, and 21 are all trending in same direction
            if not (df['rsi_9'].iloc[-1] > df['rsi_9'].iloc[-2] and 
                    df['rsi'].iloc[-1] > df['rsi'].iloc[-2] and 
                    df['rsi_21'].iloc[-1] > df['rsi_21'].iloc[-2]):
                return None

        # 2. VFI Filter (Institutional Flow)
        if self.use_vfi:
            if curr['vfi'] < 0: return None # Only buy if VFI is positive (Bullish flow)

        # 3. Detect Divergence
        sig = self._check_divergence(df, col, idx)
        
        if sig:
            # 4. Trendline Trigger (Optional)
            if self.use_trendline:
                if not curr['tl_break']: return None # Only enter on the break
            
            direction = 'BUY' if 'Bullish' in sig else 'SELL'
            return {
                'direction': direction,
                'stop_loss': df['low'].tail(20).min() - curr['atr'] if direction == 'BUY' else df['high'].tail(20).max() + curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 4 if direction == 'BUY' else curr['close'] - curr['atr'] * 4,
                'reason': f"{sig} ({self.variant})"
            }
            
        return None

    def _check_divergence(self, df, col, current_idx):
        # Only use pivots that are already confirmed
        confirmed_troughs = [t for t in self.p_troughs if t <= current_idx - self.pivot_window]
        
        # Hidden Bullish (Trend Continuation)
        if len(confirmed_troughs) >= 2:
            idx1, idx2 = confirmed_troughs[-2], confirmed_troughs[-1]
            # Must be within 7 bars of confirmation
            if current_idx - (idx2 + self.pivot_window) <= 7:
                p1, p2 = df.iloc[idx1], df.iloc[idx2]
                ind1, ind2 = p1[col], p2[col]
                if p2['close'] > p1['close'] and ind2 < ind1:
                    return "Bullish Hidden"
                    
        return None

# --- RUNNER ---

def run_rsi_ultra_lab():
    print("🚀 Starting RSI Ultra Deep Dive (Divergence 3.0)...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    timeframes = {"H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4}
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2026, 1, 1)
    
    test_cases = [
        {'variant': 'stoch_rsi', 'tl': False, 'multi': False, 'vfi': False},
        {'variant': 'stoch_rsi', 'tl': True, 'multi': False, 'vfi': False},
        {'variant': 'smoothed', 'tl': False, 'multi': False, 'vfi': False},
        {'variant': 'stoch_rsi', 'tl': False, 'multi': True, 'vfi': False},
        {'variant': 'stoch_rsi', 'tl': True, 'multi': True, 'vfi': True},
    ]
    
    results = []
    
    for tf_name, tf_val in timeframes.items():
        print(f"\n--- Timeframe: {tf_name} ---")
        engine = BacktestEngine(symbol, tf_val, start_date, end_date)
        
        for case in test_cases:
            strategy = RSI_Ultra_Strategy(
                variant=case['variant'],
                use_trendline=case['tl'],
                use_multi=case['multi'],
                use_vfi=case['vfi']
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
    print("\n📊 RSI Ultra Summary:")
    print(df_results.to_string(index=False))
    
    df_results.to_markdown("RSI_ULTRA_REPORT.md", index=False)
    mt5.shutdown()

if __name__ == "__main__":
    run_rsi_ultra_lab()
