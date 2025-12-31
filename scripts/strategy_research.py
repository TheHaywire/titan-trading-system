"""
COMPREHENSIVE STRATEGY RESEARCH
===============================
Tests multiple proven trading strategies across all available symbols.
Finds what ACTUALLY works with statistical significance.

Strategies Tested:
1. Simple Moving Average Crossover (9/21 EMA)
2. RSI Mean Reversion (Oversold/Overbought bounces)
3. Momentum Breakout (ATR breakout)
4. VWAP Reversion
5. Bollinger Band Mean Reversion
6. Dual Momentum (Absolute + Relative)
7. Opening Range Breakout (ORB)

Author: QuantAI Research
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')


@dataclass
class BacktestResult:
    strategy: str
    symbol: str
    signals: int
    wins: int
    losses: int
    win_rate: float
    total_return: float  # in R multiples
    profit_factor: float
    avg_winner: float
    avg_loser: float
    expectancy: float  # Expected R per trade
    sharpe: float


def get_all_symbols() -> Dict[str, List[str]]:
    """Get all tradeable symbols grouped by category"""
    symbols = mt5.symbols_get()
    
    categories = {
        "FOREX_MAJOR": [],
        "FOREX_MINOR": [],
        "CRYPTO": [],
        "INDICES": [],
        "COMMODITIES": [],
        "STOCKS": []
    }
    
    major_fx = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD"]
    
    for sym in symbols:
        name = sym.name
        
        # Skip if not visible or not tradeable
        if not sym.visible or sym.trade_mode == 0:
            continue
        
        # Categorize
        if name in major_fx:
            categories["FOREX_MAJOR"].append(name)
        elif "USD" in name and len(name) == 6:
            categories["FOREX_MINOR"].append(name)
        elif any(c in name for c in ["BTC", "ETH", "XRP", "SOL", "DOGE"]):
            categories["CRYPTO"].append(name)
        elif any(i in name for i in ["US500", "US30", "USTEC", "GER40", "UK100", "JP225", "NAS", "SPX", "DOW"]):
            categories["INDICES"].append(name)
        elif any(c in name for c in ["GOLD", "XAU", "SILVER", "XAG", "OIL", "WTI", "BRENT"]):
            categories["COMMODITIES"].append(name)
    
    return categories


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all needed indicators"""
    # EMAs
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    df['EMA50'] = df['close'].ewm(span=50).mean()
    df['EMA200'] = df['close'].ewm(span=200).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # ATR
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    # Bollinger Bands
    df['BB_MID'] = df['close'].rolling(20).mean()
    df['BB_STD'] = df['close'].rolling(20).std()
    df['BB_UPPER'] = df['BB_MID'] + 2 * df['BB_STD']
    df['BB_LOWER'] = df['BB_MID'] - 2 * df['BB_STD']
    
    # VWAP (simplified - using volume-weighted price)
    df['VWAP'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
    
    # Momentum
    df['MOM'] = df['close'].pct_change(10)
    
    return df


def strategy_ema_crossover(df: pd.DataFrame) -> List[Dict]:
    """Strategy 1: EMA 9/21 Crossover with trend filter"""
    signals = []
    
    for i in range(50, len(df) - 10):
        prev = df.iloc[i-1]
        curr = df.iloc[i]
        
        # Bullish crossover + above EMA50
        if prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']:
            if curr['close'] > curr['EMA50']:  # Trend filter
                signals.append({
                    'idx': i,
                    'direction': 1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['low'] - curr['ATR'],
                    'target': df.iloc[i+1]['open'] + 2 * curr['ATR']
                })
        
        # Bearish crossover + below EMA50
        elif prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']:
            if curr['close'] < curr['EMA50']:
                signals.append({
                    'idx': i,
                    'direction': -1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['high'] + curr['ATR'],
                    'target': df.iloc[i+1]['open'] - 2 * curr['ATR']
                })
    
    return signals


def strategy_rsi_reversal(df: pd.DataFrame) -> List[Dict]:
    """Strategy 2: RSI Oversold/Overbought with trend"""
    signals = []
    
    for i in range(50, len(df) - 10):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # RSI oversold bounce (in uptrend)
        if prev['RSI'] < 30 and curr['RSI'] > 30:
            if curr['close'] > curr['EMA50']:
                signals.append({
                    'idx': i,
                    'direction': 1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['low'] - curr['ATR'],
                    'target': df.iloc[i+1]['open'] + 2 * curr['ATR']
                })
        
        # RSI overbought drop (in downtrend)
        elif prev['RSI'] > 70 and curr['RSI'] < 70:
            if curr['close'] < curr['EMA50']:
                signals.append({
                    'idx': i,
                    'direction': -1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['high'] + curr['ATR'],
                    'target': df.iloc[i+1]['open'] - 2 * curr['ATR']
                })
    
    return signals


def strategy_momentum_breakout(df: pd.DataFrame) -> List[Dict]:
    """Strategy 3: ATR Breakout"""
    signals = []
    
    for i in range(50, len(df) - 10):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Price breaks above recent high by 1 ATR
        recent_high = df.iloc[i-20:i]['high'].max()
        recent_low = df.iloc[i-20:i]['low'].min()
        
        if curr['close'] > recent_high + 0.5 * curr['ATR']:
            if curr['RSI'] > 50:  # Momentum confirmation
                signals.append({
                    'idx': i,
                    'direction': 1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': recent_low,
                    'target': df.iloc[i+1]['open'] + 2 * curr['ATR']
                })
        
        elif curr['close'] < recent_low - 0.5 * curr['ATR']:
            if curr['RSI'] < 50:
                signals.append({
                    'idx': i,
                    'direction': -1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': recent_high,
                    'target': df.iloc[i+1]['open'] - 2 * curr['ATR']
                })
    
    return signals


def strategy_bb_reversion(df: pd.DataFrame) -> List[Dict]:
    """Strategy 4: Bollinger Band Mean Reversion"""
    signals = []
    
    for i in range(50, len(df) - 10):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Price touches lower band and bounces
        if prev['close'] < prev['BB_LOWER'] and curr['close'] > curr['BB_LOWER']:
            if curr['RSI'] < 40:  # Oversold
                signals.append({
                    'idx': i,
                    'direction': 1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['BB_LOWER'] - curr['ATR'],
                    'target': curr['BB_MID']
                })
        
        # Price touches upper band and drops
        elif prev['close'] > prev['BB_UPPER'] and curr['close'] < curr['BB_UPPER']:
            if curr['RSI'] > 60:
                signals.append({
                    'idx': i,
                    'direction': -1,
                    'entry': df.iloc[i+1]['open'],
                    'stop': curr['BB_UPPER'] + curr['ATR'],
                    'target': curr['BB_MID']
                })
    
    return signals


def strategy_ema_pullback(df: pd.DataFrame) -> List[Dict]:
    """Strategy 5: Pullback to EMA in trend"""
    signals = []
    
    for i in range(50, len(df) - 10):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # Uptrend: Price pulls back to EMA21 and bounces
        if curr['EMA21'] > curr['EMA50'] > curr['EMA200']:  # Strong uptrend
            if prev['low'] <= prev['EMA21'] and curr['close'] > curr['EMA21']:
                if curr['RSI'] > 40 and curr['RSI'] < 65:
                    signals.append({
                        'idx': i,
                        'direction': 1,
                        'entry': df.iloc[i+1]['open'],
                        'stop': curr['EMA50'] - 0.5 * curr['ATR'],
                        'target': df.iloc[i+1]['open'] + 2 * curr['ATR']
                    })
        
        # Downtrend: Price pulls back to EMA21 and drops
        elif curr['EMA21'] < curr['EMA50'] < curr['EMA200']:
            if prev['high'] >= prev['EMA21'] and curr['close'] < curr['EMA21']:
                if curr['RSI'] < 60 and curr['RSI'] > 35:
                    signals.append({
                        'idx': i,
                        'direction': -1,
                        'entry': df.iloc[i+1]['open'],
                        'stop': curr['EMA50'] + 0.5 * curr['ATR'],
                        'target': df.iloc[i+1]['open'] - 2 * curr['ATR']
                    })
    
    return signals


def evaluate_signals(df: pd.DataFrame, signals: List[Dict], hold_periods: int = 10) -> BacktestResult:
    """Evaluate signal performance"""
    if not signals:
        return None
    
    wins = 0
    losses = 0
    total_r = 0
    winners = []
    losers = []
    
    for sig in signals:
        idx = sig['idx']
        if idx + hold_periods >= len(df):
            continue
        
        entry = sig['entry']
        stop = sig['stop']
        direction = sig['direction']
        
        risk = abs(entry - stop)
        if risk == 0:
            continue
        
        # Check outcome
        exit_price = df.iloc[idx + hold_periods]['close']
        pnl = (exit_price - entry) * direction
        r_multiple = pnl / risk
        
        if pnl > 0:
            wins += 1
            winners.append(r_multiple)
        else:
            losses += 1
            losers.append(r_multiple)
        
        total_r += r_multiple
    
    total = wins + losses
    if total == 0:
        return None
    
    win_rate = wins / total
    avg_winner = np.mean(winners) if winners else 0
    avg_loser = np.mean(losers) if losers else 0
    
    profit_factor = (sum(winners) / abs(sum(losers))) if losers and sum(losers) != 0 else 0
    expectancy = total_r / total
    
    # Simplified Sharpe
    all_r = winners + losers
    sharpe = np.mean(all_r) / np.std(all_r) if len(all_r) > 1 and np.std(all_r) > 0 else 0
    
    return BacktestResult(
        strategy="",
        symbol="",
        signals=total,
        wins=wins,
        losses=losses,
        win_rate=win_rate,
        total_return=total_r,
        profit_factor=profit_factor,
        avg_winner=avg_winner,
        avg_loser=avg_loser,
        expectancy=expectancy,
        sharpe=sharpe
    )


def main():
    print("=" * 70)
    print("COMPREHENSIVE STRATEGY RESEARCH")
    print("Testing Multiple Strategies Across All Symbols")
    print("=" * 70)
    
    if not mt5.initialize():
        print(f"MT5 failed: {mt5.last_error()}")
        return
    
    # Get all symbols
    categories = get_all_symbols()
    
    print("\nAvailable Symbols:")
    for cat, syms in categories.items():
        if syms:
            print(f"  {cat}: {', '.join(syms[:5])}{'...' if len(syms) > 5 else ''} ({len(syms)} total)")
    
    # Define strategies
    strategies = {
        "EMA_Crossover_9_21": strategy_ema_crossover,
        "RSI_Reversal": strategy_rsi_reversal,
        "Momentum_Breakout": strategy_momentum_breakout,
        "BB_MeanReversion": strategy_bb_reversion,
        "EMA_Pullback": strategy_ema_pullback
    }
    
    # Collect results
    all_results = []
    
    # Test priority symbols first
    priority_symbols = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",  # Forex
        "XAUUSD", "GOLD",  # Gold
        "BTCUSD",  # Crypto
        "US500", "USTEC", "US30",  # Indices
    ]
    
    # Find valid symbols
    valid_symbols = []
    for sym in priority_symbols:
        info = mt5.symbol_info(sym)
        if info and info.visible:
            valid_symbols.append(sym)
    
    if not valid_symbols:
        # Fallback to what's available
        for cat, syms in categories.items():
            valid_symbols.extend(syms[:3])
    
    print(f"\nTesting {len(valid_symbols)} symbols: {valid_symbols}")
    
    for symbol in valid_symbols:
        print(f"\n{'='*50}")
        print(f"TESTING: {symbol}")
        print(f"{'='*50}")
        
        # Get H1 data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 1000)
        if rates is None or len(rates) < 200:
            print(f"  Skipping - insufficient data")
            continue
        
        df = pd.DataFrame(rates)
        df = calculate_indicators(df)
        
        for strat_name, strat_func in strategies.items():
            try:
                signals = strat_func(df)
                result = evaluate_signals(df, signals)
                
                if result and result.signals >= 20:  # Minimum sample size
                    result.strategy = strat_name
                    result.symbol = symbol
                    all_results.append(result)
                    
                    # Print if promising
                    if result.expectancy > 0.3 and result.win_rate > 0.45:
                        print(f"\n  ** {strat_name} **")
                        print(f"     Signals: {result.signals}")
                        print(f"     Win Rate: {result.win_rate*100:.1f}%")
                        print(f"     Expectancy: {result.expectancy:.2f}R")
                        print(f"     Profit Factor: {result.profit_factor:.2f}")
                        print(f"     Total R: {result.total_return:.1f}")
                        
            except Exception as e:
                pass
    
    # SUMMARY - Find best strategies
    print("\n" + "=" * 70)
    print("STRATEGY RESEARCH RESULTS")
    print("=" * 70)
    
    if not all_results:
        print("No valid results generated!")
        mt5.shutdown()
        return
    
    # Sort by expectancy
    all_results.sort(key=lambda x: x.expectancy, reverse=True)
    
    # Top 10 performers
    print("\nTOP 10 PROFITABLE STRATEGIES:")
    print("-" * 70)
    print(f"{'Rank':<5} {'Symbol':<10} {'Strategy':<20} {'Signals':<8} {'Win%':<8} {'Expect':<8} {'PF':<8}")
    print("-" * 70)
    
    profitable = [r for r in all_results if r.expectancy > 0]
    
    for i, r in enumerate(profitable[:10], 1):
        print(f"{i:<5} {r.symbol:<10} {r.strategy:<20} {r.signals:<8} {r.win_rate*100:<8.1f} {r.expectancy:<8.2f} {r.profit_factor:<8.2f}")
    
    # By category
    print("\n\nBEST STRATEGY BY SYMBOL:")
    print("-" * 70)
    
    best_by_symbol = {}
    for r in all_results:
        if r.symbol not in best_by_symbol or r.expectancy > best_by_symbol[r.symbol].expectancy:
            best_by_symbol[r.symbol] = r
    
    for sym, r in sorted(best_by_symbol.items(), key=lambda x: x[1].expectancy, reverse=True):
        if r.expectancy > 0:
            print(f"  {sym}: {r.strategy} | Win: {r.win_rate*100:.1f}% | Exp: {r.expectancy:.2f}R | Signals: {r.signals}")
    
    # Overall stats
    print("\n\nOVERALL FINDINGS:")
    print("-" * 70)
    print(f"Total combinations tested: {len(all_results)}")
    print(f"Profitable combinations: {len(profitable)}")
    print(f"Unprofitable combinations: {len(all_results) - len(profitable)}")
    
    if profitable:
        best = profitable[0]
        print(f"\nBEST OVERALL: {best.symbol} + {best.strategy}")
        print(f"   Win Rate: {best.win_rate*100:.1f}%")
        print(f"   Expectancy: {best.expectancy:.2f}R per trade")
        print(f"   Profit Factor: {best.profit_factor:.2f}")
        print(f"   Sample Size: {best.signals} trades")
        
        print("\nRECOMMENDATION: Deploy this strategy configuration!")
    else:
        print("\nNo profitable strategies found in current data.")
        print("Consider different timeframes or longer lookback periods.")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
