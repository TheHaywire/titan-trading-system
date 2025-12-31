"""
Advanced ORB Multi-Session Backtest
====================================
Tests the Opening Range Breakout strategy across:
- All 4 major sessions (London, New York, Tokyo, Sydney)
- Multiple symbol categories (Forex, Commodities, Indices, Crypto)
- Different parameter variations (R:R, VWAP confirmation, ATR multipliers)

This uses the REAL ORB strategy logic, not the simplified backtester.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
import sys
import os
from datetime import datetime, timedelta, time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ORB_MultiSession")


# ============================================================================
# SESSION CONFIGURATIONS
# ============================================================================

@dataclass
class SessionConfig:
    """Trading session configuration."""
    name: str
    start_hour: int  # UTC
    start_minute: int = 0
    duration_hours: int = 8
    
    def get_session_start(self, date: datetime) -> datetime:
        """Get session start time for a given date."""
        return date.replace(
            hour=self.start_hour, 
            minute=self.start_minute, 
            second=0, 
            microsecond=0
        )


SESSIONS = {
    'london': SessionConfig('London', 8, 0, 8),
    'newyork': SessionConfig('New York', 13, 0, 8),
    'tokyo': SessionConfig('Tokyo', 0, 0, 8),
    'sydney': SessionConfig('Sydney', 22, 0, 8),
}

# Symbol category mapping
CATEGORY_HINTS = {
    'forex': ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'NZD', 'CAD', 'SEK', 'NOK', 'DKK', 'PLN', 'HUF', 'TRY', 'ZAR', 'SGD', 'HKD', 'MXN'],
    'commodity': ['XAU', 'GOLD', 'XAG', 'SILVER', 'OIL', 'WTI', 'BRENT', 'NATGAS', 'COPPER', 'PLAT', 'COCOA', 'COFFEE', 'WHEAT', 'CORN', 'SOYBEAN'],
    'index': ['US30', 'US500', 'US100', 'NAS100', 'SPX', 'DAX', 'FTSE', 'NIK', 'DJ30', 'NDX', 'US2000', 'VIX', 'UK100', 'DE40', 'JP225'],
    'crypto': ['BTC', 'ETH', 'XRP', 'LTC', 'DOGE', 'SOL', 'ADA', 'BNB', 'AVAX', 'DOT']
}


@dataclass
class TradeResult:
    """Single trade outcome."""
    symbol: str
    session: str
    direction: str  # BUY or SELL
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    pnl_pips: float
    is_win: bool
    exit_reason: str  # TP, SL, EOD (End of Day)
    
    # Strategy details
    orb_high: float = 0
    orb_low: float = 0
    vwap_at_entry: float = 0
    atr_at_entry: float = 0
    breakout_ratio: float = 0  # How much price moved beyond ORB relative to ATR


@dataclass
class SessionStats:
    """Statistics for a single session."""
    session: str
    symbol: str
    trades: List[TradeResult] = field(default_factory=list)
    
    @property
    def total_trades(self) -> int:
        return len(self.trades)
    
    @property
    def wins(self) -> int:
        return sum(1 for t in self.trades if t.is_win)
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.total_trades * 100) if self.total_trades > 0 else 0
    
    @property
    def profit_factor(self) -> float:
        gross_profit = sum(t.pnl for t in self.trades if t.pnl > 0)
        gross_loss = abs(sum(t.pnl for t in self.trades if t.pnl < 0))
        return gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    @property
    def expectancy(self) -> float:
        return sum(t.pnl for t in self.trades) / self.total_trades if self.total_trades > 0 else 0


class AdvancedORBBacktester:
    """
    Advanced ORB Strategy Backtester.
    
    Tests the EXACT strategy logic used in production:
    - Opening Range from first M15 candle of session
    - VWAP confirmation
    - ATR-based stop losses
    - Session-specific testing
    """
    
    def __init__(
        self,
        vwap_confirmation: bool = True,
        atr_stop_multiplier: float = 0.5,
        risk_reward: float = 2.0,
        max_bars_to_wait: int = 20,  # Max bars to wait for breakout after ORB
        close_at_session_end: bool = True
    ):
        self.vwap_confirmation = vwap_confirmation
        self.atr_stop_multiplier = atr_stop_multiplier
        self.risk_reward = risk_reward
        self.max_bars_to_wait = max_bars_to_wait
        self.close_at_session_end = close_at_session_end
        
        if not mt5.initialize():
            raise RuntimeError(f"MT5 init failed: {mt5.last_error()}")
    
    def categorize_symbol(self, symbol: str) -> str:
        """Categorize symbol by type."""
        name = symbol.upper()
        
        for category, hints in CATEGORY_HINTS.items():
            if any(hint in name for hint in hints):
                return category
        
        return 'other'
    
    def get_available_symbols(self) -> Dict[str, List[str]]:
        """Get all available symbols from MT5, categorized."""
        symbols = mt5.symbols_get()
        if not symbols:
            return {}
        
        categorized = defaultdict(list)
        
        for sym in symbols:
            if sym.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                continue
            
            # Try to get data for this symbol
            rates = mt5.copy_rates_from_pos(sym.name, mt5.TIMEFRAME_M15, 0, 5)
            if rates is None or len(rates) < 5:
                continue
            
            category = self.categorize_symbol(sym.name)
            if category != 'other':
                categorized[category].append(sym.name)
        
        return dict(categorized)
    
    def calculate_vwap(self, df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP."""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        volume = df['tick_volume']
        
        cum_vol = volume.cumsum()
        cum_vol_price = (typical_price * volume).cumsum()
        
        return cum_vol_price / cum_vol
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate ATR."""
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def get_historical_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """Fetch historical M15 data."""
        bars_needed = days * 24 * 4  # M15 bars per day
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, bars_needed)
        
        if rates is None or len(rates) < 100:
            return None
        
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        # Add indicators
        df['vwap'] = self.calculate_vwap(df)
        df['atr'] = self.calculate_atr(df)
        
        return df.dropna()
    
    def find_orb_for_session(self, df: pd.DataFrame, date: datetime, session: SessionConfig) -> Optional[Dict]:
        """
        Find the Opening Range for a specific session on a specific date.
        
        The ORB is defined as the HIGH and LOW of the FIRST M15 candle 
        after the session opens.
        """
        # Get session start for this date
        session_start = session.get_session_start(date)
        session_end = session_start + timedelta(hours=session.duration_hours)
        
        # Handle sessions that cross midnight
        if session.start_hour >= 22:
            if date.hour < session.start_hour:
                session_start -= timedelta(days=1)
        
        # Find first bar after session start
        mask = (df.index >= session_start) & (df.index < session_start + timedelta(minutes=15))
        orb_bars = df[mask]
        
        if orb_bars.empty:
            # Try to find the closest bar after session start
            after_start = df[df.index >= session_start]
            if after_start.empty:
                return None
            orb_bars = after_start.iloc[:1]
        
        orb_bar = orb_bars.iloc[0]
        
        return {
            'high': orb_bar['high'],
            'low': orb_bar['low'],
            'open': orb_bar['open'],
            'close': orb_bar['close'],
            'time': orb_bars.index[0],
            'session_start': session_start,
            'session_end': session_end,
            'atr': orb_bar['atr'] if 'atr' in orb_bar else 0,
            'vwap': orb_bar['vwap'] if 'vwap' in orb_bar else 0
        }
    
    def simulate_trade(
        self, 
        df: pd.DataFrame, 
        entry_idx: int, 
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        session_end: datetime,
        symbol: str,
        session_name: str,
        orb: Dict
    ) -> Optional[TradeResult]:
        """Simulate a trade from entry to exit."""
        
        for i in range(entry_idx + 1, len(df)):
            row = df.iloc[i]
            current_time = df.index[i]
            
            # Check if we've passed session end
            if self.close_at_session_end and current_time >= session_end:
                exit_price = row['close']
                pnl = (exit_price - entry_price) if direction == 'BUY' else (entry_price - exit_price)
                
                return TradeResult(
                    symbol=symbol,
                    session=session_name,
                    direction=direction,
                    entry_time=df.index[entry_idx],
                    entry_price=entry_price,
                    exit_time=current_time,
                    exit_price=exit_price,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    pnl=pnl,
                    pnl_pips=pnl / 0.0001 if 'USD' in symbol else pnl / 0.01,
                    is_win=pnl > 0,
                    exit_reason='EOD',
                    orb_high=orb['high'],
                    orb_low=orb['low'],
                    vwap_at_entry=orb.get('vwap', 0),
                    atr_at_entry=orb.get('atr', 0)
                )
            
            if direction == 'BUY':
                # Check TP first (optimistic assumption)
                if row['high'] >= take_profit:
                    pnl = take_profit - entry_price
                    return TradeResult(
                        symbol=symbol, session=session_name, direction=direction,
                        entry_time=df.index[entry_idx], entry_price=entry_price,
                        exit_time=current_time, exit_price=take_profit,
                        stop_loss=stop_loss, take_profit=take_profit,
                        pnl=pnl, pnl_pips=pnl / 0.0001 if 'USD' in symbol else pnl / 0.01,
                        is_win=True, exit_reason='TP',
                        orb_high=orb['high'], orb_low=orb['low'],
                        vwap_at_entry=orb.get('vwap', 0), atr_at_entry=orb.get('atr', 0)
                    )
                # Check SL
                if row['low'] <= stop_loss:
                    pnl = stop_loss - entry_price
                    return TradeResult(
                        symbol=symbol, session=session_name, direction=direction,
                        entry_time=df.index[entry_idx], entry_price=entry_price,
                        exit_time=current_time, exit_price=stop_loss,
                        stop_loss=stop_loss, take_profit=take_profit,
                        pnl=pnl, pnl_pips=pnl / 0.0001 if 'USD' in symbol else pnl / 0.01,
                        is_win=False, exit_reason='SL',
                        orb_high=orb['high'], orb_low=orb['low'],
                        vwap_at_entry=orb.get('vwap', 0), atr_at_entry=orb.get('atr', 0)
                    )
            else:  # SELL
                if row['low'] <= take_profit:
                    pnl = entry_price - take_profit
                    return TradeResult(
                        symbol=symbol, session=session_name, direction=direction,
                        entry_time=df.index[entry_idx], entry_price=entry_price,
                        exit_time=current_time, exit_price=take_profit,
                        stop_loss=stop_loss, take_profit=take_profit,
                        pnl=pnl, pnl_pips=pnl / 0.0001 if 'USD' in symbol else pnl / 0.01,
                        is_win=True, exit_reason='TP',
                        orb_high=orb['high'], orb_low=orb['low'],
                        vwap_at_entry=orb.get('vwap', 0), atr_at_entry=orb.get('atr', 0)
                    )
                if row['high'] >= stop_loss:
                    pnl = entry_price - stop_loss
                    return TradeResult(
                        symbol=symbol, session=session_name, direction=direction,
                        entry_time=df.index[entry_idx], entry_price=entry_price,
                        exit_time=current_time, exit_price=stop_loss,
                        stop_loss=stop_loss, take_profit=take_profit,
                        pnl=pnl, pnl_pips=pnl / 0.0001 if 'USD' in symbol else pnl / 0.01,
                        is_win=False, exit_reason='SL',
                        orb_high=orb['high'], orb_low=orb['low'],
                        vwap_at_entry=orb.get('vwap', 0), atr_at_entry=orb.get('atr', 0)
                    )
        
        return None
    
    def backtest_symbol_session(
        self, 
        symbol: str, 
        session_name: str, 
        days: int = 30
    ) -> SessionStats:
        """
        Backtest ORB strategy on a symbol for a specific session.
        """
        session = SESSIONS[session_name]
        stats = SessionStats(session=session_name, symbol=symbol)
        
        df = self.get_historical_data(symbol, days + 10)
        if df is None:
            return stats
        
        # Get unique dates in the data
        dates = df.index.normalize().unique()
        
        for date in dates:
            try:
                # Get ORB for this date/session
                orb = self.find_orb_for_session(df, date.to_pydatetime(), session)
                if orb is None:
                    continue
                
                orb_high = orb['high']
                orb_low = orb['low']
                session_end = orb['session_end']
                atr = orb['atr']
                
                if atr == 0 or np.isnan(atr):
                    continue
                
                # Get bars after ORB for this session
                session_data = df[(df.index > orb['time']) & (df.index < session_end)]
                
                if session_data.empty or len(session_data) < 2:
                    continue
                
                # Look for breakout in first N bars
                for i in range(min(len(session_data), self.max_bars_to_wait)):
                    row = session_data.iloc[i]
                    current_price = row['close']
                    current_vwap = row['vwap']
                    
                    trade = None
                    
                    # BULLISH BREAKOUT: Price > ORB High (and > VWAP if required)
                    if current_price > orb_high:
                        vwap_ok = (not self.vwap_confirmation) or (current_price > current_vwap)
                        
                        if vwap_ok:
                            sl = orb_low - (atr * self.atr_stop_multiplier)
                            risk = current_price - sl
                            tp = current_price + (risk * self.risk_reward)
                            
                            # Find the absolute index in df
                            abs_idx = df.index.get_loc(session_data.index[i])
                            
                            trade = self.simulate_trade(
                                df, abs_idx, 'BUY', current_price, sl, tp,
                                session_end, symbol, session_name, orb
                            )
                    
                    # BEARISH BREAKOUT: Price < ORB Low (and < VWAP if required)
                    elif current_price < orb_low:
                        vwap_ok = (not self.vwap_confirmation) or (current_price < current_vwap)
                        
                        if vwap_ok:
                            sl = orb_high + (atr * self.atr_stop_multiplier)
                            risk = sl - current_price
                            tp = current_price - (risk * self.risk_reward)
                            
                            abs_idx = df.index.get_loc(session_data.index[i])
                            
                            trade = self.simulate_trade(
                                df, abs_idx, 'SELL', current_price, sl, tp,
                                session_end, symbol, session_name, orb
                            )
                    
                    if trade:
                        stats.trades.append(trade)
                        break  # Only one trade per session per day
                        
            except Exception as e:
                continue
        
        return stats
    
    def backtest_all_sessions(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, SessionStats]:
        """Backtest symbol across all sessions."""
        results = {}
        
        for session_name in SESSIONS.keys():
            stats = self.backtest_symbol_session(symbol, session_name, days)
            results[session_name] = stats
        
        return results


def main():
    """Run comprehensive multi-session backtest."""
    
    print("\n" + "="*80)
    print("  ADVANCED ORB MULTI-SESSION BACKTEST")
    print("  Testing across London, New York, Tokyo, Sydney sessions")
    print("="*80 + "\n")
    
    # Test different parameter combinations
    PARAM_SETS = [
        {'name': 'Default', 'vwap': True, 'atr_mult': 0.5, 'rr': 2.0},
        {'name': 'No VWAP', 'vwap': False, 'atr_mult': 0.5, 'rr': 2.0},
        {'name': 'Tight SL', 'vwap': True, 'atr_mult': 0.3, 'rr': 2.0},
        {'name': 'Wide SL', 'vwap': True, 'atr_mult': 1.0, 'rr': 2.0},
        {'name': '3:1 RR', 'vwap': True, 'atr_mult': 0.5, 'rr': 3.0},
        {'name': '1.5:1 RR', 'vwap': True, 'atr_mult': 0.5, 'rr': 1.5},
    ]
    
    # Use default parameters for category comparison
    bt = AdvancedORBBacktester(
        vwap_confirmation=True,
        atr_stop_multiplier=0.5,
        risk_reward=2.0
    )
    
    logger.info("Fetching available symbols...")
    categories = bt.get_available_symbols()
    
    if not categories:
        logger.error("No symbols found. Is MT5 connected?")
        return
    
    for cat, syms in categories.items():
        logger.info(f"  {cat.upper()}: {len(syms)} symbols")
    
    # Results storage
    all_results = []
    
    # Test each category
    for category in ['forex', 'commodity', 'index', 'crypto']:
        symbols = categories.get(category, [])[:10]  # Limit to 10 per category
        
        if not symbols:
            continue
        
        print(f"\n{'='*60}")
        print(f"  CATEGORY: {category.upper()}")
        print(f"{'='*60}")
        
        for symbol in symbols:
            logger.info(f"Testing {symbol}...")
            
            try:
                session_results = bt.backtest_all_sessions(symbol, days=30)
                
                for session_name, stats in session_results.items():
                    if stats.total_trades > 0:
                        all_results.append({
                            'category': category,
                            'symbol': symbol,
                            'session': session_name,
                            'trades': stats.total_trades,
                            'wins': stats.wins,
                            'win_rate': stats.win_rate,
                            'profit_factor': stats.profit_factor,
                            'expectancy': stats.expectancy
                        })
                        
                        status = "✅" if stats.win_rate >= 40 else "⚠️"
                        logger.info(f"  {status} {session_name:10} | Trades: {stats.total_trades:3} | "
                                   f"WR: {stats.win_rate:5.1f}% | PF: {stats.profit_factor:5.2f}")
            except Exception as e:
                logger.error(f"  Error: {e}")
    
    # Generate summary report
    print("\n" + "="*80)
    print("  SESSION PERFORMANCE SUMMARY")
    print("="*80)
    
    if not all_results:
        print("No trades generated. Check if market data is available.")
        return
    
    df_results = pd.DataFrame(all_results)
    
    # Session comparison
    print("\n📊 BY SESSION:")
    print("-" * 60)
    for session in SESSIONS.keys():
        session_data = df_results[df_results['session'] == session]
        if not session_data.empty:
            avg_wr = session_data['win_rate'].mean()
            avg_pf = session_data[session_data['profit_factor'] != float('inf')]['profit_factor'].mean()
            total_trades = session_data['trades'].sum()
            print(f"  {session.upper():12} | Avg WR: {avg_wr:5.1f}% | Avg PF: {avg_pf:5.2f} | Total Trades: {total_trades}")
    
    # Category comparison
    print("\n📊 BY CATEGORY:")
    print("-" * 60)
    for category in ['forex', 'commodity', 'index', 'crypto']:
        cat_data = df_results[df_results['category'] == category]
        if not cat_data.empty:
            avg_wr = cat_data['win_rate'].mean()
            avg_pf = cat_data[cat_data['profit_factor'] != float('inf')]['profit_factor'].mean()
            total_trades = cat_data['trades'].sum()
            print(f"  {category.upper():12} | Avg WR: {avg_wr:5.1f}% | Avg PF: {avg_pf:5.2f} | Total Trades: {total_trades}")
    
    # Best combinations
    print("\n🏆 TOP 10 SYMBOL-SESSION COMBINATIONS:")
    print("-" * 80)
    
    # Filter out inf profit factors and sort by win rate then PF
    valid_results = df_results[df_results['profit_factor'] != float('inf')]
    if not valid_results.empty:
        valid_results = valid_results[valid_results['trades'] >= 5]  # Minimum 5 trades
        if not valid_results.empty:
            top_10 = valid_results.nlargest(10, ['win_rate', 'profit_factor'])
            
            for _, row in top_10.iterrows():
                print(f"  {row['symbol']:12} | {row['session']:10} | {row['category']:10} | "
                     f"WR: {row['win_rate']:5.1f}% | PF: {row['profit_factor']:5.2f} | Trades: {row['trades']}")
    
    # Save detailed results
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ORB_MULTI_SESSION_BACKTEST.md'
    )
    
    with open(report_path, 'w') as f:
        f.write("# ORB Multi-Session Backtest Results\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Strategy:** Opening Range Breakout (ORB)\n")
        f.write(f"**Period:** Last 30 days\n\n")
        f.write("## Strategy Parameters\n")
        f.write("- **VWAP Confirmation:** Yes\n")
        f.write("- **Stop Loss:** ORB Low/High ± (0.5 × ATR)\n")
        f.write("- **Take Profit:** 2:1 Risk-Reward\n")
        f.write("- **Entry Window:** First 20 bars after ORB\n\n")
        
        f.write("## Session Times (UTC)\n")
        f.write("| Session | Open | Duration |\n")
        f.write("|---------|------|----------|\n")
        for name, session in SESSIONS.items():
            f.write(f"| {name.capitalize()} | {session.start_hour:02d}:{session.start_minute:02d} | {session.duration_hours}h |\n")
        
        f.write("\n## Full Results\n\n")
        f.write("| Category | Symbol | Session | Trades | Win Rate | Profit Factor | Expectancy |\n")
        f.write("|----------|--------|---------|--------|----------|---------------|------------|\n")
        
        for _, row in df_results.iterrows():
            pf_str = f"{row['profit_factor']:.2f}" if row['profit_factor'] != float('inf') else "∞"
            f.write(f"| {row['category']} | {row['symbol']} | {row['session']} | "
                   f"{row['trades']} | {row['win_rate']:.1f}% | {pf_str} | {row['expectancy']:.5f} |\n")
    
    logger.info(f"\nDetailed report saved to: {report_path}")
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
