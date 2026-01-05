"""
CONTEXT SCORE VALIDATOR
Statistical proof that our 'Advanced TA' Context Score actually predicts market behavior.
"""

import sys
import os
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.append(os.getcwd())

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import ta
from rich.console import Console
from rich.table import Table

console = Console()

def fetch_data(symbol, bars=5000):
    if not mt5.initialize():
        return None
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df

def calculate_context_score(df):
    """
    Calculates the Composite Context Score (0-100) based on TITAN_AUTONOMOUS_BEHAVIOR_SPEC.md
    """
    c = df['close']
    h = df['high']
    l = df['low']
    
    # --- A. TREND VECTOR (50 pts) ---
    # 1. Long Term: Price > SMA200 (+20)
    sma200 = ta.trend.sma_indicator(c, window=200)
    score_trend_lt = np.where(c > sma200, 20, 0)
    
    # 2. Strength: ADX > 25 (+15)
    adx = ta.trend.ADXIndicator(h, l, c, window=14).adx()
    score_trend_str = np.where(adx > 25, 15, 0)
    
    # 3. Alignment: EMA8 > EMA21 > EMA50 (+15)
    ema8 = ta.trend.ema_indicator(c, window=8)
    ema21 = ta.trend.ema_indicator(c, window=21)
    ema50 = ta.trend.ema_indicator(c, window=50)
    score_trend_align = np.where((ema8 > ema21) & (ema21 > ema50), 15, 0)
    
    # --- B. VOLATILITY VECTOR (30 pts) ---
    # 1. Cycle: ATR > SMA(ATR, 20) (+15)
    atr = ta.volatility.AverageTrueRange(h, l, c, window=14).average_true_range()
    sma_atr = atr.rolling(20).mean()
    score_vol_cycle = np.where(atr > sma_atr, 15, 0)
    
    # 2. Bandwidth: Not Squeezed (+15) - Simplified to just "Not Low"
    # Using simple ATR/Price ratio as proxy for bandwidth relative to history
    # Or strict Bollinger Band Width
    bb = ta.volatility.BollingerBands(c, window=20, window_dev=2)
    bbw = bb.bollinger_wband()
    # Normalize BBW? For now, let's use a simple threshold or standard deviation logic
    # Let's stick to the spec: "Not Squeezed". Let's say BBW > 20-day mean of BBW? 
    # Spec said > 0.05. For ETH/BTC 0.05 is tiny. For Forex it's huge. 
    # Let's use robust: BBW > Rolling Mean BBW (Expansion)
    bbw_mean = bbw.rolling(20).mean()
    score_vol_bw = np.where(bbw > bbw_mean, 15, 0)
    
    # --- C. STRUCTURE VECTOR (20 pts) ---
    # 1. Breakout: Price > 20-Day High (+10)
    high20 = h.rolling(20).max().shift(1) # Shift 1 to avoid lookahead bias? 
    # Actually, we want to know if TODAY is breaking out. 
    # If using Close > Prev High20.
    score_struct_brk = np.where(c > high20, 10, 0)
    
    # 2. Momentum: RSI 50-70 (+10)
    rsi = ta.momentum.rsi(c, window=14)
    score_struct_mom = np.where((rsi > 50) & (rsi < 70), 10, 0)
    
    # --- TOTAL SCORE ---
    total_score = (score_trend_lt + score_trend_str + score_trend_align + 
                   score_vol_cycle + score_vol_bw + 
                   score_struct_brk + score_struct_mom)
                   
    df['context_score'] = total_score
    
    # Next Day Return (for validation)
    df['next_return'] = c.shift(-1) / c - 1
    
    return df

def validate_asset(symbol):
    console.print(f"Fetching data for {symbol}...")
    df = fetch_data(symbol)
    if df is None: return
    
    df = calculate_context_score(df)
    df.dropna(inplace=True)
    
    # BUCKET ANALYSIS
    buckets = {
        'PRISTINE BULL (80-100)': df[(df['context_score'] >= 80)],
        'MILD BULL (60-79)':      df[(df['context_score'] >= 60) & (df['context_score'] < 80)],
        'NEUTRAL/CHOP (40-59)':   df[(df['context_score'] >= 40) & (df['context_score'] < 60)],
        'BEAR/CRASH (0-39)':      df[(df['context_score'] < 40)]
    }
    
    print(f"\nCTX VALIDATION: {symbol}")
    print(f"{'BUCKET':<25} | {'N':<5} | {'NEXT_RET':<10} | {'WIN_RATE':<10} | {'ANN_RET':<10}")
    print("-" * 75)
    
    for name, bucket in buckets.items():
        if len(bucket) == 0: continue
        avg_ret = bucket['next_return'].mean() * 100
        win_rate = (bucket['next_return'] > 0).mean() * 100
        
        # Simple annualization
        ann_ret = (1 + bucket['next_return'].mean()) ** 365 - 1
        ann_ret_pct = ann_ret * 100
        
        print(f"{name:<25} | {len(bucket):<5} | {avg_ret:6.2f}%   | {win_rate:6.1f}%   | {ann_ret_pct:6.0f}%")
        
    print("\n")

if __name__ == "__main__":
    validate_asset("ETHUSD")
    validate_asset("BTCUSD")
    validate_asset("GOLD")
    mt5.shutdown()
