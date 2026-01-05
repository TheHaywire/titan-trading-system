"""
Kalman Filter & VWAP Strategy Backtest
=======================================
Two advanced strategies:

1. KALMAN FILTER TREND FOLLOWING:
   - Kalman filter provides adaptive smoothing of price
   - BUY when price crosses above Kalman estimate + velocity is positive
   - SELL when price crosses below Kalman estimate + velocity is negative
   - Much smoother than MA crossovers, adapts to volatility

2. VWAP MEAN REVERSION:
   - VWAP = Volume Weighted Average Price (intraday anchor)
   - Price tends to revert to VWAP
   - BUY when price is 2+ ATR below VWAP (oversold)
   - SELL when price is 2+ ATR above VWAP (overbought)
   - Target: Return to VWAP
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

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from titan_system.core.symbol_mapper import SymbolMapper


# ============================================================================
# CONFIGURATION
# ============================================================================

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
    strategy: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    pnl_r: float
    is_win: bool


@dataclass
class BacktestResult:
    symbol: str
    timeframe: str
    strategy: str
    params: str
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
# KALMAN FILTER
# ============================================================================

def kalman_filter(prices: pd.Series, q: float = 0.01, r: float = 0.1) -> Tuple[pd.Series, pd.Series]:
    """
    Simple 1D Kalman Filter for price estimation.
    
    State: [price, velocity]
    
    Parameters:
    - q: Process noise (how much we expect price to change unexpectedly)
    - r: Measurement noise (how noisy is the price data)
    
    Returns:
    - estimate: Filtered price estimate
    - velocity: Rate of change estimate
    """
    n = len(prices)
    
    # Initialize state
    x = np.array([prices.iloc[0], 0.0])  # [price, velocity]
    P = np.eye(2) * 1000  # Initial uncertainty
    
    # State transition matrix (constant velocity model)
    F = np.array([[1, 1],
                  [0, 1]])
    
    # Observation matrix (we only observe price, not velocity)
    H = np.array([[1, 0]])
    
    # Process noise covariance
    Q = np.array([[q, 0],
                  [0, q]])
    
    # Measurement noise covariance
    R = np.array([[r]])
    
    estimates = []
    velocities = []
    
    for i in range(n):
        # Predict
        x = F @ x
        P = F @ P @ F.T + Q
        
        # Update
        z = np.array([prices.iloc[i]])
        y = z - H @ x  # Innovation
        S = H @ P @ H.T + R  # Innovation covariance
        K = P @ H.T @ np.linalg.inv(S)  # Kalman gain
        x = x + K @ y
        P = (np.eye(2) - K @ H) @ P
        
        estimates.append(x[0])
        velocities.append(x[1])
    
    return pd.Series(estimates, index=prices.index), pd.Series(velocities, index=prices.index)


# ============================================================================
# VWAP CALCULATION
# ============================================================================

def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    """
    Calculate cumulative VWAP.
    VWAP = Cumulative(Price * Volume) / Cumulative(Volume)
    
    For intraday, this resets each day.
    """
    df = df.copy()
    
    # Typical price
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    
    # Use tick_volume as volume proxy
    volume = df['tick_volume'].astype(float)
    pv = typical_price * volume
    
    # Daily reset - create date column for grouping
    dates = df.index.date
    
    # Calculate cumulative sums per day
    vwap_values = []
    current_date = None
    cum_pv = 0.0
    cum_vol = 0.0
    
    for i, (idx, row) in enumerate(df.iterrows()):
        row_date = idx.date()
        
        # Reset on new day
        if row_date != current_date:
            cum_pv = 0.0
            cum_vol = 0.0
            current_date = row_date
        
        cum_pv += pv.iloc[i]
        cum_vol += volume.iloc[i]
        
        if cum_vol > 0:
            vwap_values.append(cum_pv / cum_vol)
        else:
            vwap_values.append(typical_price.iloc[i])
    
    return pd.Series(vwap_values, index=df.index)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    return tr.rolling(window=period).mean()


# ============================================================================
# DATA FUNCTIONS
# ============================================================================

def get_data(symbol: str, timeframe: int, days: int = 365) -> pd.DataFrame:
    """Fetch historical data from MT5."""
    utc_to = datetime.now()
    utc_from = utc_to - timedelta(days=days)
    
    rates = mt5.copy_rates_range(symbol, timeframe, utc_from, utc_to)
    
    if rates is None or len(rates) == 0:
        return pd.DataFrame()
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    
    return df


# ============================================================================
# BACKTEST: KALMAN FILTER TREND
# ============================================================================

def backtest_kalman(
    symbol: str,
    timeframe_name: str,
    df: pd.DataFrame,
    q: float = 0.01,
    r: float = 0.1,
    risk_reward: float = 2.0
) -> BacktestResult:
    """
    Kalman Filter Trend Following:
    - Long when price crosses above Kalman estimate AND velocity > 0
    - Short when price crosses below Kalman estimate AND velocity < 0
    """
    trades: List[Trade] = []
    
    if len(df) < 100:
        return BacktestResult(symbol, timeframe_name, 'Kalman', f'q={q}/r={r}', trades)
    
    # Calculate Kalman filter
    estimate, velocity = kalman_filter(df['close'], q, r)
    
    df = df.copy()
    df['kalman'] = estimate
    df['velocity'] = velocity
    df['atr'] = calculate_atr(df)
    
    df = df.dropna()
    
    # Generate signals
    df['above_kalman'] = df['close'] > df['kalman']
    df['prev_above'] = df['above_kalman'].shift(1)
    
    # Long signal: cross above + positive velocity
    df['prev_above'] = df['prev_above'].fillna(False).astype(bool)
    df['above_kalman'] = df['above_kalman'].astype(bool)
    df['long_signal'] = (df['above_kalman'] & ~df['prev_above'] & (df['velocity'] > 0))
    # Short signal: cross below + negative velocity
    df['short_signal'] = (~df['above_kalman'] & df['prev_above'] & (df['velocity'] < 0))
    
    # Process signals
    for idx in df.index:
        row = df.loc[idx]
        
        if row['long_signal'] or row['short_signal']:
            direction = 'long' if row['long_signal'] else 'short'
            entry_price = row['close']
            entry_time = idx
            atr = row['atr']
            
            if atr <= 0:
                continue
            
            # Stop loss: 1.5 ATR from entry
            if direction == 'long':
                stop_loss = entry_price - (1.5 * atr)
                take_profit = entry_price + (1.5 * atr * risk_reward)
            else:
                stop_loss = entry_price + (1.5 * atr)
                take_profit = entry_price - (1.5 * atr * risk_reward)
            
            risk = abs(entry_price - stop_loss)
            
            # Simulate forward
            future_data = df.loc[idx:].iloc[1:50]
            
            exit_price = None
            exit_time = None
            pnl_r = 0
            is_win = False
            
            for future_idx, future_row in future_data.iterrows():
                if direction == 'long':
                    if future_row['low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_time = future_idx
                        pnl_r = -1.0
                        break
                    if future_row['high'] >= take_profit:
                        exit_price = take_profit
                        exit_time = future_idx
                        pnl_r = risk_reward
                        is_win = True
                        break
                else:
                    if future_row['high'] >= stop_loss:
                        exit_price = stop_loss
                        exit_time = future_idx
                        pnl_r = -1.0
                        break
                    if future_row['low'] <= take_profit:
                        exit_price = take_profit
                        exit_time = future_idx
                        pnl_r = risk_reward
                        is_win = True
                        break
            
            if exit_price is None and len(future_data) > 0:
                exit_price = future_data.iloc[-1]['close']
                exit_time = future_data.index[-1]
                if direction == 'long':
                    pnl_r = (exit_price - entry_price) / risk if risk > 0 else 0
                else:
                    pnl_r = (entry_price - exit_price) / risk if risk > 0 else 0
                is_win = pnl_r > 0
            
            if exit_price is not None:
                trades.append(Trade(
                    symbol=symbol,
                    timeframe=timeframe_name,
                    strategy='Kalman',
                    direction=direction,
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=exit_time,
                    exit_price=exit_price,
                    pnl_r=pnl_r,
                    is_win=is_win
                ))
    
    return BacktestResult(symbol, timeframe_name, 'Kalman', f'q={q}/r={r}', trades)


# ============================================================================
# BACKTEST: VWAP MEAN REVERSION
# ============================================================================

def backtest_vwap(
    symbol: str,
    timeframe_name: str,
    df: pd.DataFrame,
    atr_threshold: float = 2.0,
    risk_reward: float = 1.5
) -> BacktestResult:
    """
    VWAP Mean Reversion:
    - Long when price is atr_threshold * ATR below VWAP
    - Short when price is atr_threshold * ATR above VWAP
    - Target: Reversion to VWAP
    """
    trades: List[Trade] = []
    
    if len(df) < 100:
        return BacktestResult(symbol, timeframe_name, 'VWAP', f'thresh={atr_threshold}', trades)
    
    df = df.copy()
    
    # Calculate indicators
    df['vwap'] = calculate_vwap(df)
    df['atr'] = calculate_atr(df)
    
    df = df.dropna()
    
    if len(df) < 50:
        return BacktestResult(symbol, timeframe_name, 'VWAP', f'thresh={atr_threshold}', trades)
    
    # Calculate distance from VWAP in ATR units
    df['vwap_distance'] = (df['close'] - df['vwap']) / df['atr']
    
    # Generate signals
    df['long_signal'] = df['vwap_distance'] < -atr_threshold
    df['short_signal'] = df['vwap_distance'] > atr_threshold
    
    # Prevent consecutive signals
    df['prev_long'] = df['long_signal'].shift(1).fillna(False)
    df['prev_short'] = df['short_signal'].shift(1).fillna(False)
    
    df['new_long'] = df['long_signal'] & ~df['prev_long']
    df['new_short'] = df['short_signal'] & ~df['prev_short']
    
    for idx in df.index:
        row = df.loc[idx]
        
        if row['new_long'] or row['new_short']:
            direction = 'long' if row['new_long'] else 'short'
            entry_price = row['close']
            entry_time = idx
            atr = row['atr']
            vwap = row['vwap']
            
            if atr <= 0:
                continue
            
            # Target: VWAP (or partial distance)
            distance_to_vwap = abs(vwap - entry_price)
            
            # Stop loss: Beyond the extreme (1 ATR beyond entry)
            if direction == 'long':
                stop_loss = entry_price - atr
                # Target: Move 75% back to VWAP
                take_profit = entry_price + (distance_to_vwap * 0.75)
            else:
                stop_loss = entry_price + atr
                take_profit = entry_price - (distance_to_vwap * 0.75)
            
            risk = abs(entry_price - stop_loss)
            
            # Simulate forward
            future_data = df.loc[idx:].iloc[1:30]  # Shorter horizon for mean reversion
            
            exit_price = None
            exit_time = None
            pnl_r = 0
            is_win = False
            
            for future_idx, future_row in future_data.iterrows():
                if direction == 'long':
                    if future_row['low'] <= stop_loss:
                        exit_price = stop_loss
                        exit_time = future_idx
                        pnl_r = -1.0
                        break
                    if future_row['high'] >= take_profit:
                        exit_price = take_profit
                        exit_time = future_idx
                        pnl_r = (take_profit - entry_price) / risk if risk > 0 else 0
                        is_win = True
                        break
                else:
                    if future_row['high'] >= stop_loss:
                        exit_price = stop_loss
                        exit_time = future_idx
                        pnl_r = -1.0
                        break
                    if future_row['low'] <= take_profit:
                        exit_price = take_profit
                        exit_time = future_idx
                        pnl_r = (entry_price - take_profit) / risk if risk > 0 else 0
                        is_win = True
                        break
            
            if exit_price is None and len(future_data) > 0:
                exit_price = future_data.iloc[-1]['close']
                exit_time = future_data.index[-1]
                if direction == 'long':
                    pnl_r = (exit_price - entry_price) / risk if risk > 0 else 0
                else:
                    pnl_r = (entry_price - exit_price) / risk if risk > 0 else 0
                is_win = pnl_r > 0
            
            if exit_price is not None:
                trades.append(Trade(
                    symbol=symbol,
                    timeframe=timeframe_name,
                    strategy='VWAP',
                    direction=direction,
                    entry_time=entry_time,
                    entry_price=entry_price,
                    exit_time=exit_time,
                    exit_price=exit_price,
                    pnl_r=pnl_r,
                    is_win=is_win
                ))
    
    return BacktestResult(symbol, timeframe_name, 'VWAP', f'thresh={atr_threshold}', trades)


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
    print("KALMAN FILTER & VWAP STRATEGY BACKTEST")
    print("=" * 80)
    print()
    
    if not mt5.initialize():
        print("Failed to initialize MT5!")
        return
    
    print(f"MT5 Connected: {mt5.terminal_info().name}")
    print(f"Account: {mt5.account_info().login}")
    
    # Resolve symbols
    mapper = SymbolMapper()
    SYMBOLS = resolve_symbols(mapper)
    
    if not SYMBOLS:
        print("ERROR: No symbols resolved!")
        mt5.shutdown()
        return
    
    all_results: List[BacktestResult] = []
    
    # Test parameters
    KALMAN_PARAMS = [
        (0.001, 0.1),  # Slow/smooth
        (0.01, 0.1),   # Default
        (0.05, 0.1),   # Faster
    ]
    
    VWAP_PARAMS = [
        1.5,  # Tighter
        2.0,  # Default  
        2.5,  # Wider
    ]
    
    for symbol, asset_class in SYMBOLS.items():
        print(f"\n{'='*70}")
        print(f"Testing: {symbol} ({asset_class})")
        print('='*70)
        
        for tf_name, tf_value in TIMEFRAMES.items():
            print(f"\n  {tf_name}:")
            
            df = get_data(symbol, tf_value, days=365)
            
            if df.empty:
                print(f"    [!] No data")
                continue
            
            print(f"    Data: {len(df)} bars")
            
            # === KALMAN FILTER ===
            print(f"    --- Kalman Filter ---")
            for q, r in KALMAN_PARAMS:
                result = backtest_kalman(symbol, tf_name, df, q=q, r=r)
                
                if result.total_trades >= 10:
                    t_stat, p_value = calculate_significance(result.trades)
                    sig = "✓ EDGE" if p_value < 0.05 and result.expectancy_r > 0 else ""
                    
                    print(f"      [q={q}/r={r}] Trades: {result.total_trades:3d} | "
                          f"Win: {result.win_rate*100:5.1f}% | Exp: {result.expectancy_r:+.2f}R | "
                          f"PF: {result.profit_factor:.2f} | p={p_value:.4f} {sig}")
                    
                    all_results.append(result)
                else:
                    print(f"      [q={q}/r={r}] Trades: {result.total_trades} (too few)")
            
            # === VWAP ===
            print(f"    --- VWAP Mean Reversion ---")
            for thresh in VWAP_PARAMS:
                result = backtest_vwap(symbol, tf_name, df, atr_threshold=thresh)
                
                if result.total_trades >= 10:
                    t_stat, p_value = calculate_significance(result.trades)
                    sig = "✓ EDGE" if p_value < 0.05 and result.expectancy_r > 0 else ""
                    
                    print(f"      [thresh={thresh}] Trades: {result.total_trades:3d} | "
                          f"Win: {result.win_rate*100:5.1f}% | Exp: {result.expectancy_r:+.2f}R | "
                          f"PF: {result.profit_factor:.2f} | p={p_value:.4f} {sig}")
                    
                    all_results.append(result)
                else:
                    print(f"      [thresh={thresh}] Trades: {result.total_trades} (too few)")
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY - STATISTICALLY SIGNIFICANT EDGES")
    print("=" * 80)
    
    significant = [
        r for r in all_results
        if r.total_trades >= 20 and calculate_significance(r.trades)[1] < 0.05 and r.expectancy_r > 0
    ]
    
    if significant:
        print(f"\nFound {len(significant)} edges:\n")
        significant.sort(key=lambda x: x.expectancy_r, reverse=True)
        
        for r in significant[:20]:
            t_stat, p_value = calculate_significance(r.trades)
            print(f"  {r.strategy:8s} {r.symbol:12s} {r.timeframe:4s} ({r.params}) | "
                  f"Trades: {r.total_trades:3d} | Win: {r.win_rate*100:.1f}% | "
                  f"Exp: {r.expectancy_r:+.3f}R | PF: {r.profit_factor:.2f} | p={p_value:.4f}")
    else:
        print("\nNo statistically significant edges found.")
    
    # Save results
    if all_results:
        data = []
        for r in all_results:
            t_stat, p_value = calculate_significance(r.trades)
            data.append({
                'strategy': r.strategy,
                'symbol': r.symbol,
                'timeframe': r.timeframe,
                'params': r.params,
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
        results_df.to_csv('data/kalman_vwap_backtest_results.csv', index=False)
        print(f"\nResults saved to data/kalman_vwap_backtest_results.csv")
    
    mt5.shutdown()
    print("\n✓ Backtest complete!")


if __name__ == "__main__":
    main()
