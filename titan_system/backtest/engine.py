"""
PROFESSIONAL BACKTESTING ENGINE
================================
Core backtesting framework for testing strategies on historical data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Tuple, Optional
import MetaTrader5 as mt5


@dataclass
class Trade:
    """Represents a single trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    direction: str  # 'BUY' or 'SELL'
    size: float
    profit: float
    pips: float
    reason: str


@dataclass
class BacktestResult:
    """Results from a backtest"""
    strategy_name: str
    symbol: str
    timeframe: str
    
    # Performance Metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    
    total_return: float
    total_return_pct: float
    max_drawdown: float
    max_drawdown_pct: float
    
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    
    avg_win: float
    avg_loss: float
    avg_rr: float
    
    largest_win: float
    largest_loss: float
    
    # Statistical
    expectancy: float
    p_value: float
    
    # Equity curve
    equity_curve: List[float]
    trades: List[Trade]


class BacktestEngine:
    """
    Professional backtesting engine.
    """
    
    def __init__(self, symbol: str, timeframe: int, start_date: datetime, end_date: datetime):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.data = None
        
    def fetch_data(self) -> pd.DataFrame:
        """Fetch historical data from MT5"""
        if not mt5.initialize():
            raise Exception("MT5 initialization failed")
        
        if not mt5.symbol_select(self.symbol, True):
            mt5.shutdown()
            raise Exception(f"Cannot select {self.symbol}")
        
        # Calculate number of bars needed
        rates = mt5.copy_rates_range(self.symbol, self.timeframe, self.start_date, self.end_date)
        
        if rates is None or len(rates) == 0:
            mt5.shutdown()
            raise Exception(f"No data for {self.symbol}")
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        mt5.shutdown()
        
        self.data = df
        return df
    
    def run_backtest(self, strategy, initial_capital: float = 10000, risk_pct: float = 0.02):
        """
        Run backtest for a given strategy.
        
        Args:
            strategy: Strategy object with analyze() method
            initial_capital: Starting capital
            risk_pct: Risk per trade as percentage of capital
        """
        if self.data is None:
            self.fetch_data()
        
        capital = initial_capital
        equity_curve = [capital]
        trades = []
        position = None
        
        # Calculate indicators once
        df = strategy.calculate_indicators(self.data.copy())
        
        # Walk through data bar by bar
        for i in range(100, len(df)):  # Start after enough bars for indicators
            current_bar = df.iloc[i]
            current_time = current_bar['time']
            
            # Check if we have an open position
            if position:
                # Check exit conditions
                exit_signal = strategy.check_exit(df.iloc[:i+1], position)
                
                if exit_signal:
                    # Close position
                    exit_price = current_bar['close']
                    
                    if position['direction'] == 'BUY':
                        pips = exit_price - position['entry_price']
                        profit = pips * position['size']
                    else:
                        pips = position['entry_price'] - exit_price
                        profit = pips * position['size']
                    
                    capital += profit
                    
                    trade = Trade(
                        entry_time=position['entry_time'],
                        exit_time=current_time,
                        entry_price=position['entry_price'],
                        exit_price=exit_price,
                        direction=position['direction'],
                        size=position['size'],
                        profit=profit,
                        pips=pips,
                        reason=exit_signal
                    )
                    trades.append(trade)
                    equity_curve.append(capital)
                    position = None
            
            else:
                # Check entry conditions
                signal = strategy.analyze(df.iloc[:i+1])
                
                if signal:
                    # Calculate position size based on risk
                    risk_amount = capital * risk_pct
                    
                    # Simple position sizing (can be improved with ATR)
                    atr = df.iloc[i].get('atr', 0.001)
                    sl_distance = atr * 2
                    size = risk_amount / sl_distance if sl_distance > 0 else 1
                    
                    position = {
                        'direction': signal['direction'],
                        'entry_price': current_bar['close'],
                        'entry_time': current_time,
                        'size': size,
                        'sl': signal.get('stop_loss'),
                        'tp': signal.get('take_profit')
                    }
        
        # Close any remaining position at end
        if position:
            exit_price = df.iloc[-1]['close']
            if position['direction'] == 'BUY':
                pips = exit_price - position['entry_price']
                profit = pips * position['size']
            else:
                pips = position['entry_price'] - exit_price
                profit = pips * position['size']
            
            capital += profit
            
            trade = Trade(
                entry_time=position['entry_time'],
                exit_time=df.iloc[-1]['time'],
                entry_price=position['entry_price'],
                exit_price=exit_price,
                direction=position['direction'],
                size=position['size'],
                profit=profit,
                pips=pips,
                reason='End of backtest'
            )
            trades.append(trade)
            equity_curve.append(capital)
        
        # Calculate metrics
        result = self.calculate_metrics(
            strategy_name=strategy.name,
            trades=trades,
            equity_curve=equity_curve,
            initial_capital=initial_capital
        )
        
        return result
    
    def calculate_metrics(self, strategy_name: str, trades: List[Trade], 
                         equity_curve: List[float], initial_capital: float) -> BacktestResult:
        """Calculate performance metrics"""
        
        if len(trades) == 0:
            return BacktestResult(
                strategy_name=strategy_name,
                symbol=self.symbol,
                timeframe=self.get_tf_string(),
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                win_rate=0,
                total_return=0,
                total_return_pct=0,
                max_drawdown=0,
                max_drawdown_pct=0,
                sharpe_ratio=0,
                sortino_ratio=0,
                profit_factor=0,
                avg_win=0,
                avg_loss=0,
                avg_rr=0,
                largest_win=0,
                largest_loss=0,
                expectancy=0,
                p_value=1.0,
                equity_curve=equity_curve,
                trades=trades
            )
        
        # Basic stats
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.profit > 0])
        losing_trades = len([t for t in trades if t.profit < 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Returns
        final_capital = equity_curve[-1]
        total_return = final_capital - initial_capital
        total_return_pct = (total_return / initial_capital) * 100
        
        # Drawdown
        peak = equity_curve[0]
        max_dd = 0
        for equity in equity_curve:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd
        max_dd_pct = (max_dd / initial_capital) * 100
        
        # Win/Loss stats
        wins = [t.profit for t in trades if t.profit > 0]
        losses = [abs(t.profit) for t in trades if t.profit < 0]
        
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0
        largest_win = max(wins) if wins else 0
        largest_loss = max(losses) if losses else 0
        
        # Profit factor
        total_wins = sum(wins) if wins else 0
        total_losses = sum(losses) if losses else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Sharpe Ratio (simplified - using trade returns)
        returns = [t.profit / initial_capital for t in trades]
        if len(returns) > 1:
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        # Sortino (downside deviation)
        downside_returns = [r for r in returns if r < 0]
        if len(downside_returns) > 1:
            sortino = np.mean(returns) / np.std(downside_returns) * np.sqrt(252) if np.std(downside_returns) > 0 else 0
        else:
            sortino = 0
        
        # Expectancy
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        
        # Average RR
        avg_rr = avg_win / avg_loss if avg_loss > 0 else 0
        
        # P-value (t-test against zero mean)
        from scipy import stats
        if len(returns) > 2:
            t_stat, p_value = stats.ttest_1samp(returns, 0)
            p_value = p_value / 2  # One-tailed test
        else:
            p_value = 1.0
        
        return BacktestResult(
            strategy_name=strategy_name,
            symbol=self.symbol,
            timeframe=self.get_tf_string(),
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_return=total_return,
            total_return_pct=total_return_pct,
            max_drawdown=max_dd,
            max_drawdown_pct=max_dd_pct,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            profit_factor=profit_factor,
            avg_win=avg_win,
            avg_loss=avg_loss,
            avg_rr=avg_rr,
            largest_win=largest_win,
            largest_loss=largest_loss,
            expectancy=expectancy,
            p_value=p_value,
            equity_curve=equity_curve,
            trades=trades
        )
    
    def get_tf_string(self):
        """Convert MT5 timeframe to string"""
        tf_map = {
            mt5.TIMEFRAME_M1: "M1",
            mt5.TIMEFRAME_M5: "M5",
            mt5.TIMEFRAME_M15: "M15",
            mt5.TIMEFRAME_M30: "M30",
            mt5.TIMEFRAME_H1: "H1",
            mt5.TIMEFRAME_H4: "H4",
            mt5.TIMEFRAME_D1: "D1"
        }
        return tf_map.get(self.timeframe, "UNKNOWN")
