"""
SuperTrend Strategy Backtest
============================
SuperTrend is a popular trend-following indicator that uses ATR (Average True Range)
to create dynamic support/resistance levels.

Strategy Rules:
- BUY when price closes above the SuperTrend line (trend turns bullish)
- SELL when price closes below the SuperTrend line (trend turns bearish)

Parameters:
- Period: ATR lookback period (default: 10)
- Multiplier: ATR multiplier for band width (default: 3.0)
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Tuple
from scipy import stats
import sys
import os

# Add project root to path for titan_system imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.symbol_mapper import SymbolMapper


# ============================================================================
# CONFIGURATION - Using SymbolMapper for correct resolution
# ============================================================================

# Human-readable names -> will be resolved by SymbolMapper
SYMBOLS_TO_TEST = {
    # Commodities
    'GOLD': 'commodity',
    'XAGUSD': 'commodity',
    
    # Crypto
    'BTC': 'crypto',
    'ETH': 'crypto',
    
    # Indices
    'NAS100': 'index',
    'US30': 'index',
    'DAX': 'index',
    
    # Forex
    'EURUSD': 'forex',
    'GBPUSD': 'forex',
    'GBPJPY': 'forex',
}

TIMEFRAMES = {
    'M15': mt5.TIMEFRAME_M15,
    'H1': mt5.TIMEFRAME_H1,
    'H4': mt5.TIMEFRAME_H4,
    'D1': mt5.TIMEFRAME_D1,
}


def resolve_symbols(mapper: SymbolMapper) -> Dict[str, str]:
    """Resolve all symbols using the SymbolMapper."""
    resolved = {}
    print("\n--- Symbol Resolution ---")
    for sym, asset_class in SYMBOLS_TO_TEST.items():
        resolved_name, method = mapper.resolve(sym)
        if resolved_name:
            resolved[resolved_name] = asset_class
            print(f"  ✓ {sym:12s} -> {resolved_name:15s} ({method})")
        else:
            print(f"  ✗ {sym:12s} -> NOT FOUND")
    print()
    return resolved


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class Trade:
    symbol: str
    timeframe: str
    direction: str  # 'long' or 'short'
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl_pips: float
    pnl_r: float
    is_win: bool


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    atr_period: int
    atr_multiplier: float
    trades: List[Trade]
    
    @property
    def total_trades(self) -> int:
        return len(self.trades)
    
    @property
    def wins(self) -> int:
        return len([t for t in self.trades if t.is_win])
    
    @property
    def win_rate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.wins / self.total_trades
    
    @property
    def total_pnl_r(self) -> float:
        return sum(t.pnl_r for t in self.trades)
    
    @property
    def expectancy_r(self) -> float:
        if self.total_trades == 0:
            return 0.0
        return self.total_pnl_r / self.total_trades
    
    @property
    def profit_factor(self) -> float:
        gross_wins = sum(t.pnl_r for t in self.trades if t.pnl_r > 0)
        gross_losses = abs(sum(t.pnl_r for t in self.trades if t.pnl_r < 0))
        if gross_losses == 0:
            return float('inf') if gross_wins > 0 else 0.0
        return gross_wins / gross_losses
    
    @property
    def sharpe(self) -> float:
        if self.total_trades < 2:
            return 0.0
        returns = [t.pnl_r for t in self.trades]
        if np.std(returns) == 0:
            return 0.0
        return np.mean(returns) / np.std(returns) * np.sqrt(252)


# ============================================================================
# SUPERTREND CALCULATION
# ============================================================================

def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    Calculate SuperTrend indicator.
    
    SuperTrend = 
    - Upper Band = (High + Low) / 2 + (Multiplier * ATR)
    - Lower Band = (High + Low) / 2 - (Multiplier * ATR)
    
    The SuperTrend line switches between upper and lower bands based on price action.
    """
    df = df.copy()
    
    # Calculate ATR
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(window=period).mean()
    
    # Calculate basic bands
    df['hl2'] = (df['high'] + df['low']) / 2
    df['upper_band'] = df['hl2'] + (multiplier * df['atr'])
    df['lower_band'] = df['hl2'] - (multiplier * df['atr'])
    
    # Initialize SuperTrend
    df['supertrend'] = np.nan
    df['st_direction'] = 1  # 1 = bullish, -1 = bearish
    
    for i in range(period, len(df)):
        # Previous values
        prev_st = df['supertrend'].iloc[i-1]
        prev_dir = df['st_direction'].iloc[i-1]
        
        curr_upper = df['upper_band'].iloc[i]
        curr_lower = df['lower_band'].iloc[i]
        curr_close = df['close'].iloc[i]
        prev_close = df['close'].iloc[i-1]
        
        # Adjust bands based on previous bands (prevents whipsaws)
        if i > period:
            prev_upper = df['upper_band'].iloc[i-1]
            prev_lower = df['lower_band'].iloc[i-1]
            
            if curr_upper < prev_upper or prev_close > prev_upper:
                df.loc[df.index[i], 'upper_band'] = curr_upper
            else:
                df.loc[df.index[i], 'upper_band'] = prev_upper
                curr_upper = prev_upper
            
            if curr_lower > prev_lower or prev_close < prev_lower:
                df.loc[df.index[i], 'lower_band'] = curr_lower
            else:
                df.loc[df.index[i], 'lower_band'] = prev_lower
                curr_lower = prev_lower
        
        # Determine current SuperTrend
        if np.isnan(prev_st):
            # First value
            df.loc[df.index[i], 'supertrend'] = curr_lower if curr_close > df['hl2'].iloc[i] else curr_upper
            df.loc[df.index[i], 'st_direction'] = 1 if curr_close > df['hl2'].iloc[i] else -1
        else:
            if prev_dir == 1:  # Was bullish
                if curr_close < curr_lower:  # Price broke below - turn bearish
                    df.loc[df.index[i], 'supertrend'] = curr_upper
                    df.loc[df.index[i], 'st_direction'] = -1
                else:  # Stay bullish
                    df.loc[df.index[i], 'supertrend'] = curr_lower
                    df.loc[df.index[i], 'st_direction'] = 1
            else:  # Was bearish
                if curr_close > curr_upper:  # Price broke above - turn bullish
                    df.loc[df.index[i], 'supertrend'] = curr_lower
                    df.loc[df.index[i], 'st_direction'] = 1
                else:  # Stay bearish
                    df.loc[df.index[i], 'supertrend'] = curr_upper
                    df.loc[df.index[i], 'st_direction'] = -1
    
    return df


# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def get_data(symbol: str, timeframe: int, days: int = 365) -> pd.DataFrame:
    """Fetch historical data from MT5."""
    if not mt5.initialize():
        print("MT5 initialization failed!")
        return pd.DataFrame()
    
    utc_to = datetime.now()
    utc_from = utc_to - timedelta(days=days)
    
    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    
    if rates is None or len(rates) == 0:
        print(f"No data for {symbol}")
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    return df


# ============================================================================
# BACKTEST ENGINE
# ============================================================================

def backtest_supertrend(
    symbol: str, 
    timeframe_name: str,
    df: pd.DataFrame, 
    atr_period: int = 10, 
    atr_multiplier: float = 3.0,
    risk_reward: float = 2.0
) -> BacktestResult:
    """
    Backtest SuperTrend strategy.
    
    Entry: When SuperTrend direction changes
    Stop Loss: SuperTrend line at entry
    Take Profit: Risk * RR ratio
    """
    trades: List[Trade] = []
    
    # Calculate SuperTrend
    df = calculate_supertrend(df, atr_period, atr_multiplier)
    df = df.dropna(subset=['supertrend'])
    
    if len(df) < 50:
        return BacktestResult(symbol, timeframe_name, atr_period, atr_multiplier, trades)
    
    # Detect direction changes
    df['prev_direction'] = df['st_direction'].shift(1)
    df['signal'] = 0
    df.loc[df['st_direction'] > df['prev_direction'], 'signal'] = 1   # Bullish crossover
    df.loc[df['st_direction'] < df['prev_direction'], 'signal'] = -1  # Bearish crossover
    
    signals = df[df['signal'] != 0].copy()
    
    for i, (idx, row) in enumerate(signals.iterrows()):
        direction = 'long' if row['signal'] == 1 else 'short'
        entry_price = row['close']
        entry_time = idx
        stop_loss = row['supertrend']
        
        # Calculate risk and TP
        risk = abs(entry_price - stop_loss)
        if direction == 'long':
            take_profit = entry_price + (risk * risk_reward)
        else:
            take_profit = entry_price - (risk * risk_reward)
        
        # Simulate trade forward
        future_data = df.loc[idx:].iloc[1:100]  # Next 100 candles max
        
        exit_price = None
        exit_time = None
        pnl_pips = 0
        pnl_r = 0
        is_win = False
        
        for future_idx, future_row in future_data.iterrows():
            if direction == 'long':
                # Check stop loss
                if future_row['low'] <= stop_loss:
                    exit_price = stop_loss
                    exit_time = future_idx
                    pnl_r = -1.0
                    is_win = False
                    break
                # Check take profit
                if future_row['high'] >= take_profit:
                    exit_price = take_profit
                    exit_time = future_idx
                    pnl_r = risk_reward
                    is_win = True
                    break
            else:  # short
                # Check stop loss
                if future_row['high'] >= stop_loss:
                    exit_price = stop_loss
                    exit_time = future_idx
                    pnl_r = -1.0
                    is_win = False
                    break
                # Check take profit
                if future_row['low'] <= take_profit:
                    exit_price = take_profit
                    exit_time = future_idx
                    pnl_r = risk_reward
                    is_win = True
                    break
        
        # If trade didn't hit SL/TP, close at last price
        if exit_price is None and len(future_data) > 0:
            exit_price = future_data.iloc[-1]['close']
            exit_time = future_data.index[-1]
            if direction == 'long':
                pnl_r = (exit_price - entry_price) / risk if risk > 0 else 0
            else:
                pnl_r = (entry_price - exit_price) / risk if risk > 0 else 0
            is_win = pnl_r > 0
        
        if exit_price is not None:
            # Calculate pips (simplified - adjust per instrument)
            if 'JPY' in symbol:
                pnl_pips = (exit_price - entry_price) * 100 if direction == 'long' else (entry_price - exit_price) * 100
            elif 'XAU' in symbol:
                pnl_pips = (exit_price - entry_price) * 10 if direction == 'long' else (entry_price - exit_price) * 10
            else:
                pnl_pips = (exit_price - entry_price) * 10000 if direction == 'long' else (entry_price - exit_price) * 10000
            
            trades.append(Trade(
                symbol=symbol,
                timeframe=timeframe_name,
                direction=direction,
                entry_time=entry_time,
                entry_price=entry_price,
                exit_time=exit_time,
                exit_price=exit_price,
                pnl_pips=pnl_pips,
                pnl_r=pnl_r,
                is_win=is_win
            ))
    
    return BacktestResult(symbol, timeframe_name, atr_period, atr_multiplier, trades)


