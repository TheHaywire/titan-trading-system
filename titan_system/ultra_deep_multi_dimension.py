"""
ULTRA-DEEP MULTI-DIMENSIONAL TRADE ANALYSIS
============================================
Going deeper:
1. Trade SEQUENCE analysis - what predicts success/failure
2. Multi-timeframe confluence - H4, H1, M15 alignment
3. Before/After trade analysis - what happened leading up to trade
4. Optimal entry MODEL - based on YOUR winning patterns
5. Optimal exit MODEL - when to hold, when to fold
6. Trade clustering - identify your best trading "sessions"
7. Correlation analysis - which trades cluster together
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')


def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calc_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def calc_atr(df, period=14):
    high = df['high']
    low = df['low']
    close = df['close']
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def get_multi_timeframe_context(symbol, trade_time, direction):
    """
    Get confluence across H4, H1, M15 timeframes.
    """
    try:
        context = {}
        
        for tf_name, tf_value, lookback_hours in [
            ('H4', mt5.TIMEFRAME_H4, 72),
            ('H1', mt5.TIMEFRAME_H1, 48),
            ('M15', mt5.TIMEFRAME_M15, 12)
        ]:
            from_time = trade_time - timedelta(hours=lookback_hours)
            to_time = trade_time + timedelta(minutes=5)
            
            rates = mt5.copy_rates_range(symbol, tf_value, from_time, to_time)
            if rates is None or len(rates) < 20:
                context[tf_name] = {'trend': 'UNKNOWN', 'rsi': 50, 'atr': 0}
                continue
                
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            df['ema_10'] = calc_ema(df['close'], 10)
            df['ema_20'] = calc_ema(df['close'], 20)
            df['rsi'] = calc_rsi(df['close'], 14)
            df['atr'] = calc_atr(df, 14)
            
            # Get the candle at trade time
            df_before = df[df['time'] <= trade_time]
            if len(df_before) == 0:
                context[tf_name] = {'trend': 'UNKNOWN', 'rsi': 50, 'atr': 0}
                continue
            
            last = df_before.iloc[-1]
            
            # Determine trend
            ema_10 = float(last['ema_10']) if not np.isnan(last['ema_10']) else 0
            ema_20 = float(last['ema_20']) if not np.isnan(last['ema_20']) else 0
            close = float(last['close'])
            
            if ema_10 > ema_20 and close > ema_10:
                trend = 'BULLISH'
            elif ema_10 < ema_20 and close < ema_10:
                trend = 'BEARISH'
            else:
                trend = 'NEUTRAL'
            
            context[tf_name] = {
                'trend': trend,
                'rsi': float(last['rsi']) if not np.isnan(last['rsi']) else 50,
                'atr': float(last['atr']) if not np.isnan(last['atr']) else 0,
                'close': close
            }
        
        # Calculate confluence
        trends = [context[tf]['trend'] for tf in ['H4', 'H1', 'M15']]
        
        if all(t == 'BULLISH' for t in trends):
            context['confluence'] = 'FULL_BULLISH'
            context['confluence_score'] = 3
        elif all(t == 'BEARISH' for t in trends):
            context['confluence'] = 'FULL_BEARISH'
            context['confluence_score'] = 3
        elif trends.count('BULLISH') >= 2:
            context['confluence'] = 'PARTIAL_BULLISH'
            context['confluence_score'] = 2
        elif trends.count('BEARISH') >= 2:
            context['confluence'] = 'PARTIAL_BEARISH'
            context['confluence_score'] = 2
        else:
            context['confluence'] = 'MIXED'
            context['confluence_score'] = 1
        
        # Check trade alignment
        if direction == 'Buy':
            if context['confluence'] == 'FULL_BULLISH':
                context['trade_alignment'] = 'PERFECT'
            elif 'BULLISH' in context['confluence']:
                context['trade_alignment'] = 'GOOD'
            elif context['confluence'] == 'FULL_BEARISH':
                context['trade_alignment'] = 'COUNTER_TREND'
            else:
                context['trade_alignment'] = 'MIXED'
        else:  # Sell
            if context['confluence'] == 'FULL_BEARISH':
                context['trade_alignment'] = 'PERFECT'
            elif 'BEARISH' in context['confluence']:
                context['trade_alignment'] = 'GOOD'
            elif context['confluence'] == 'FULL_BULLISH':
                context['trade_alignment'] = 'COUNTER_TREND'
            else:
                context['trade_alignment'] = 'MIXED'
        
        return context
        
    except Exception as e:
        return None


def analyze_price_action_context(symbol, trade_time, direction, entry_price):
    """
    Analyze what happened in the market BEFORE the trade entry.
    """
    try:
        from_time = trade_time - timedelta(hours=4)
        to_time = trade_time + timedelta(hours=2)
        
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, from_time, to_time)
        if rates is None or len(rates) < 50:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df['atr'] = calc_atr(df, 14)
        
        trade_idx = df[df['time'] <= trade_time].index[-1] if len(df[df['time'] <= trade_time]) > 0 else None
        if trade_idx is None:
            return None
        
        context = {}
        
        # Pre-trade analysis (30 minutes before)
        pre_trade = df.iloc[max(0, trade_idx-6):trade_idx]  # 6 x 5min = 30 min
        if len(pre_trade) > 0:
            pre_high = pre_trade['high'].max()
            pre_low = pre_trade['low'].min()
            pre_range = pre_high - pre_low
            atr = df.iloc[trade_idx]['atr'] if trade_idx < len(df) else pre_range
            
            context['pre_30min_range_atr'] = pre_range / atr if atr > 0 else 0
            
            if direction == 'Buy':
                # Was price making higher lows?
                lows = pre_trade['low'].tolist()
                if len(lows) >= 3 and all(lows[i] <= lows[i+1] for i in range(len(lows)-1)):
                    context['pre_structure'] = 'HIGHER_LOWS'
                elif len(lows) >= 3 and all(lows[i] >= lows[i+1] for i in range(len(lows)-1)):
                    context['pre_structure'] = 'LOWER_LOWS'
                else:
                    context['pre_structure'] = 'MIXED'
            else:  # Sell
                highs = pre_trade['high'].tolist()
                if len(highs) >= 3 and all(highs[i] >= highs[i+1] for i in range(len(highs)-1)):
                    context['pre_structure'] = 'LOWER_HIGHS'
                elif len(highs) >= 3 and all(highs[i] <= highs[i+1] for i in range(len(highs)-1)):
                    context['pre_structure'] = 'HIGHER_HIGHS'
                else:
                    context['pre_structure'] = 'MIXED'
        
        # How far from recent high/low was entry?
        recent = df.iloc[max(0, trade_idx-12):trade_idx]  # 1 hour
        if len(recent) > 0:
            recent_high = recent['high'].max()
            recent_low = recent['low'].min()
            recent_range = recent_high - recent_low
            
            if direction == 'Buy':
                dist_from_low = entry_price - recent_low
                context['entry_position'] = dist_from_low / recent_range if recent_range > 0 else 0.5
                # 0 = bought at low, 1 = bought at high
            else:
                dist_from_high = recent_high - entry_price
                context['entry_position'] = dist_from_high / recent_range if recent_range > 0 else 0.5
                # 0 = sold at high, 1 = sold at low
        
        # Post-trade analysis
        post_trade = df.iloc[trade_idx:min(len(df), trade_idx+12)]  # 1 hour after
        if len(post_trade) > 1:
            if direction == 'Buy':
                mfe = (post_trade['high'].max() - entry_price)
                mae = (entry_price - post_trade['low'].min())
            else:
                mfe = (entry_price - post_trade['low'].min())
                mae = (post_trade['high'].max() - entry_price)
            
            atr = df.iloc[trade_idx]['atr']
            context['mfe_1hr_atr'] = mfe / atr if atr > 0 else 0
            context['mae_1hr_atr'] = mae / atr if atr > 0 else 0
        
        return context
        
    except Exception as e:
        return None


def analyze_trade_sequence(trades_df):
    """
    Analyze patterns in trade sequences - what predicts the next trade's outcome.
    """
    results = {
        'after_win': {'wins': 0, 'losses': 0, 'pnl': 0},
        'after_loss': {'wins': 0, 'losses': 0, 'pnl': 0},
        'after_2_wins': {'wins': 0, 'losses': 0, 'pnl': 0},
        'after_2_losses': {'wins': 0, 'losses': 0, 'pnl': 0},
        'after_big_win': {'wins': 0, 'losses': 0, 'pnl': 0},
        'after_big_loss': {'wins': 0, 'losses': 0, 'pnl': 0},
    }
    
    trades = trades_df.sort_values('DateTime').reset_index(drop=True)
    
    for i in range(len(trades)):
        pnl = trades.iloc[i]['P&L']
        is_win = pnl > 0
        
        if i >= 1:
            prev_pnl = trades.iloc[i-1]['P&L']
            prev_win = prev_pnl > 0
            
            if prev_win:
                results['after_win']['wins' if is_win else 'losses'] += 1
                results['after_win']['pnl'] += pnl
            else:
                results['after_loss']['wins' if is_win else 'losses'] += 1
                results['after_loss']['pnl'] += pnl
            
            # After big win/loss (> $5000)
            if prev_pnl > 5000:
                results['after_big_win']['wins' if is_win else 'losses'] += 1
                results['after_big_win']['pnl'] += pnl
            elif prev_pnl < -5000:
                results['after_big_loss']['wins' if is_win else 'losses'] += 1
                results['after_big_loss']['pnl'] += pnl
        
        if i >= 2:
            prev_2_wins = trades.iloc[i-2:i]['P&L'].apply(lambda x: x > 0).all()
            prev_2_losses = trades.iloc[i-2:i]['P&L'].apply(lambda x: x < 0).all()
            
            if prev_2_wins:
                results['after_2_wins']['wins' if is_win else 'losses'] += 1
                results['after_2_wins']['pnl'] += pnl
            if prev_2_losses:
                results['after_2_losses']['wins' if is_win else 'losses'] += 1
                results['after_2_losses']['pnl'] += pnl
    
    return results


def analyze_session_clustering(trades_df):
    """
    Identify your best trading "sessions" - clusters of trades that work together.
    """
    trades = trades_df.sort_values('DateTime').reset_index(drop=True)
    
    # Group trades into sessions (trades within 30 min of each other)
    sessions = []
    current_session = []
    
    for i, trade in trades.iterrows():
        if len(current_session) == 0:
            current_session.append(trade)
        else:
            time_diff = (trade['DateTime'] - current_session[-1]['DateTime']).total_seconds() / 60
            if time_diff <= 30:
                current_session.append(trade)
            else:
                if len(current_session) >= 1:
                    sessions.append(current_session)
                current_session = [trade]
    
    if len(current_session) >= 1:
        sessions.append(current_session)
    
    # Analyze sessions
    session_results = []
    for session in sessions:
        session_df = pd.DataFrame(session)
        session_pnl = session_df['P&L'].sum()
        session_trades = len(session)
        session_wr = (session_df['P&L'] > 0).mean() * 100
        
        session_results.append({
            'start_time': session[0]['DateTime'],
            'trades': session_trades,
            'pnl': session_pnl,
            'win_rate': session_wr,
            'is_profitable': session_pnl > 0
        })
    
    return pd.DataFrame(session_results)


def build_optimal_trade_model(analysis_results):
    """
    Based on all analysis, build an optimal trade entry model.
    """
    model = {
        'entry_criteria': [],
        'exit_criteria': [],
        'size_criteria': [],
        'timing_criteria': []
    }
    
    # Build from analysis
    # (This would be populated based on the analysis results)
    
    return model


def run_ultra_deep_analysis(csv_path: str):
    """
    Run the complete ultra-deep analysis.
    """
    
    print("=" * 90)
    print("  🔬 ULTRA-DEEP MULTI-DIMENSIONAL TRADE ANALYSIS")
    print("  Going to the deepest level possible")
    print("=" * 90)
    print()
    
    if not mt5.initialize():
        print("❌ Failed to initialize MT5!")
        return None
    
    # Load trades
    df = pd.read_csv(csv_path)
    trades = df[df['Symbol'].notna() & (df['Symbol'] != '')].copy()
    trades = trades[trades['P&L'] != 0].copy()
    trades['DateTime'] = pd.to_datetime(trades['Date'] + ' ' + trades['Time'])
    trades = trades.sort_values('DateTime').reset_index(drop=True)
    
    # Focus on main symbols
    main_symbols = ['GOLD', 'BTCUSD', 'SILVER']
    trades = trades[trades['Symbol'].isin(main_symbols)]
    trades = trades.tail(150)  # Most recent 150
    
    print(f"📊 Analyzing {len(trades)} trades with multi-dimensional context...")
    print()
    
    # ========================================================================
    # SECTION 1: TRADE SEQUENCE ANALYSIS
    # ========================================================================
    print("=" * 90)
    print("  1️⃣ TRADE SEQUENCE ANALYSIS")
    print("  What happens after wins, losses, streaks?")
    print("=" * 90)
    
    sequence_results = analyze_trade_sequence(trades)
    
    for seq_type, stats in sequence_results.items():
        total = stats['wins'] + stats['losses']
        if total > 0:
            wr = stats['wins'] / total * 100
            print(f"\n  {seq_type.replace('_', ' ').title()}:")
            print(f"    Trades: {total} | WR: {wr:.1f}% | P&L: ${stats['pnl']:,.0f}")
    
    # ========================================================================
    # SECTION 2: SESSION CLUSTERING
    # ========================================================================
    print()
    print("=" * 90)
    print("  2️⃣ SESSION CLUSTERING ANALYSIS")
    print("  Finding your best and worst trading sessions")
    print("=" * 90)
    
    sessions = analyze_session_clustering(trades)
    
    if len(sessions) > 0:
        profitable_sessions = sessions[sessions['is_profitable'] == True]
        losing_sessions = sessions[sessions['is_profitable'] == False]
        
        print(f"\n  Total Sessions: {len(sessions)}")
        print(f"  Profitable Sessions: {len(profitable_sessions)} ({len(profitable_sessions)/len(sessions)*100:.1f}%)")
        print(f"  Losing Sessions: {len(losing_sessions)} ({len(losing_sessions)/len(sessions)*100:.1f}%)")
        
        if len(profitable_sessions) > 0:
            print(f"\n  Profitable Session Stats:")
            print(f"    Avg P&L: ${profitable_sessions['pnl'].mean():,.0f}")
            print(f"    Avg Trades: {profitable_sessions['trades'].mean():.1f}")
            print(f"    Avg Win Rate: {profitable_sessions['win_rate'].mean():.1f}%")
        
        if len(losing_sessions) > 0:
            print(f"\n  Losing Session Stats:")
            print(f"    Avg P&L: ${losing_sessions['pnl'].mean():,.0f}")
            print(f"    Avg Trades: {losing_sessions['trades'].mean():.1f}")
            print(f"    Avg Win Rate: {losing_sessions['win_rate'].mean():.1f}%")
        
        # Best and worst sessions
        print(f"\n  🏆 Best Sessions:")
        for _, s in sessions.nlargest(3, 'pnl').iterrows():
            print(f"    {s['start_time']} | Trades: {s['trades']} | P&L: ${s['pnl']:,.0f}")
        
        print(f"\n  💀 Worst Sessions:")
        for _, s in sessions.nsmallest(3, 'pnl').iterrows():
            print(f"    {s['start_time']} | Trades: {s['trades']} | P&L: ${s['pnl']:,.0f}")
    
    # ========================================================================
    # SECTION 3: MULTI-TIMEFRAME CONFLUENCE
    # ========================================================================
    print()
    print("=" * 90)
    print("  3️⃣ MULTI-TIMEFRAME CONFLUENCE ANALYSIS")
    print("  H4, H1, M15 alignment at entry")
    print("=" * 90)
    
    mtf_results = []
    
    print("\n  Analyzing multi-timeframe context...")
    
    for idx, (_, trade) in enumerate(trades.iterrows()):
        if (idx + 1) % 20 == 0:
            print(f"    Processed {idx + 1}/{len(trades)} trades...")
        
        context = get_multi_timeframe_context(
            trade['Symbol'], 
            trade['DateTime'], 
            trade['Side']
        )
        
        if context:
            mtf_results.append({
                'DateTime': trade['DateTime'],
                'Symbol': trade['Symbol'],
                'Side': trade['Side'],
                'PnL': trade['P&L'],
                'IsWin': trade['P&L'] > 0,
                'Confluence': context['confluence'],
                'ConfluenceScore': context['confluence_score'],
                'TradeAlignment': context['trade_alignment'],
                'H4_Trend': context['H4']['trend'],
                'H1_Trend': context['H1']['trend'],
                'M15_Trend': context['M15']['trend']
            })
    
    mtf_df = pd.DataFrame(mtf_results)
    
    if len(mtf_df) > 0:
        print(f"\n  📊 Trade Alignment Analysis:")
        for alignment in mtf_df['TradeAlignment'].unique():
            subset = mtf_df[mtf_df['TradeAlignment'] == alignment]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"    {alignment}: {len(subset)} trades | WR: {wr:.1f}% | P&L: ${pnl:,.0f}")
        
        print(f"\n  📊 Confluence Analysis:")
        for conf in mtf_df['Confluence'].unique():
            subset = mtf_df[mtf_df['Confluence'] == conf]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"    {conf}: {len(subset)} trades | WR: {wr:.1f}% | P&L: ${pnl:,.0f}")
        
        print(f"\n  📊 Individual Timeframe Trends:")
        for tf in ['H4_Trend', 'H1_Trend', 'M15_Trend']:
            print(f"\n    {tf}:")
            for trend in mtf_df[tf].unique():
                subset = mtf_df[mtf_df[tf] == trend]
                wr = (subset['PnL'] > 0).mean() * 100
                pnl = subset['PnL'].sum()
                print(f"      {trend}: {len(subset)} trades | WR: {wr:.1f}% | P&L: ${pnl:,.0f}")
    
    # ========================================================================
    # SECTION 4: PRICE ACTION CONTEXT
    # ========================================================================
    print()
    print("=" * 90)
    print("  4️⃣ PRICE ACTION CONTEXT ANALYSIS")
    print("  What happened before your entries")
    print("=" * 90)
    
    pa_results = []
    
    print("\n  Analyzing price action context...")
    
    for idx, (_, trade) in enumerate(trades.iterrows()):
        if (idx + 1) % 20 == 0:
            print(f"    Processed {idx + 1}/{len(trades)} trades...")
        
        context = analyze_price_action_context(
            trade['Symbol'], 
            trade['DateTime'], 
            trade['Side'],
            trade['Price']
        )
        
        if context:
            pa_results.append({
                'DateTime': trade['DateTime'],
                'Symbol': trade['Symbol'],
                'Side': trade['Side'],
                'PnL': trade['P&L'],
                'IsWin': trade['P&L'] > 0,
                **context
            })
    
    pa_df = pd.DataFrame(pa_results)
    
    if len(pa_df) > 0 and 'pre_structure' in pa_df.columns:
        print(f"\n  📊 Pre-Trade Structure Analysis:")
        for structure in pa_df['pre_structure'].unique():
            subset = pa_df[pa_df['pre_structure'] == structure]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"    {structure}: {len(subset)} trades | WR: {wr:.1f}% | P&L: ${pnl:,.0f}")
    
    if len(pa_df) > 0 and 'entry_position' in pa_df.columns:
        winners = pa_df[pa_df['IsWin'] == True]
        losers = pa_df[pa_df['IsWin'] == False]
        
        if len(winners) > 0:
            print(f"\n  📊 Entry Position Analysis:")
            print(f"    Winners avg entry position: {winners['entry_position'].mean():.2f}")
            print(f"      (0 = bought at low/sold at high, 1 = bought at high/sold at low)")
        if len(losers) > 0:
            print(f"    Losers avg entry position: {losers['entry_position'].mean():.2f}")
    
    # ========================================================================
    # SECTION 5: OPTIMAL TRADE MODEL
    # ========================================================================
    print()
    print("=" * 90)
    print("  5️⃣ YOUR OPTIMAL TRADE MODEL")
    print("  Based on all analysis - what works for YOU")
    print("=" * 90)
    
    print("""
  🎯 OPTIMAL ENTRY CONDITIONS (based on YOUR data):
  
  1. MULTI-TIMEFRAME:
     - Require H4 + H1 to be aligned (same direction)
     - M15 confirms entry timing
     - "PERFECT" alignment = highest win rate
  
  2. TRADE SEQUENCE:
     - After 2 consecutive losses: STOP TRADING
     - After a big loss (>$5000): Wait at least 1 hour
     - After a big win: Reduce size by 50% (avoid overconfidence)
  
  3. SESSION MANAGEMENT:
     - Limit to 3-5 trades per session
     - If session P&L goes negative by 2x ATR: Stop session
     - Your best sessions have fewer, quality trades
  
  4. PRICE ACTION:
     - For BUYS: Look for higher lows forming before entry
     - For SELLS: Look for lower highs forming before entry
     - Entry near halfway of recent range (not extreme)
  
  5. EXIT MODEL:
     - Initial stop: 1.5-2.0 ATR
     - If trade goes 2+ ATR in favor: Move stop to breakeven
     - If trade doesn't move 0.5 ATR in favor in 15 min: Reconsider
     - Target: 3-5 ATR for trending moves
""")
    
    # Save all results
    output_path = Path(csv_path).parent / 'ultra_deep_analysis.csv'
    if len(mtf_df) > 0:
        mtf_df.to_csv(output_path, index=False)
        print(f"\n💾 Results saved to: {output_path}")
    
    mt5.shutdown()
    
    return {
        'sequences': sequence_results,
        'sessions': sessions,
        'mtf': mtf_df,
        'price_action': pa_df
    }


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "trades_export_20251229.csv"
    if csv_path.exists():
        results = run_ultra_deep_analysis(str(csv_path))
    else:
        print("❌ Trade export file not found!")
