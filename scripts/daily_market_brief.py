"""
Deep Market Analysis - Institutional Daily Brief
================================================
Comprehensive analysis of today's market using MT5 data:
- Multi-timeframe price action
- Volatility analysis (ATR, range %)
- Session performance (Asian/London/NY)
- Key technical levels
- Correlation analysis
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def calculate_atr(rates, period=14):
    """Calculate ATR from rates array."""
    df = pd.DataFrame(rates)
    tr1 = df['high'] - df['low']
    tr2 = abs(df['high'] - df['close'].shift(1))
    tr3 = abs(df['low'] - df['close'].shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def calculate_rsi(rates, period=14):
    """Calculate RSI."""
    df = pd.DataFrame(rates)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs.iloc[-1]))

def get_session_performance(symbol, session_name, start_hour, end_hour):
    """Analyze today's performance during a specific session."""
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None:
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    # Filter for today
    today = datetime.now().date()
    df_today = df[df['time'].dt.date == today]
    
    if df_today.empty:
        return None
    
    # Filter for session hours (UTC)
    session_df = df_today[(df_today['time'].dt.hour >= start_hour) & 
                          (df_today['time'].dt.hour < end_hour)]
    
    if session_df.empty:
        return None
    
    session_open = session_df.iloc[0]['open']
    session_high = session_df['high'].max()
    session_low = session_df['low'].min()
    session_close = session_df.iloc[-1]['close']
    
    change = session_close - session_open
    change_pct = (change / session_open) * 100
    
    return {
        'session': session_name,
        'open': session_open,
        'high': session_high,
        'low': session_low,
        'close': session_close,
        'change': change,
        'change_pct': change_pct,
        'range': session_high - session_low
    }

def find_support_resistance(rates, lookback=20):
    """Find key S/R levels from recent price action."""
    df = pd.DataFrame(rates[-lookback:])
    
    # Recent highs and lows
    recent_high = df['high'].max()
    recent_low = df['low'].min()
    
    # Yesterday's levels
    yesterday_high = rates[-2]['high']
    yesterday_low = rates[-2]['low']
    yesterday_close = rates[-2]['close']
    
    return {
        'resistance_1': recent_high,
        'resistance_2': yesterday_high,
        'support_1': recent_low,
        'support_2': yesterday_low,
        'pivot': (yesterday_high + yesterday_low + yesterday_close) / 3
    }

