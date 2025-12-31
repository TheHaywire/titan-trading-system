"""
Multi-Strategy Institutional Research
======================================
Deep research on multiple strategies across volatile instruments.

Strategies Tested:
1. Liquidity Sweep (SMC) - Price sweeps high/low then reverses
2. VWAP Deviation Mean Reversion - Buy/sell when price deviates from VWAP
3. Momentum Breakout - Break from consolidation with ATR expansion
4. Asian Range Breakout - Trade London break of Asian session range
5. First Hour Range - Breakout of first 1-hour range

Instruments: Gold, Silver, BTC, ETH, XRP, US100, US30, GER40, + Forex majors

All with institutional metrics: p-value, Sharpe, Sortino, Monte Carlo
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("MultiStrategy")


# ============================================================================
# CONFIGURATION
# ============================================================================

# All the exciting + reliable symbols
SYMBOLS = {
    # Commodities (exciting)
    'XAUUSD': 'commodity',
    'XAGUSD': 'commodity', 
    'OILCash': 'commodity',
    'BRENTCash': 'commodity',
    
    # Crypto (exciting)
    'BTCUSD': 'crypto',
    'ETHUSD': 'crypto',
    'XRPUSD': 'crypto',
    'LTCUSD': 'crypto',
    'ADAUSD': 'crypto',
    'SOLUSD': 'crypto',
    
    # Indices (exciting)
    'US100Cash': 'index',
    'US30Cash': 'index',
    'US500Cash': 'index',
    'DE40Cash': 'index',
    'UK100Cash': 'index',
    
    # Forex majors (for comparison)
    'EURUSD': 'forex',
    'GBPUSD': 'forex',
    'USDJPY': 'forex',
    'GBPJPY': 'forex',
    'AUDUSD': 'forex',
}

SESSIONS = {
    'asian': (0, 8),
    'london': (8, 13),
    'newyork': (13, 21),
}


@dataclass
class Trade:
    symbol: str
    strategy: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl_r: float
    is_win: bool
    exit_reason: str
    session: str = ""


@dataclass 
class StrategyResult:
    strategy: str
    symbol: str
    session: str
    trades: List[Trade]
    
    @property
    def total_trades(self): return len(self.trades)
    @property
    def wins(self): return sum(1 for t in self.trades if t.is_win)
    @property
    def win_rate(self): return (self.wins / self.total_trades * 100) if self.trades else 0
    @property
    def expectancy_r(self): return np.mean([t.pnl_r for t in self.trades]) if self.trades else 0
    @property
    def sharpe(self):
        if len(self.trades) < 2: return 0
        r_vals = [t.pnl_r for t in self.trades]
        return np.mean(r_vals) / np.std(r_vals) if np.std(r_vals) > 0 else 0
    @property
    def profit_factor(self):
        wins = sum(t.pnl_r for t in self.trades if t.pnl_r > 0)
        losses = abs(sum(t.pnl_r for t in self.trades if t.pnl_r < 0))
        return wins / losses if losses > 0 else float('inf') if wins > 0 else 0


# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def get_data(symbol: str, timeframe: int, days: int = 60) -> Optional[pd.DataFrame]:
    """Fetch historical data with indicators."""
    bars = days * 24 * 4 if timeframe == mt5.TIMEFRAME_M15 else days * 24
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    
    if rates is None or len(rates) < 50:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    # Add indicators
    # VWAP
    tp = (df['high'] + df['low'] + df['close']) / 3
    df['vwap'] = (tp * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
    
    # ATR
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    df['atr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1).rolling(14).mean()
    
    # Bollinger Bands
    df['sma20'] = df['close'].rolling(20).mean()
    df['bb_upper'] = df['sma20'] + 2 * df['close'].rolling(20).std()
    df['bb_lower'] = df['sma20'] - 2 * df['close'].rolling(20).std()
    
    # RSI
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['rsi'] = 100 - (100 / (1 + gain / loss))
    
    # Previous highs/lows for liquidity sweep
    df['prev_high'] = df['high'].rolling(20).max().shift(1)
    df['prev_low'] = df['low'].rolling(20).min().shift(1)
    
    return df.dropna()


# ============================================================================
# STRATEGY 1: LIQUIDITY SWEEP (SMC Style)
# ============================================================================

def backtest_liquidity_sweep(symbol: str, df: pd.DataFrame, session: str = 'all') -> List[Trade]:
    """
    Liquidity Sweep Strategy:
    - Price breaks above recent high (sweep)
    - Then closes back below it (rejection)
    - Enter short with stop above the sweep high
    
    Vice versa for longs.
    
    This is core Smart Money Concepts (SMC).
    """
    trades = []
    lookback = 20
    
    session_hours = SESSIONS.get(session, (0, 24))
    
    for i in range(lookback + 5, len(df) - 10):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Session filter
        if session != 'all':
            hour = row.name.hour
            if not (session_hours[0] <= hour < session_hours[1]):
                continue
        
        atr = row['atr']
        if atr == 0 or np.isnan(atr):
            continue
        
        # Recent high/low (liquidity levels)
        recent_high = df.iloc[i-lookback:i]['high'].max()
        recent_low = df.iloc[i-lookback:i]['low'].min()
        
        trade = None
        
        # BEARISH LIQUIDITY SWEEP
        # Price wicks above recent high but closes below it
        if prev_row['high'] > recent_high and prev_row['close'] < recent_high:
            # Current bar confirms by closing lower
            if row['close'] < prev_row['close']:
                entry = row['close']
                sl = prev_row['high'] + (atr * 0.3)  # Stop above sweep
                risk = sl - entry
                tp = entry - (risk * 2)  # 2:1 RR
                
                # Simulate
                for j in range(i + 1, min(i + 30, len(df))):
                    check = df.iloc[j]
                    if check['low'] <= tp:
                        trade = Trade(symbol, 'LiquiditySweep', 'SELL', row.name,
                                     entry, tp, sl, tp, 2.0, True, 'TP', session)
                        break
                    if check['high'] >= sl:
                        trade = Trade(symbol, 'LiquiditySweep', 'SELL', row.name,
                                     entry, sl, sl, tp, -1.0, False, 'SL', session)
                        break
        
        # BULLISH LIQUIDITY SWEEP
        # Price wicks below recent low but closes above it
        elif prev_row['low'] < recent_low and prev_row['close'] > recent_low:
            if row['close'] > prev_row['close']:
                entry = row['close']
                sl = prev_row['low'] - (atr * 0.3)
                risk = entry - sl
                tp = entry + (risk * 2)
                
                for j in range(i + 1, min(i + 30, len(df))):
                    check = df.iloc[j]
                    if check['high'] >= tp:
                        trade = Trade(symbol, 'LiquiditySweep', 'BUY', row.name,
                                     entry, tp, sl, tp, 2.0, True, 'TP', session)
                        break
                    if check['low'] <= sl:
                        trade = Trade(symbol, 'LiquiditySweep', 'BUY', row.name,
                                     entry, sl, sl, tp, -1.0, False, 'SL', session)
                        break
        
        if trade:
            trades.append(trade)
    
    return trades


# ============================================================================
# STRATEGY 2: VWAP Mean Reversion
# ============================================================================

def backtest_vwap_reversion(symbol: str, df: pd.DataFrame, session: str = 'all') -> List[Trade]:
    """
    VWAP Mean Reversion:
    - Price moves 2+ ATR away from VWAP
    - Enter towards VWAP
    - Exit at VWAP or 1:1 RR
    """
    trades = []
    session_hours = SESSIONS.get(session, (0, 24))
    
    for i in range(30, len(df) - 10):
        row = df.iloc[i]
        
        if session != 'all':
            hour = row.name.hour
            if not (session_hours[0] <= hour < session_hours[1]):
                continue
        
        atr = row['atr']
        vwap = row['vwap']
        price = row['close']
        
        if atr == 0 or np.isnan(atr) or np.isnan(vwap):
            continue
        
        distance_from_vwap = abs(price - vwap)
        atr_distance = distance_from_vwap / atr
        
        trade = None
        
        # LONG: Price is 2+ ATR BELOW VWAP (oversold deviation)
        if price < vwap and atr_distance >= 2.0:
            entry = price
            sl = price - atr
            tp = vwap  # Target VWAP
            risk = entry - sl
            reward = tp - entry
            rr = reward / risk if risk > 0 else 0
            
            for j in range(i + 1, min(i + 30, len(df))):
                check = df.iloc[j]
                if check['high'] >= tp:
                    trade = Trade(symbol, 'VWAPReversion', 'BUY', row.name,
                                 entry, tp, sl, tp, rr, True, 'TP', session)
                    break
                if check['low'] <= sl:
                    trade = Trade(symbol, 'VWAPReversion', 'BUY', row.name,
                                 entry, sl, sl, tp, -1.0, False, 'SL', session)
                    break
        
        # SHORT: Price is 2+ ATR ABOVE VWAP
        elif price > vwap and atr_distance >= 2.0:
            entry = price
            sl = price + atr
            tp = vwap
            risk = sl - entry
            reward = entry - tp
            rr = reward / risk if risk > 0 else 0
            
            for j in range(i + 1, min(i + 30, len(df))):
                check = df.iloc[j]
                if check['low'] <= tp:
                    trade = Trade(symbol, 'VWAPReversion', 'SELL', row.name,
                                 entry, tp, sl, tp, rr, True, 'TP', session)
                    break
                if check['high'] >= sl:
                    trade = Trade(symbol, 'VWAPReversion', 'SELL', row.name,
                                 entry, sl, sl, tp, -1.0, False, 'SL', session)
                    break
        
        if trade:
            trades.append(trade)
    
    return trades


# ============================================================================
# STRATEGY 3: Momentum Breakout (ATR Expansion)
# ============================================================================

def backtest_momentum_breakout(symbol: str, df: pd.DataFrame, session: str = 'all') -> List[Trade]:
    """
    Momentum Breakout:
    - Consolidation (low ATR period)
    - Breakout candle with ATR > 1.5x average
    - Enter in direction of breakout
    """
    trades = []
    session_hours = SESSIONS.get(session, (0, 24))
    
    for i in range(30, len(df) - 10):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        if session != 'all':
            hour = row.name.hour
            if not (session_hours[0] <= hour < session_hours[1]):
                continue
        
        atr = row['atr']
        current_range = row['high'] - row['low']
        
        if atr == 0 or np.isnan(atr):
            continue
        
        # Check for consolidation before (low range)
        lookback_ranges = [df.iloc[i-k]['high'] - df.iloc[i-k]['low'] for k in range(1, 6)]
        avg_range = np.mean(lookback_ranges)
        
        # Breakout: current range > 1.5x recent average
        if current_range > avg_range * 1.5:
            trade = None
            
            # Bullish breakout
            if row['close'] > row['open'] and row['close'] > prev_row['high']:
                entry = row['close']
                sl = row['low'] - (atr * 0.3)
                risk = entry - sl
                tp = entry + (risk * 2)
                
                for j in range(i + 1, min(i + 30, len(df))):
                    check = df.iloc[j]
                    if check['high'] >= tp:
                        trade = Trade(symbol, 'MomentumBreakout', 'BUY', row.name,
                                     entry, tp, sl, tp, 2.0, True, 'TP', session)
                        break
                    if check['low'] <= sl:
                        trade = Trade(symbol, 'MomentumBreakout', 'BUY', row.name,
                                     entry, sl, sl, tp, -1.0, False, 'SL', session)
                        break
            
            # Bearish breakout
            elif row['close'] < row['open'] and row['close'] < prev_row['low']:
                entry = row['close']
                sl = row['high'] + (atr * 0.3)
                risk = sl - entry
                tp = entry - (risk * 2)
                
                for j in range(i + 1, min(i + 30, len(df))):
                    check = df.iloc[j]
                    if check['low'] <= tp:
                        trade = Trade(symbol, 'MomentumBreakout', 'SELL', row.name,
                                     entry, tp, sl, tp, 2.0, True, 'TP', session)
                        break
                    if check['high'] >= sl:
                        trade = Trade(symbol, 'MomentumBreakout', 'SELL', row.name,
                                     entry, sl, sl, tp, -1.0, False, 'SL', session)
                        break
            
            if trade:
                trades.append(trade)
    
    return trades


# ============================================================================
# STRATEGY 4: Asian Range Breakout (for Gold)
# ============================================================================

def backtest_asian_range_breakout(symbol: str, df: pd.DataFrame) -> List[Trade]:
    """
    Asian Range Breakout:
    - Define Asian session (00:00-08:00 UTC) high/low
    - Trade breakout during London session
    """
    trades = []
    
    dates = df.index.normalize().unique()
    
    for date in dates[1:-1]:
        try:
            # Asian session range
            asian_start = date.replace(hour=0)
            asian_end = date.replace(hour=8)
            london_end = date.replace(hour=16)
            
            asian_data = df[(df.index >= asian_start) & (df.index < asian_end)]
            if asian_data.empty or len(asian_data) < 4:
                continue
            
            asian_high = asian_data['high'].max()
            asian_low = asian_data['low'].min()
            asian_atr = asian_data['atr'].iloc[-1]
            
            if asian_atr == 0 or np.isnan(asian_atr):
                continue
            
            # London session
            london_data = df[(df.index >= asian_end) & (df.index < london_end)]
            if london_data.empty:
                continue
            
            for i in range(len(london_data)):
                row = london_data.iloc[i]
                
                trade = None
                
                # Bullish breakout
                if row['close'] > asian_high:
                    entry = row['close']
                    sl = asian_low - (asian_atr * 0.3)
                    risk = entry - sl
                    tp = entry + (risk * 2)
                    
                    # Simulate
                    remaining = london_data.iloc[i+1:]
                    for _, check in remaining.iterrows():
                        if check['high'] >= tp:
                            trade = Trade(symbol, 'AsianBreakout', 'BUY', row.name,
                                         entry, tp, sl, tp, 2.0, True, 'TP', 'london')
                            break
                        if check['low'] <= sl:
                            trade = Trade(symbol, 'AsianBreakout', 'BUY', row.name,
                                         entry, sl, sl, tp, -1.0, False, 'SL', 'london')
                            break
                    break
                
                # Bearish breakout
                elif row['close'] < asian_low:
                    entry = row['close']
                    sl = asian_high + (asian_atr * 0.3)
                    risk = sl - entry
                    tp = entry - (risk * 2)
                    
                    remaining = london_data.iloc[i+1:]
                    for _, check in remaining.iterrows():
                        if check['low'] <= tp:
                            trade = Trade(symbol, 'AsianBreakout', 'SELL', row.name,
                                         entry, tp, sl, tp, 2.0, True, 'TP', 'london')
                            break
                        if check['high'] >= sl:
                            trade = Trade(symbol, 'AsianBreakout', 'SELL', row.name,
                                         entry, sl, sl, tp, -1.0, False, 'SL', 'london')
                            break
                    break
                
                if trade:
                    trades.append(trade)
                    break
                    
        except:
            continue
    
    return trades


# ============================================================================
# STATISTICAL ANALYSIS
# ============================================================================

def calculate_significance(trades: List[Trade]) -> Tuple[float, float, bool]:
    """Calculate t-test for statistical significance."""
    if len(trades) < 5:
        return 0, 1.0, False
    
    from scipy import stats
    r_values = [t.pnl_r for t in trades]
    t_stat, p_value = stats.ttest_1samp(r_values, 0)
    is_sig = p_value < 0.05 and np.mean(r_values) > 0
    
    return float(t_stat), float(p_value), is_sig


def monte_carlo(trades: List[Trade], sims: int = 500) -> Dict:
    """Quick Monte Carlo simulation."""
    if len(trades) < 5:
        return {}
    
    r_values = [t.pnl_r for t in trades]
    n = len(r_values)
    
    finals = []
    for _ in range(sims):
        sample = np.random.choice(r_values, n, replace=True)
        finals.append(np.sum(sample))
    
    return {
        'median': np.median(finals),
        'p5': np.percentile(finals, 5),
        'p95': np.percentile(finals, 95),
        'prob_profit': np.mean([f > 0 for f in finals]) * 100
    }


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "=" * 80)
    print("  MULTI-STRATEGY INSTITUTIONAL RESEARCH")
    print("  Finding Edges on Exciting Instruments")
    print("=" * 80 + "\n")
    
    if not mt5.initialize():
        print("MT5 not connected")
        return
    
    # Install scipy if needed
    try:
        from scipy import stats
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "scipy", "-q"])
        from scipy import stats
    
    strategies = {
        'LiquiditySweep': backtest_liquidity_sweep,
        'VWAPReversion': backtest_vwap_reversion,
        'MomentumBreakout': backtest_momentum_breakout,
    }
    
    all_results = []
    
    # Validate symbols
    valid_symbols = {}
    for sym, cat in SYMBOLS.items():
        info = mt5.symbol_info(sym)
        # Try alternative names
        if not info and sym == 'DE40Cash':
            info = mt5.symbol_info('GER40Cash')
            if info:
                sym = 'GER40Cash'
        if info:
            valid_symbols[sym] = cat
    
    logger.info(f"Testing {len(valid_symbols)} symbols across {len(strategies)} strategies")
    
    for symbol, category in valid_symbols.items():
        logger.info(f"\n{'='*40}")
        logger.info(f"Analyzing {symbol} ({category})")
        logger.info(f"{'='*40}")
        
        df = get_data(symbol, mt5.TIMEFRAME_M15, days=60)
        if df is None:
            logger.warning(f"  No data for {symbol}")
            continue
        
        for strategy_name, strategy_func in strategies.items():
            for session in ['all', 'london', 'newyork']:
                try:
                    if strategy_name == 'AsianBreakout' and session != 'all':
                        continue
                    
                    trades = strategy_func(symbol, df, session)
                    
                    if len(trades) >= 5:
                        result = StrategyResult(strategy_name, symbol, session, trades)
                        t_stat, p_val, is_sig = calculate_significance(trades)
                        
                        all_results.append({
                            'category': category,
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'session': session,
                            'trades': result.total_trades,
                            'win_rate': result.win_rate,
                            'expectancy_r': result.expectancy_r,
                            'sharpe': result.sharpe,
                            'profit_factor': result.profit_factor,
                            'p_value': p_val,
                            'is_significant': is_sig,
                            'trade_objects': trades
                        })
                        
                        sig = "✅ SIG" if is_sig else "❌"
                        logger.info(f"  {strategy_name:18} | {session:8} | N={result.total_trades:3} | "
                                   f"WR={result.win_rate:5.1f}% | Exp={result.expectancy_r:+.2f}R | {sig}")
                except Exception as e:
                    continue
        
        # Also test Asian Breakout for Gold/commodities
        if category in ['commodity', 'crypto']:
            try:
                trades = backtest_asian_range_breakout(symbol, df)
                if len(trades) >= 5:
                    result = StrategyResult('AsianBreakout', symbol, 'london', trades)
                    t_stat, p_val, is_sig = calculate_significance(trades)
                    
                    all_results.append({
                        'category': category,
                        'symbol': symbol,
                        'strategy': 'AsianBreakout',
                        'session': 'london',
                        'trades': result.total_trades,
                        'win_rate': result.win_rate,
                        'expectancy_r': result.expectancy_r,
                        'sharpe': result.sharpe,
                        'profit_factor': result.profit_factor,
                        'p_value': p_val,
                        'is_significant': is_sig,
                        'trade_objects': trades
                    })
                    
                    sig = "✅ SIG" if is_sig else "❌"
                    logger.info(f"  {'AsianBreakout':18} | {'london':8} | N={result.total_trades:3} | "
                               f"WR={result.win_rate:5.1f}% | Exp={result.expectancy_r:+.2f}R | {sig}")
            except:
                pass
    
    # Results analysis
    print("\n" + "=" * 80)
    print("  RESEARCH RESULTS")
    print("=" * 80)
    
    df_results = pd.DataFrame([{k: v for k, v in r.items() if k != 'trade_objects'} 
                               for r in all_results])
    
    if df_results.empty:
        print("No results generated")
        mt5.shutdown()
        return
    
    # Significant edges
    significant = df_results[df_results['is_significant'] == True].copy()
    
    print(f"\n📊 Total Combinations Tested: {len(df_results)}")
    print(f"✅ Statistically Significant (p<0.05): {len(significant)}")
    
    if not significant.empty:
        print("\n" + "=" * 80)
        print("  STATISTICALLY SIGNIFICANT EDGES")
        print("=" * 80)
        
        significant = significant.sort_values('expectancy_r', ascending=False)
        
        for _, row in significant.iterrows():
            print(f"\n🎯 {row['symbol']} | {row['strategy']} | {row['session'].upper()}")
            print(f"   Win Rate: {row['win_rate']:.1f}%")
            print(f"   Expectancy: {row['expectancy_r']:+.2f}R per trade")
            print(f"   Sharpe: {row['sharpe']:.2f}")
            print(f"   P-value: {row['p_value']:.4f}")
            print(f"   Trades: {row['trades']}")
            
            # Monte Carlo for significant edges
            original = next((r for r in all_results 
                           if r['symbol'] == row['symbol'] 
                           and r['strategy'] == row['strategy']
                           and r['session'] == row['session']), None)
            if original:
                mc = monte_carlo(original['trade_objects'])
                if mc:
                    print(f"   Monte Carlo: Median {mc['median']:.1f}R, "
                          f"Range [{mc['p5']:.1f}R, {mc['p95']:.1f}R], "
                          f"P(Profit)={mc['prob_profit']:.0f}%")
    
    # Best by category
    print("\n" + "=" * 80)
    print("  BEST EDGE PER CATEGORY")
    print("=" * 80)
    
    for category in ['commodity', 'crypto', 'index', 'forex']:
        cat_data = df_results[df_results['category'] == category]
        if cat_data.empty:
            continue
        
        best = cat_data.loc[cat_data['expectancy_r'].idxmax()]
        sig = "✅" if best['is_significant'] else "⚠️"
        print(f"\n{category.upper()}: {best['symbol']} | {best['strategy']} | {best['session']}")
        print(f"   Expectancy: {best['expectancy_r']:+.2f}R | WR: {best['win_rate']:.1f}% | {sig} p={best['p_value']:.3f}")
    
    # Best by strategy
    print("\n" + "=" * 80)
    print("  BEST EDGE PER STRATEGY")
    print("=" * 80)
    
    for strategy in df_results['strategy'].unique():
        strat_data = df_results[df_results['strategy'] == strategy]
        if strat_data.empty:
            continue
        
        best = strat_data.loc[strat_data['expectancy_r'].idxmax()]
        sig = "✅" if best['is_significant'] else "⚠️"
        print(f"\n{strategy}: {best['symbol']} | {best['session']}")
        print(f"   Expectancy: {best['expectancy_r']:+.2f}R | WR: {best['win_rate']:.1f}% | {sig} p={best['p_value']:.3f}")
    
    # Save report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'MULTI_STRATEGY_RESEARCH.md'
    )
    
    with open(report_path, 'w') as f:
        f.write("# Multi-Strategy Institutional Research\n\n")
        f.write(f"**Generated:** {datetime.now()}\n\n")
        f.write("## Strategies Tested\n")
        f.write("1. **Liquidity Sweep** - SMC style, trade reversals after stop hunts\n")
        f.write("2. **VWAP Reversion** - Mean reversion when price is 2+ ATR from VWAP\n")
        f.write("3. **Momentum Breakout** - Trade breakouts from consolidation\n")
        f.write("4. **Asian Range Breakout** - Trade London breakout of Asian range\n\n")
        
        f.write("## Statistically Significant Edges (p < 0.05)\n\n")
        if not significant.empty:
            f.write("| Symbol | Strategy | Session | Trades | WR% | Exp(R) | Sharpe | p-value |\n")
            f.write("|--------|----------|---------|--------|-----|--------|--------|--------|\n")
            for _, r in significant.iterrows():
                f.write(f"| {r['symbol']} | {r['strategy']} | {r['session']} | "
                       f"{r['trades']} | {r['win_rate']:.1f} | {r['expectancy_r']:.2f} | "
                       f"{r['sharpe']:.2f} | {r['p_value']:.4f} |\n")
        else:
            f.write("*No statistically significant edges found.*\n")
        
        f.write("\n## All Results\n\n")
        f.write("| Category | Symbol | Strategy | Session | Trades | WR% | Exp(R) | p-value |\n")
        f.write("|----------|--------|----------|---------|--------|-----|--------|--------|\n")
        for _, r in df_results.sort_values('expectancy_r', ascending=False).iterrows():
            f.write(f"| {r['category']} | {r['symbol']} | {r['strategy']} | {r['session']} | "
                   f"{r['trades']} | {r['win_rate']:.1f} | {r['expectancy_r']:.2f} | {r['p_value']:.3f} |\n")
    
    print(f"\n📄 Full report saved: {report_path}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
