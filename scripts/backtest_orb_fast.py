"""
Fast ORB Multi-Session Backtest
================================
Tests ORB across all 4 sessions using predefined high-liquidity symbols.
No scanning - direct symbol list for speed.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import logging
import sys
import os
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("ORB_Fast")


# ============================================================================
# SESSION CONFIGURATIONS (UTC)
# ============================================================================

SESSIONS = {
    'london':   {'start': 8,  'duration': 8, 'name': 'London Open'},
    'newyork':  {'start': 13, 'duration': 8, 'name': 'New York Open'},
    'tokyo':    {'start': 0,  'duration': 8, 'name': 'Tokyo Open'},
    'sydney':   {'start': 22, 'duration': 8, 'name': 'Sydney Open'},
}

# Pre-defined symbol lists (fast, no scanning)
SYMBOLS = {
    'forex': [
        'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'NZDUSD', 'USDCAD',
        'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'EURAUD', 'EURCHF', 'GBPCHF',
        'EURCAD', 'GBPCAD', 'AUDCAD', 'NZDJPY', 'CHFJPY', 'CADJPY',
        'EURNZD', 'GBPNZD', 'AUDNZD', 'NZDCAD', 'GBPAUD'
    ],
    'commodity': [
        'XAUUSD', 'XAGUSD', 'OILCash', 'BRENTCash', 'WTICOUSD', 
        'XAUUSDm', 'GOLDm', 'GOLD'
    ],
    'index': [
        'US30Cash', 'US100Cash', 'US500Cash', 'US2000Cash',
        'US30', 'NAS100', 'SPX500', 'DE40Cash', 'UK100Cash'
    ],
    'crypto': [
        'BTCUSD', 'ETHUSD', 'XRPUSD', 'LTCUSD', 'ADAUSD', 'SOLUSD', 'BTCEUR'
    ]
}


@dataclass
class Trade:
    symbol: str
    session: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    pnl: float
    is_win: bool
    exit_reason: str


def calculate_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df['high'] + df['low'] + df['close']) / 3
    return (tp * df['tick_volume']).cumsum() / df['tick_volume'].cumsum()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def backtest_orb(
    symbol: str,
    session_name: str,
    days: int = 30,
    vwap_confirm: bool = True,
    atr_mult: float = 0.5,
    risk_reward: float = 2.0
) -> List[Trade]:
    """
    Backtest ORB for a symbol/session combination.
    """
    if not mt5.initialize():
        return []
    
    session = SESSIONS[session_name]
    session_start_hour = session['start']
    session_duration = session['duration']
    
    # Fetch data
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, days * 96)
    if rates is None or len(rates) < 100:
        return []
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    df['vwap'] = calculate_vwap(df)
    df['atr'] = calculate_atr(df)
    df = df.dropna()
    
    trades = []
    
    # Group by date
    dates = df.index.normalize().unique()
    
    for date in dates:
        try:
            # Session start for this date
            session_start = date.replace(hour=session_start_hour, minute=0, second=0)
            
            # Handle sessions that might be on previous day (Sydney at 22:00)
            if session_start_hour >= 22:
                session_start = session_start - timedelta(days=1)
            
            session_end = session_start + timedelta(hours=session_duration)
            
            # Find ORB (first M15 bar of session)
            orb_mask = (df.index >= session_start) & (df.index < session_start + timedelta(minutes=15))
            orb_bars = df[orb_mask]
            
            if orb_bars.empty:
                continue
            
            orb_bar = orb_bars.iloc[0]
            orb_high = orb_bar['high']
            orb_low = orb_bar['low']
            orb_time = orb_bars.index[0]
            
            # Get session data after ORB
            session_mask = (df.index > orb_time) & (df.index < session_end)
            session_data = df[session_mask]
            
            if session_data.empty or len(session_data) < 2:
                continue
            
            # Look for breakout in first 20 bars
            for i in range(min(len(session_data), 20)):
                row = session_data.iloc[i]
                price = row['close']
                vwap = row['vwap']
                atr = row['atr']
                
                if atr == 0 or np.isnan(atr):
                    continue
                
                trade = None
                
                # BULLISH BREAKOUT
                if price > orb_high and (not vwap_confirm or price > vwap):
                    sl = orb_low - (atr * atr_mult)
                    risk = price - sl
                    tp = price + (risk * risk_reward)
                    
                    # Simulate trade
                    for j in range(i + 1, len(session_data)):
                        check = session_data.iloc[j]
                        if check['high'] >= tp:
                            trade = Trade(symbol, session_name, 'BUY', price, tp, sl, tp,
                                        tp - price, True, 'TP')
                            break
                        if check['low'] <= sl:
                            trade = Trade(symbol, session_name, 'BUY', price, sl, sl, tp,
                                        sl - price, False, 'SL')
                            break
                    
                    if trade is None and len(session_data) > i + 1:
                        # Closed at session end
                        exit_price = session_data.iloc[-1]['close']
                        pnl = exit_price - price
                        trade = Trade(symbol, session_name, 'BUY', price, exit_price, sl, tp,
                                    pnl, pnl > 0, 'EOD')
                
                # BEARISH BREAKOUT  
                elif price < orb_low and (not vwap_confirm or price < vwap):
                    sl = orb_high + (atr * atr_mult)
                    risk = sl - price
                    tp = price - (risk * risk_reward)
                    
                    for j in range(i + 1, len(session_data)):
                        check = session_data.iloc[j]
                        if check['low'] <= tp:
                            trade = Trade(symbol, session_name, 'SELL', price, tp, sl, tp,
                                        price - tp, True, 'TP')
                            break
                        if check['high'] >= sl:
                            trade = Trade(symbol, session_name, 'SELL', price, sl, sl, tp,
                                        price - sl, False, 'SL')
                            break
                    
                    if trade is None and len(session_data) > i + 1:
                        exit_price = session_data.iloc[-1]['close']
                        pnl = price - exit_price
                        trade = Trade(symbol, session_name, 'SELL', price, exit_price, sl, tp,
                                    pnl, pnl > 0, 'EOD')
                
                if trade:
                    trades.append(trade)
                    break  # One trade per session/day
                    
        except Exception as e:
            continue
    
    return trades


def main():
    print("\n" + "="*80)
    print("  FAST ORB MULTI-SESSION BACKTEST")
    print("  Testing London, New York, Tokyo, Sydney sessions")
    print("="*80 + "\n")
    
    if not mt5.initialize():
        print("MT5 init failed")
        return
    
    all_results = []
    
    for category, symbols in SYMBOLS.items():
        print(f"\n{'='*60}")
        print(f"  CATEGORY: {category.upper()}")
        print(f"{'='*60}")
        
        for symbol in symbols:
            # Check if symbol exists
            info = mt5.symbol_info(symbol)
            if info is None:
                continue
            
            logger.info(f"Testing {symbol}...")
            
            for session_name in SESSIONS.keys():
                trades = backtest_orb(symbol, session_name, days=30)
                
                if trades:
                    wins = sum(1 for t in trades if t.is_win)
                    win_rate = (wins / len(trades)) * 100 if trades else 0
                    gross_profit = sum(t.pnl for t in trades if t.pnl > 0)
                    gross_loss = abs(sum(t.pnl for t in trades if t.pnl < 0))
                    pf = gross_profit / gross_loss if gross_loss > 0 else 999
                    
                    all_results.append({
                        'category': category,
                        'symbol': symbol,
                        'session': session_name,
                        'trades': len(trades),
                        'wins': wins,
                        'win_rate': win_rate,
                        'profit_factor': pf,
                        'gross_pnl': gross_profit - gross_loss
                    })
                    
                    status = "✅" if win_rate >= 40 and pf >= 1.0 else "⚠️"
                    logger.info(f"  {status} {session_name:10} | Trades: {len(trades):3} | "
                               f"WR: {win_rate:5.1f}% | PF: {min(pf, 99.9):5.2f}")
    
    if not all_results:
        print("\nNo results. Check MT5 connection and symbol names.")
        mt5.shutdown()
        return
    
    df = pd.DataFrame(all_results)
    
    # Summary by session
    print("\n" + "="*80)
    print("  SESSION PERFORMANCE SUMMARY")
    print("="*80)
    
    for session in SESSIONS.keys():
        sd = df[df['session'] == session]
        if not sd.empty:
            avg_wr = sd['win_rate'].mean()
            valid_pf = sd[sd['profit_factor'] < 100]
            avg_pf = valid_pf['profit_factor'].mean() if not valid_pf.empty else 0
            total = sd['trades'].sum()
            print(f"  {session.upper():12} | Avg WR: {avg_wr:5.1f}% | Avg PF: {avg_pf:5.2f} | Trades: {total}")
    
    # Summary by category
    print("\n" + "="*80)
    print("  CATEGORY PERFORMANCE SUMMARY")
    print("="*80)
    
    for cat in ['forex', 'commodity', 'index', 'crypto']:
        cd = df[df['category'] == cat]
        if not cd.empty:
            avg_wr = cd['win_rate'].mean()
            valid_pf = cd[cd['profit_factor'] < 100]
            avg_pf = valid_pf['profit_factor'].mean() if not valid_pf.empty else 0
            total = cd['trades'].sum()
            print(f"  {cat.upper():12} | Avg WR: {avg_wr:5.1f}% | Avg PF: {avg_pf:5.2f} | Trades: {total}")
    
    # Top 10
    print("\n" + "="*80)
    print("  TOP 10 SYMBOL-SESSION COMBINATIONS (min 5 trades)")
    print("="*80)
    
    valid = df[(df['trades'] >= 5) & (df['profit_factor'] < 100)]
    if not valid.empty:
        top10 = valid.nlargest(10, ['win_rate', 'profit_factor'])
        for _, r in top10.iterrows():
            print(f"  {r['symbol']:12} | {r['session']:10} | {r['category']:10} | "
                 f"WR: {r['win_rate']:5.1f}% | PF: {r['profit_factor']:5.2f}")
    
    # Save report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ORB_MULTI_SESSION_RESULTS.md'
    )
    
    with open(report_path, 'w') as f:
        f.write("# ORB Multi-Session Backtest Results\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Strategy Logic\n\n")
        f.write("```\n")
        f.write("ORB = First M15 candle after session open\n")
        f.write("BUY = Close > ORB_High AND Close > VWAP\n")
        f.write("SELL = Close < ORB_Low AND Close < VWAP\n")
        f.write("Stop Loss = ORB opposite side - (0.5 × ATR)\n")
        f.write("Take Profit = 2:1 Risk-Reward\n")
        f.write("```\n\n")
        f.write("## Session Times (UTC)\n\n")
        f.write("| Session | Open Time |\n")
        f.write("|---------|----------|\n")
        for name, cfg in SESSIONS.items():
            f.write(f"| {name.capitalize()} | {cfg['start']:02d}:00 |\n")
        f.write("\n## Full Results\n\n")
        f.write("| Category | Symbol | Session | Trades | Win Rate | PF |\n")
        f.write("|----------|--------|---------|--------|----------|----|\n")
        for _, r in df.iterrows():
            pf_str = f"{r['profit_factor']:.2f}" if r['profit_factor'] < 100 else "∞"
            f.write(f"| {r['category']} | {r['symbol']} | {r['session']} | "
                   f"{r['trades']} | {r['win_rate']:.1f}% | {pf_str} |\n")
    
    print(f"\n📄 Report saved: {report_path}")
    mt5.shutdown()


if __name__ == "__main__":
    main()