def main():
    if not mt5.initialize():
        print("MT5 not connected")
        return
    
    symbols = {
        'EURUSD': 'forex',
        'GBPUSD': 'forex', 
        'USDJPY': 'forex',
        'XAUUSD': 'commodity',
        'BTCUSD': 'crypto',
        'US30Cash': 'index',
        'US100Cash': 'index',
        'OILCash': 'commodity',
        'GBPJPY': 'forex',
        'AUDUSD': 'forex'
    }
    
    print("=" * 80)
    print("  INSTITUTIONAL DAILY MARKET BRIEF")
    print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Overall market analysis
    print("\n" + "=" * 80)
    print("  PART 1: PRICE ACTION SUMMARY")
    print("=" * 80)
    
    all_data = []
    
    for symbol, category in symbols.items():
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        
        # Get D1 data for context
        d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 30)
        if d1_rates is None:
            continue
        
        # Get H1 data for intraday
        h1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
        
        today = d1_rates[-1]
        yesterday = d1_rates[-2]
        
        current = tick.bid
        daily_change = current - yesterday['close']
        daily_change_pct = (daily_change / yesterday['close']) * 100
        
        # ATR analysis
        atr_14 = calculate_atr(d1_rates)
        today_range = today['high'] - today['low']
        range_vs_atr = (today_range / atr_14) * 100 if atr_14 > 0 else 0
        
        # RSI
        rsi = calculate_rsi(d1_rates)
        
        # Distance from today's high/low
        dist_from_high = ((today['high'] - current) / today['high']) * 100
        dist_from_low = ((current - today['low']) / today['low']) * 100
        
        # Weekly context
        week_open = d1_rates[-5]['open'] if len(d1_rates) >= 5 else d1_rates[0]['open']
        weekly_change = ((current - week_open) / week_open) * 100
        
        all_data.append({
            'symbol': symbol,
            'category': category,
            'current': current,
            'daily_change_pct': daily_change_pct,
            'weekly_change_pct': weekly_change,
            'atr_14': atr_14,
            'range_vs_atr': range_vs_atr,
            'rsi': rsi,
            'today_high': today['high'],
            'today_low': today['low']
        })
        
        # Print summary
        direction = "UP  " if daily_change_pct > 0 else "DOWN" if daily_change_pct < 0 else "FLAT"
        rsi_signal = "OVERBOUGHT" if rsi > 70 else "OVERSOLD" if rsi < 30 else "NEUTRAL"
        
        print(f"\n{symbol} ({category.upper()})")
        print(f"  Price: {current:.5f} | {direction} {daily_change_pct:+.2f}% today | {weekly_change:+.2f}% this week")
        print(f"  Range: {today['low']:.5f} - {today['high']:.5f}")
        print(f"  ATR(14): {atr_14:.5f} | Today's range = {range_vs_atr:.0f}% of ATR")
        print(f"  RSI(14): {rsi:.1f} ({rsi_signal})")
    
    # Session Analysis
    print("\n" + "=" * 80)
    print("  PART 2: SESSION ANALYSIS (Today)")
    print("=" * 80)
    
    sessions = [
        ('Asian', 0, 8),
        ('London', 8, 13),
        ('New York', 13, 21)
    ]
    
    for symbol in ['EURUSD', 'GBPUSD', 'XAUUSD', 'US30Cash']:
        print(f"\n{symbol}:")
        for session_name, start, end in sessions:
            perf = get_session_performance(symbol, session_name, start, end)
            if perf:
                direction = "UP  " if perf['change_pct'] > 0 else "DOWN" if perf['change_pct'] < 0 else "FLAT"
                print(f"  {session_name:10}: {direction} {perf['change_pct']:+.3f}% | Range: {perf['range']:.5f}")
    
    # Key Levels
    print("\n" + "=" * 80)
    print("  PART 3: KEY TECHNICAL LEVELS")
    print("=" * 80)
    
    for symbol in ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD']:
        d1_rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_D1, 0, 30)
        if d1_rates is None:
            continue
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue
        
        levels = find_support_resistance(d1_rates)
        current = tick.bid
        
        print(f"\n{symbol} (Current: {current:.5f})")
        print(f"  Resistance 1 (Recent High): {levels['resistance_1']:.5f}")
        print(f"  Resistance 2 (Yest High):   {levels['resistance_2']:.5f}")
        print(f"  Pivot Point:                {levels['pivot']:.5f}")
        print(f"  Support 1 (Yest Low):       {levels['support_2']:.5f}")
        print(f"  Support 2 (Recent Low):     {levels['support_1']:.5f}")
        
        # Distance to key levels
        dist_to_r1 = ((levels['resistance_1'] - current) / current) * 100
        dist_to_s1 = ((current - levels['support_2']) / current) * 100
        print(f"  -> Distance to R1: {dist_to_r1:+.2f}% | Distance to S1: {dist_to_s1:+.2f}%")
    
    # Volatility Ranking
    print("\n" + "=" * 80)
    print("  PART 4: VOLATILITY RANKING (Today)")
    print("=" * 80)
    
    vol_data = sorted(all_data, key=lambda x: abs(x['daily_change_pct']), reverse=True)
    
    print("\nMost Active (by % move):")
    for i, d in enumerate(vol_data[:5], 1):
        print(f"  {i}. {d['symbol']:12} {d['daily_change_pct']:+.2f}% | Range = {d['range_vs_atr']:.0f}% of ATR")
    
    # Correlation quick check
    print("\n" + "=" * 80)
    print("  PART 5: MARKET THEMES")
    print("=" * 80)
    
    # Dollar strength check
    eur = next((d for d in all_data if d['symbol'] == 'EURUSD'), None)
    gbp = next((d for d in all_data if d['symbol'] == 'GBPUSD'), None)
    jpy = next((d for d in all_data if d['symbol'] == 'USDJPY'), None)
    
    if eur and gbp and jpy:
        # If EURUSD and GBPUSD down, USDJPY up = Dollar strength
        dollar_score = 0
        if eur['daily_change_pct'] < 0: dollar_score += 1
        if gbp['daily_change_pct'] < 0: dollar_score += 1
        if jpy['daily_change_pct'] > 0: dollar_score += 1
        
        if dollar_score >= 2:
            print("\n  DOLLAR: STRONG today (most pairs moving against USD)")
        elif dollar_score <= 1:
            print("\n  DOLLAR: WEAK today (most pairs moving with USD)")
        else:
            print("\n  DOLLAR: MIXED signals")
    
    # Risk sentiment
    gold = next((d for d in all_data if d['symbol'] == 'XAUUSD'), None)
    btc = next((d for d in all_data if d['symbol'] == 'BTCUSD'), None)
    spx = next((d for d in all_data if d['symbol'] == 'US100Cash'), None)
    
    if gold and spx:
        if gold['daily_change_pct'] > 0 and spx['daily_change_pct'] < 0:
            print("  RISK: OFF (Gold up, Stocks down) - Flight to safety")
        elif gold['daily_change_pct'] < 0 and spx['daily_change_pct'] > 0:
            print("  RISK: ON (Stocks up, Gold down) - Risk appetite")
        else:
            print("  RISK: NEUTRAL (Mixed signals)")
    
    # Volatility regime
    low_vol_count = sum(1 for d in all_data if d['range_vs_atr'] < 80)
    if low_vol_count > len(all_data) / 2:
        print("  VOLATILITY: LOW (Holiday mode - thin liquidity)")
    else:
        print("  VOLATILITY: NORMAL")
    
    print("\n" + "=" * 80)
    print("  END OF DAILY BRIEF")
    print("=" * 80)
    
    mt5.shutdown()


if __name__ == "__main__":
    main()
