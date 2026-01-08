import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime
from titan_system.backtest.engine import BacktestEngine
from titan_system.backtest.strategy_base import BaseStrategy, add_indicators
import random

# --- RSI ULTRA STRATEGY (The Champion) ---

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
    
    return df

class RSI_Ultra_Strategy(BaseStrategy):
    def __init__(self, variant='stoch_rsi'):
        name = f"RSIUltra_{variant}"
        super().__init__(name)
        self.variant = variant
        self.pivot_window = 3
        self.p_troughs = []
        
    def calculate_indicators(self, df):
        df = add_ultra_rsi_indicators(df)
        peaks, troughs = self._get_pivots(df['close'], self.pivot_window)
        self.p_troughs = df[troughs].index.tolist()
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
                    return {
                        'direction': 'BUY',
                        'stop_loss': df['low'].tail(20).min() - curr['atr'],
                        'take_profit': curr['close'] + curr['atr'] * 3, # 3:1 RR
                        'reason': 'Hidden Scalp'
                    }
        return None

# --- RANDOM CONTROL GROUP (The Scientific Control) ---

class RandomStrategy(BaseStrategy):
    def __init__(self):
        super().__init__("Random_Control")
        
    def calculate_indicators(self, df):
        return add_indicators(df)
        
    def analyze(self, df):
        # 5% chance to enter a trade randomly
        if random.random() < 0.05:
            direction = 'BUY' if random.random() > 0.5 else 'SELL'
            curr = df.iloc[-1]
            return {
                'direction': direction,
                'stop_loss': curr['close'] - curr['atr'] if direction == 'BUY' else curr['close'] + curr['atr'],
                'take_profit': curr['close'] + curr['atr'] * 2 if direction == 'BUY' else curr['close'] - curr['atr'] * 2,
                'reason': 'Random Chance'
            }
        return None

# --- VERIFICATION RUNNER ---

def run_scientific_verification():
    print("STARTING DEEP HISTORY STRESS TEST (2020-2026)...")
    if not mt5.initialize(): return
    
    symbol = "GOLD"
    timeframes = {"H1": mt5.TIMEFRAME_H1} 
    
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2026, 1, 1)
    
    results = []
    
    for tf_name, tf_val in timeframes.items():
        print(f"\n--- Verifying Timeframe: {tf_name} (6-Year Scan) ---")
        try:
            engine = BacktestEngine(symbol, tf_val, start_date, end_date)
        except Exception as e:
            print(f"Data fetch error for {tf_name}: {e}")
            continue
        
        # 1. Run Strategy
        strat = RSI_Ultra_Strategy('stoch_rsi')
        print(f"Testing Strategy: {strat.name}...")
        res_strat = engine.run_backtest(strat)
        
        # 2. Run Control (Random)
        control = RandomStrategy()
        print(f"Testing Control: {control.name}...")
        res_control = engine.run_backtest(control)
        
        results.append({
            'TF': tf_name,
            'Type': 'STRATEGY',
            'Name': strat.name,
            'Sharpe': res_strat.sharpe_ratio,
            'WinRate': f"{res_strat.win_rate:.1f}%",
            'Return': f"{res_strat.total_return_pct:.1f}%",
            'Trades': res_strat.total_trades,
            'MDD': f"{res_strat.max_drawdown_pct:.1f}%"
        })
        
        results.append({
            'TF': tf_name,
            'Type': 'CONTROL',
            'Name': 'Random Walk',
            'Sharpe': res_control.sharpe_ratio,
            'WinRate': f"{res_control.win_rate:.1f}%",
            'Return': f"{res_control.total_return_pct:.1f}%",
            'Trades': res_control.total_trades,
            'MDD': f"{res_control.max_drawdown_pct:.1f}%"
        })
        
        # 3. REGIME ANALYSIS (Year-by-Year Breakdown)
        print(f"\nANNUAL REGIME BREAKDOWN ({tf_name}):")
        trades_df = pd.DataFrame([vars(t) for t in res_strat.trades])
        if not trades_df.empty:
            trades_df['year'] = trades_df['entry_time'].dt.year
            yearly = trades_df.groupby('year')['profit'].sum()
            print(yearly)
            
    df = pd.DataFrame(results)
    print("\n6-YEAR DEEP DATA RESULTS:")
    print(df.to_string(index=False))
    
    # Save Proof
    with open("DEEP_HISTORY_PROOF.md", "w") as f:
        f.write("# 6-YEAR DEEP HISTORY VERIFICATION (2020-2026)\n\n")
        f.write("Testing resiliency across Covid, Inflation, and War regimes.\n\n")
        f.write(df.to_markdown(index=False))
        if 'yearly' in locals():
             f.write("\n\n## Annual Performance:\n")
             f.write(yearly.to_markdown())
        
    mt5.shutdown()

if __name__ == "__main__":
    run_scientific_verification()