def calculate_significance(trades: List[Trade]) -> tuple:
    """Calculate t-test for statistical significance."""
    if len(trades) < 10:
        return 0.0, 1.0
    
    returns = [t.pnl_r for t in trades]
    t_stat, p_value = stats.ttest_1samp(returns, 0)
    return t_stat, p_value


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 80)
    print("SUPERTREND STRATEGY BACKTEST")
    print("=" * 80)
    print()
    
    if not mt5.initialize():
        print("Failed to initialize MT5!")
        return
    
    print(f"MT5 Connected: {mt5.terminal_info().name}")
    print(f"Account: {mt5.account_info().login}")
    
    # Use SymbolMapper for correct symbol resolution
    mapper = SymbolMapper()
    SYMBOLS = resolve_symbols(mapper)
    
    if not SYMBOLS:
        print("ERROR: No symbols could be resolved. Check data/tradeable_universe.json")
        mt5.shutdown()
        return
    
    all_results: List[BacktestResult] = []
    
    # Test parameters
    PARAMETERS = [
        (10, 3.0),  # Default
        (10, 2.0),  # Tighter
        (7, 3.0),   # Faster
        (14, 3.0),  # Slower
    ]
    
    for symbol, asset_class in SYMBOLS.items():
        print(f"\n{'='*60}")
        print(f"Testing: {symbol} ({asset_class})")
        print('='*60)
        
        for tf_name, tf_value in TIMEFRAMES.items():
            print(f"\n  Timeframe: {tf_name}")
            
            df = get_data(symbol, tf_value, days=365)
            
            if df.empty:
                print(f"    [!] No data available")
                continue
            
            print(f"    Data points: {len(df)}")
            
            for period, multiplier in PARAMETERS:
                result = backtest_supertrend(
                    symbol=symbol,
                    timeframe_name=tf_name,
                    df=df,
                    atr_period=period,
                    atr_multiplier=multiplier
                )
                
                if result.total_trades >= 10:
                    t_stat, p_value = calculate_significance(result.trades)
                    is_significant = p_value < 0.05 and result.expectancy_r > 0
                    
                    sig_marker = "✓ EDGE" if is_significant else ""
                    
                    print(f"    [{period}/{multiplier}] Trades: {result.total_trades:3d} | "
                          f"Win: {result.win_rate*100:5.1f}% | "
                          f"Exp: {result.expectancy_r:+.2f}R | "
                          f"PF: {result.profit_factor:.2f} | "
                          f"Sharpe: {result.sharpe:.2f} | "
                          f"p={p_value:.4f} {sig_marker}")
                    
                    all_results.append(result)
                else:
                    print(f"    [{period}/{multiplier}] Trades: {result.total_trades:3d} (too few)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - BEST PERFORMING CONFIGURATIONS")
    print("=" * 80)
    
    # Filter significant edges
    significant_results = [
        r for r in all_results 
        if r.total_trades >= 20 and calculate_significance(r.trades)[1] < 0.05 and r.expectancy_r > 0
    ]
    
    if significant_results:
        print(f"\nFound {len(significant_results)} statistically significant edges:\n")
        
        # Sort by expectancy
        significant_results.sort(key=lambda x: x.expectancy_r, reverse=True)
        
        for r in significant_results[:15]:  # Top 15
            t_stat, p_value = calculate_significance(r.trades)
            print(f"  {r.symbol:12s} {r.timeframe:4s} ({r.atr_period}/{r.atr_multiplier}) | "
                  f"Trades: {r.total_trades:3d} | Win: {r.win_rate*100:.1f}% | "
                  f"Exp: {r.expectancy_r:+.3f}R | PF: {r.profit_factor:.2f} | "
                  f"Sharpe: {r.sharpe:.2f} | p={p_value:.4f}")
    else:
        print("\nNo statistically significant edges found with current parameters.")
        print("Consider testing different parameter combinations or timeframes.")
    
    # Save results to CSV
    if all_results:
        data = []
        for r in all_results:
            t_stat, p_value = calculate_significance(r.trades)
            data.append({
                'symbol': r.symbol,
                'timeframe': r.timeframe,
                'atr_period': r.atr_period,
                'atr_multiplier': r.atr_multiplier,
                'total_trades': r.total_trades,
                'wins': r.wins,
                'win_rate': r.win_rate,
                'expectancy_r': r.expectancy_r,
                'profit_factor': r.profit_factor,
                'sharpe': r.sharpe,
                'p_value': p_value,
                'is_significant': p_value < 0.05 and r.expectancy_r > 0
            })
        
        results_df = pd.DataFrame(data)
        results_df.to_csv('data/supertrend_backtest_results.csv', index=False)
        print(f"\nResults saved to data/supertrend_backtest_results.csv")
    
    mt5.shutdown()
    print("\n✓ Backtest complete!")


if __name__ == "__main__":
    main()
