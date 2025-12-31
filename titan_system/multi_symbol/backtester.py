"""
Simple Backtester - Validate Strategies on Historical Data
==========================================================
Quick backtesting using MT5 historical data to validate strategies
before deploying them live.

Features:
- Uses MT5 copy_rates for historical data
- Tests ORB and Mean Reversion strategies  
- Calculates key metrics (win rate, profit factor, max DD)
- Provides confidence score for strategy viability
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

logger = logging.getLogger("Titan.Backtester")


@dataclass
class TradeResult:
    """Single trade result."""
    symbol: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_pips: float
    is_win: bool
    exit_reason: str  # 'TP', 'SL', 'SIGNAL', 'TIMEOUT'


@dataclass 
class BacktestResult:
    """Complete backtest results."""
    symbol: str
    strategy: str
    period_start: datetime
    period_end: datetime
    total_trades: int
    wins: int
    losses: int
    win_rate: float
    total_pnl: float
    profit_factor: float
    max_drawdown: float
    avg_win: float
    avg_loss: float
    expectancy: float
    trades: List[TradeResult]
    confidence_score: float  # 0-100


class SimpleBacktester:
    """
    Quick backtester for strategy validation.
    
    Usage:
        bt = SimpleBacktester()
        result = bt.run('EURUSD', 'MeanReversion', days=30)
        bt.print_result(result)
    """
    
    def __init__(self):
        if not mt5.initialize():
            raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    
    def get_historical_data(self, symbol: str, timeframe: int, 
                            days: int) -> Optional[pd.DataFrame]:
        """Fetch historical OHLCV data."""
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, days * 24 * 4)  # Approx for M15
        
        if rates is None or len(rates) == 0:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        return df
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add indicators for strategies."""
        df = df.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['sma20'] = df['close'].rolling(20).mean()
        df['std20'] = df['close'].rolling(20).std()
        df['bb_upper'] = df['sma20'] + (df['std20'] * 2.0)
        df['bb_lower'] = df['sma20'] - (df['std20'] * 2.0)
        
        # ATR
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        df['tr'] = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df['atr'] = df['tr'].rolling(14).mean()
        
        # VWAP (simplified daily reset)
        df['vwap'] = (df['close'] * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()
        
        return df.dropna()
    
    def run_mean_reversion(self, df: pd.DataFrame, symbol: str) -> List[TradeResult]:
        """Backtest Mean Reversion strategy."""
        trades = []
        in_trade = False
        entry = None
        
        for i in range(50, len(df) - 10):
            row = df.iloc[i]
            
            if not in_trade:
                # BUY signal: Price < Lower BB AND RSI < 30
                if row['close'] < row['bb_lower'] and row['rsi'] < 30:
                    sl = row['close'] - (row['atr'] * 1.5)
                    tp = row['close'] + (row['atr'] * 2.0)
                    entry = {
                        'time': df.index[i],
                        'price': row['close'],
                        'direction': 'BUY',
                        'sl': sl,
                        'tp': tp
                    }
                    in_trade = True
                    
                # SELL signal: Price > Upper BB AND RSI > 70
                elif row['close'] > row['bb_upper'] and row['rsi'] > 70:
                    sl = row['close'] + (row['atr'] * 1.5)
                    tp = row['close'] - (row['atr'] * 2.0)
                    entry = {
                        'time': df.index[i],
                        'price': row['close'],
                        'direction': 'SELL',
                        'sl': sl,
                        'tp': tp
                    }
                    in_trade = True
            
            else:
                # Check exit conditions
                exit_reason = None
                exit_price = row['close']
                
                if entry['direction'] == 'BUY':
                    if row['high'] >= entry['tp']:
                        exit_reason = 'TP'
                        exit_price = entry['tp']
                    elif row['low'] <= entry['sl']:
                        exit_reason = 'SL'
                        exit_price = entry['sl']
                    elif row['close'] > row['sma20']:  # Mean reached
                        exit_reason = 'SIGNAL'
                        exit_price = row['close']
                else:  # SELL
                    if row['low'] <= entry['tp']:
                        exit_reason = 'TP'
                        exit_price = entry['tp']
                    elif row['high'] >= entry['sl']:
                        exit_reason = 'SL'
                        exit_price = entry['sl']
                    elif row['close'] < row['sma20']:
                        exit_reason = 'SIGNAL'
                        exit_price = row['close']
                
                if exit_reason:
                    pnl = (exit_price - entry['price']) if entry['direction'] == 'BUY' else (entry['price'] - exit_price)
                    pnl_pips = pnl / 0.0001 if pnl != 0 else 0  # Approximate pips
                    
                    trades.append(TradeResult(
                        symbol=symbol,
                        direction=entry['direction'],
                        entry_time=entry['time'],
                        entry_price=entry['price'],
                        exit_time=df.index[i],
                        exit_price=exit_price,
                        stop_loss=entry['sl'],
                        take_profit=entry['tp'],
                        pnl=pnl,
                        pnl_pips=pnl_pips,
                        is_win=pnl > 0,
                        exit_reason=exit_reason
                    ))
                    in_trade = False
                    entry = None
        
        return trades
    
    def run_orb(self, df: pd.DataFrame, symbol: str) -> List[TradeResult]:
        """Backtest Opening Range Breakout strategy."""
        trades = []
        
        # Resample to identify daily opens
        daily_opens = df.between_time('08:00', '08:15')  # London open M15
        
        for date in daily_opens.index.date:
            try:
                day_data = df[df.index.date == date]
                if len(day_data) < 10:
                    continue
                
                # First bar of day = Opening Range
                first_bar = day_data.iloc[0]
                orb_high = first_bar['high']
                orb_low = first_bar['low']
                
                # Look for breakout in remaining day
                for i in range(1, min(len(day_data), 20)):
                    row = day_data.iloc[i]
                    
                    # Bullish breakout
                    if row['close'] > orb_high and row['close'] > row['vwap']:
                        sl = orb_low - (row['atr'] * 0.5)
                        risk = row['close'] - sl
                        tp = row['close'] + (risk * 2.0)
                        
                        # Simulate trade outcome
                        for j in range(i + 1, len(day_data)):
                            check = day_data.iloc[j]
                            if check['high'] >= tp:
                                trades.append(TradeResult(
                                    symbol=symbol, direction='BUY',
                                    entry_time=day_data.index[i], entry_price=row['close'],
                                    exit_time=day_data.index[j], exit_price=tp,
                                    stop_loss=sl, take_profit=tp,
                                    pnl=tp - row['close'], pnl_pips=(tp - row['close']) / 0.0001,
                                    is_win=True, exit_reason='TP'
                                ))
                                break
                            elif check['low'] <= sl:
                                trades.append(TradeResult(
                                    symbol=symbol, direction='BUY',
                                    entry_time=day_data.index[i], entry_price=row['close'],
                                    exit_time=day_data.index[j], exit_price=sl,
                                    stop_loss=sl, take_profit=tp,
                                    pnl=sl - row['close'], pnl_pips=(sl - row['close']) / 0.0001,
                                    is_win=False, exit_reason='SL'
                                ))
                                break
                        break  # Only one trade per day
                    
                    # Bearish breakout
                    elif row['close'] < orb_low and row['close'] < row['vwap']:
                        sl = orb_high + (row['atr'] * 0.5)
                        risk = sl - row['close']
                        tp = row['close'] - (risk * 2.0)
                        
                        for j in range(i + 1, len(day_data)):
                            check = day_data.iloc[j]
                            if check['low'] <= tp:
                                trades.append(TradeResult(
                                    symbol=symbol, direction='SELL',
                                    entry_time=day_data.index[i], entry_price=row['close'],
                                    exit_time=day_data.index[j], exit_price=tp,
                                    stop_loss=sl, take_profit=tp,
                                    pnl=row['close'] - tp, pnl_pips=(row['close'] - tp) / 0.0001,
                                    is_win=True, exit_reason='TP'
                                ))
                                break
                            elif check['high'] >= sl:
                                trades.append(TradeResult(
                                    symbol=symbol, direction='SELL',
                                    entry_time=day_data.index[i], entry_price=row['close'],
                                    exit_time=day_data.index[j], exit_price=sl,
                                    stop_loss=sl, take_profit=tp,
                                    pnl=row['close'] - sl, pnl_pips=(row['close'] - sl) / 0.0001,
                                    is_win=False, exit_reason='SL'
                                ))
                                break
                        break
            except Exception as e:
                continue
        
        return trades
    
    def calculate_results(self, trades: List[TradeResult], symbol: str, 
                         strategy: str, start: datetime, end: datetime) -> BacktestResult:
        """Calculate backtest statistics."""
        if not trades:
            return BacktestResult(
                symbol=symbol, strategy=strategy,
                period_start=start, period_end=end,
                total_trades=0, wins=0, losses=0, win_rate=0,
                total_pnl=0, profit_factor=0, max_drawdown=0,
                avg_win=0, avg_loss=0, expectancy=0,
                trades=[], confidence_score=0
            )
        
        wins = [t for t in trades if t.is_win]
        losses = [t for t in trades if not t.is_win]
        
        total_win_pnl = sum(t.pnl for t in wins)
        total_loss_pnl = abs(sum(t.pnl for t in losses))
        
        # Max drawdown
        cumulative = 0
        max_dd = 0
        peak = 0
        for t in trades:
            cumulative += t.pnl
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        
        win_rate = len(wins) / len(trades) * 100
        profit_factor = total_win_pnl / total_loss_pnl if total_loss_pnl > 0 else float('inf')
        avg_win = total_win_pnl / len(wins) if wins else 0
        avg_loss = total_loss_pnl / len(losses) if losses else 0
        
        # Expectancy = (Win% * Avg Win) - (Loss% * Avg Loss)
        expectancy = (win_rate/100 * avg_win) - ((100-win_rate)/100 * avg_loss)
        
        # Confidence score (0-100)
        confidence = 0
        if len(trades) >= 30:  # Minimum sample size
            confidence += 20
        if win_rate >= 40:
            confidence += 20
        if profit_factor >= 1.2:
            confidence += 25
        if expectancy > 0:
            confidence += 25
        if max_dd < total_win_pnl * 0.5:  # Max DD < 50% of wins
            confidence += 10
        
        return BacktestResult(
            symbol=symbol, strategy=strategy,
            period_start=start, period_end=end,
            total_trades=len(trades),
            wins=len(wins), losses=len(losses),
            win_rate=win_rate,
            total_pnl=sum(t.pnl for t in trades),
            profit_factor=profit_factor,
            max_drawdown=max_dd,
            avg_win=avg_win, avg_loss=avg_loss,
            expectancy=expectancy,
            trades=trades,
            confidence_score=min(100, confidence)
        )
    
    def run(self, symbol: str, strategy: str = 'MeanReversion', 
            days: int = 30) -> BacktestResult:
        """
        Run backtest on a symbol.
        
        Args:
            symbol: MT5 symbol
            strategy: 'MeanReversion' or 'ORB'
            days: Number of days to backtest
        """
        logger.info(f"Running {strategy} backtest on {symbol} for {days} days...")
        
        # Get data
        df = self.get_historical_data(symbol, mt5.TIMEFRAME_M15, days)
        if df is None or df.empty:
            logger.error(f"No data for {symbol}")
            return BacktestResult(
                symbol=symbol, strategy=strategy,
                period_start=datetime.now(), period_end=datetime.now(),
                total_trades=0, wins=0, losses=0, win_rate=0,
                total_pnl=0, profit_factor=0, max_drawdown=0,
                avg_win=0, avg_loss=0, expectancy=0,
                trades=[], confidence_score=0
            )
        
        # Add indicators
        df = self.calculate_indicators(df)
        
        # Run strategy
        if strategy.lower() == 'meanreversion':
            trades = self.run_mean_reversion(df, symbol)
        elif strategy.lower() == 'orb':
            trades = self.run_orb(df, symbol)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        # Calculate results
        return self.calculate_results(
            trades, symbol, strategy,
            df.index[0], df.index[-1]
        )
    
    def run_multi(self, symbols: List[str], strategy: str = 'MeanReversion',
                  days: int = 30) -> List[BacktestResult]:
        """Run backtest on multiple symbols."""
        results = []
        for symbol in symbols:
            try:
                result = self.run(symbol, strategy, days)
                results.append(result)
            except Exception as e:
                logger.error(f"Error backtesting {symbol}: {e}")
        return results
    
    def print_result(self, result: BacktestResult):
        """Print formatted backtest result."""
        print("\n" + "="*60)
        print(f"  BACKTEST: {result.strategy} on {result.symbol}")
        print(f"  Period: {result.period_start.strftime('%Y-%m-%d')} to {result.period_end.strftime('%Y-%m-%d')}")
        print("="*60)
        
        print(f"\n📊 Results:")
        print(f"  Total Trades: {result.total_trades}")
        print(f"  Win/Loss: {result.wins}W / {result.losses}L")
        print(f"  Win Rate: {result.win_rate:.1f}%")
        print(f"  Total P&L: {result.total_pnl:.5f} ({result.total_pnl * 10000:.0f} pips approx)")
        print(f"  Profit Factor: {result.profit_factor:.2f}")
        print(f"  Expectancy: {result.expectancy:.5f}")
        print(f"  Max Drawdown: {result.max_drawdown:.5f}")
        
        # Confidence assessment
        print(f"\n🎯 Confidence Score: {result.confidence_score}/100")
        if result.confidence_score >= 70:
            print("   ✅ Strategy looks viable for live trading")
        elif result.confidence_score >= 50:
            print("   ⚠️ Strategy needs more testing/optimization")
        else:
            print("   ❌ Strategy not recommended for live trading")
        
        # Exit reason breakdown
        if result.trades:
            tp_exits = sum(1 for t in result.trades if t.exit_reason == 'TP')
            sl_exits = sum(1 for t in result.trades if t.exit_reason == 'SL')
            sig_exits = sum(1 for t in result.trades if t.exit_reason == 'SIGNAL')
            print(f"\n📈 Exit Breakdown:")
            print(f"  TP Hits: {tp_exits} ({tp_exits/len(result.trades)*100:.0f}%)")
            print(f"  SL Hits: {sl_exits} ({sl_exits/len(result.trades)*100:.0f}%)")
            print(f"  Signal: {sig_exits} ({sig_exits/len(result.trades)*100:.0f}%)")


# Quick test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    bt = SimpleBacktester()
    
    # Test on major pairs
    symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
    
    for symbol in symbols:
        result = bt.run(symbol, 'MeanReversion', 30)
        bt.print_result(result)
    
    mt5.shutdown()
