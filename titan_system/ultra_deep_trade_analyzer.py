"""
ULTRA-DEEP TRADE-BY-TRADE ANALYZER
===================================
Analyzes EACH trade with market context:
- What did indicators say at entry?
- Did you follow the edge or violate it?
- Was it trend-aligned or counter-trend gambling?
- Classification: Good setup, Bad entry, Revenge trade, Bot error, etc.

This will give you CLARITY on EXACTLY what went wrong on each trade.
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def calc_rsi(series, period=14):
    """Calculate RSI."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def calc_ema(series, period):
    """Calculate EMA."""
    return series.ewm(span=period, adjust=False).mean()


def calc_atr(df, period=14):
    """Calculate ATR."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(period).mean()


def calc_adx(df, period=14):
    """Calculate ADX for trend strength."""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff().clip(lower=0)
    minus_dm = (-low.diff()).clip(lower=0)
    
    tr = pd.concat([high - low, 
                    abs(high - close.shift(1)), 
                    abs(low - close.shift(1))], axis=1).max(axis=1)
    
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(period).mean()
    
    return adx, plus_di, minus_di


def get_market_context(symbol, trade_time, direction):
    """
    Get full market context at the moment of trade entry.
    Returns what indicators said, trend state, volatility regime.
    """
    try:
        # Get data around the trade time
        from_time = trade_time - timedelta(hours=48)
        to_time = trade_time + timedelta(minutes=5)
        
        # Get M15 data for analysis
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M15, from_time, to_time)
        if rates is None or len(rates) < 50:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Calculate indicators
        df['rsi'] = calc_rsi(df['close'], 14)
        df['ema_10'] = calc_ema(df['close'], 10)
        df['ema_20'] = calc_ema(df['close'], 20)
        df['ema_50'] = calc_ema(df['close'], 50)
        df['atr'] = calc_atr(df, 14)
        df['adx'], df['plus_di'], df['minus_di'] = calc_adx(df, 14)
        
        # Get the candle at/before trade time
        df_before = df[df['time'] <= trade_time]
        if len(df_before) == 0:
            return None
            
        last_candle = df_before.iloc[-1]
        
        # Determine market context
        context = {}
        
        # Price and spread info
        context['price_at_entry'] = float(last_candle['close'])
        context['atr'] = float(last_candle['atr']) if not np.isnan(last_candle['atr']) else 0
        
        # RSI Analysis
        rsi = float(last_candle['rsi']) if not np.isnan(last_candle['rsi']) else 50
        context['rsi'] = rsi
        if rsi > 70:
            context['rsi_signal'] = 'OVERBOUGHT'
        elif rsi < 30:
            context['rsi_signal'] = 'OVERSOLD'
        else:
            context['rsi_signal'] = 'NEUTRAL'
        
        # Trend Analysis (EMA alignment)
        ema_10 = float(last_candle['ema_10']) if not np.isnan(last_candle['ema_10']) else 0
        ema_20 = float(last_candle['ema_20']) if not np.isnan(last_candle['ema_20']) else 0
        ema_50 = float(last_candle['ema_50']) if not np.isnan(last_candle['ema_50']) else 0
        close = float(last_candle['close'])
        
        if ema_10 > ema_20 > ema_50 and close > ema_10:
            context['trend'] = 'STRONG_BULLISH'
        elif ema_10 < ema_20 < ema_50 and close < ema_10:
            context['trend'] = 'STRONG_BEARISH'
        elif close > ema_20:
            context['trend'] = 'BULLISH'
        elif close < ema_20:
            context['trend'] = 'BEARISH'
        else:
            context['trend'] = 'RANGING'
        
        # ADX - Trend Strength
        adx = float(last_candle['adx']) if not np.isnan(last_candle['adx']) else 0
        context['adx'] = adx
        if adx > 40:
            context['trend_strength'] = 'VERY_STRONG'
        elif adx > 25:
            context['trend_strength'] = 'STRONG'
        elif adx > 15:
            context['trend_strength'] = 'WEAK'
        else:
            context['trend_strength'] = 'NO_TREND'
        
        # Trade alignment check
        if direction == 'Buy':
            if context['trend'] in ['STRONG_BULLISH', 'BULLISH']:
                context['alignment'] = 'WITH_TREND'
            elif context['trend'] in ['STRONG_BEARISH', 'BEARISH']:
                context['alignment'] = 'COUNTER_TREND'
            else:
                context['alignment'] = 'NO_CLEAR_TREND'
        else:  # Sell
            if context['trend'] in ['STRONG_BEARISH', 'BEARISH']:
                context['alignment'] = 'WITH_TREND'
            elif context['trend'] in ['STRONG_BULLISH', 'BULLISH']:
                context['alignment'] = 'COUNTER_TREND'
            else:
                context['alignment'] = 'NO_CLEAR_TREND'
        
        # Volatility regime (ATR-based)
        if len(df) >= 100:
            avg_atr = df['atr'].iloc[-100:].mean()
            current_atr = context['atr']
            if current_atr > avg_atr * 1.5:
                context['volatility'] = 'HIGH'
            elif current_atr < avg_atr * 0.5:
                context['volatility'] = 'LOW'
            else:
                context['volatility'] = 'NORMAL'
        else:
            context['volatility'] = 'UNKNOWN'
        
        # Entry quality signals
        plus_di = float(last_candle['plus_di']) if not np.isnan(last_candle['plus_di']) else 0
        minus_di = float(last_candle['minus_di']) if not np.isnan(last_candle['minus_di']) else 0
        
        if direction == 'Buy':
            if plus_di > minus_di and adx > 20:
                context['momentum_aligned'] = True
            else:
                context['momentum_aligned'] = False
        else:
            if minus_di > plus_di and adx > 20:
                context['momentum_aligned'] = True
            else:
                context['momentum_aligned'] = False
        
        return context
        
    except Exception as e:
        print(f"Error getting context for {symbol}: {e}")
        return None


def classify_trade(trade_row, context, prev_trade=None, time_since_prev=None):
    """
    Classify the trade into categories:
    - EXCELLENT: Trend-aligned, good momentum, proper timing
    - ACCEPTABLE: Minor issues but reasonable setup
    - MARGINAL: Questionable setup, some edge violations
    - BAD: Clear edge violation (counter-trend, overbought/oversold)
    - REVENGE: Rapid entry after loss
    - CHASING: Entering after big move (high volatility)
    - GAMBLE: No clear edge, random entry
    """
    
    classification = {
        'class': 'UNKNOWN',
        'reasons': [],
        'score': 50  # 0-100 quality score
    }
    
    score = 50  # Start neutral
    
    if context is None:
        classification['class'] = 'NO_DATA'
        classification['reasons'].append('Could not fetch market data')
        return classification
    
    # Check for revenge trading (< 2 min after previous loss)
    if prev_trade is not None and time_since_prev is not None:
        if prev_trade < 0 and time_since_prev < 2:
            classification['class'] = 'REVENGE'
            classification['reasons'].append(f'Entry only {time_since_prev:.1f} min after ${prev_trade:.0f} loss')
            score -= 40
    
    # Check trend alignment
    if context['alignment'] == 'WITH_TREND':
        score += 20
        classification['reasons'].append(f"✅ {context['trend']} - Trade WITH trend")
    elif context['alignment'] == 'COUNTER_TREND':
        score -= 30
        classification['reasons'].append(f"❌ {context['trend']} - Trade AGAINST trend")
    else:
        classification['reasons'].append(f"⚠️ No clear trend")
    
    # Check momentum alignment
    if context['momentum_aligned']:
        score += 15
        classification['reasons'].append(f"✅ Momentum aligned (ADX: {context['adx']:.1f})")
    else:
        score -= 15
        classification['reasons'].append(f"❌ Momentum NOT aligned (ADX: {context['adx']:.1f})")
    
    # Check RSI extremes (buying overbought, selling oversold)
    direction = trade_row['Side']
    rsi = context['rsi']
    
    if direction == 'Buy' and rsi > 70:
        score -= 25
        classification['reasons'].append(f"❌ Buying OVERBOUGHT (RSI: {rsi:.1f})")
    elif direction == 'Sell' and rsi < 30:
        score -= 25
        classification['reasons'].append(f"❌ Selling OVERSOLD (RSI: {rsi:.1f})")
    elif (direction == 'Buy' and rsi < 40) or (direction == 'Sell' and rsi > 60):
        score += 10
        classification['reasons'].append(f"✅ Good RSI level ({rsi:.1f})")
    
    # Check volatility
    if context['volatility'] == 'HIGH':
        score -= 10
        classification['reasons'].append(f"⚠️ HIGH volatility entry (chase risk)")
    elif context['volatility'] == 'LOW':
        score -= 5
        classification['reasons'].append(f"⚠️ Low volatility (limited move potential)")
    
    # Trend strength
    if context['trend_strength'] == 'VERY_STRONG' and context['alignment'] == 'WITH_TREND':
        score += 15
        classification['reasons'].append(f"✅ Strong trend ({context['trend_strength']})")
    elif context['trend_strength'] == 'NO_TREND':
        score -= 10
        classification['reasons'].append(f"⚠️ No trend detected (ranging market)")
    
    # Final classification based on score
    classification['score'] = max(0, min(100, score))
    
    if classification['class'] == 'REVENGE':
        pass  # Already set
    elif score >= 75:
        classification['class'] = 'EXCELLENT'
    elif score >= 55:
        classification['class'] = 'ACCEPTABLE'
    elif score >= 40:
        classification['class'] = 'MARGINAL'
    elif score >= 25:
        classification['class'] = 'BAD'
    else:
        classification['class'] = 'GAMBLE'
    
    return classification


def analyze_all_trades_deep(csv_path: str, max_trades: int = None):
    """
    Deep analysis of every trade with full market context.
    """
    
    print("=" * 90)
    print("  🔬 ULTRA-DEEP TRADE-BY-TRADE ANALYSIS")
    print("  Getting market context for EVERY trade to understand what went wrong")
    print("=" * 90)
    print()
    
    # Initialize MT5
    if not mt5.initialize():
        print("❌ Failed to initialize MT5!")
        return None
    
    # Load trades
    df = pd.read_csv(csv_path)
    trades = df[df['Symbol'].notna() & (df['Symbol'] != '')].copy()
    trades = trades[trades['P&L'] != 0].copy()
    trades['DateTime'] = pd.to_datetime(trades['Date'] + ' ' + trades['Time'])
    trades = trades.sort_values('DateTime').reset_index(drop=True)
    
    if max_trades:
        trades = trades.tail(max_trades)
    
    print(f"📊 Analyzing {len(trades)} trades with full market context...")
    print()
    
    # Initialize results
    results = []
    prev_pnl = None
    prev_time = None
    
    # Progress tracking
    total = len(trades)
    classified_counts = {
        'EXCELLENT': 0, 'ACCEPTABLE': 0, 'MARGINAL': 0, 
        'BAD': 0, 'REVENGE': 0, 'GAMBLE': 0, 'NO_DATA': 0
    }
    
    print("⏳ Processing trades (this may take a few minutes)...")
    
    for idx, (_, trade) in enumerate(trades.iterrows()):
        if (idx + 1) % 50 == 0:
            print(f"   Processed {idx + 1}/{total} trades...")
        
        symbol = trade['Symbol']
        trade_time = trade['DateTime']
        direction = trade['Side']
        pnl = trade['P&L']
        volume = trade['Quantity']
        
        # Calculate time since previous trade
        time_since_prev = None
        if prev_time is not None:
            time_since_prev = (trade_time - prev_time).total_seconds() / 60
        
        # Get market context
        context = get_market_context(symbol, trade_time, direction)
        
        # Classify the trade
        classification = classify_trade(trade, context, prev_pnl, time_since_prev)
        
        # Store result
        result = {
            'DateTime': trade_time,
            'Symbol': symbol,
            'Side': direction,
            'Volume': volume,
            'P&L': pnl,
            'Class': classification['class'],
            'Score': classification['score'],
            'Reasons': ' | '.join(classification['reasons']),
            'RSI': context['rsi'] if context else None,
            'Trend': context['trend'] if context else None,
            'ADX': context['adx'] if context else None,
            'Alignment': context['alignment'] if context else None,
            'Volatility': context['volatility'] if context else None,
            'TimeSincePrev': time_since_prev
        }
        results.append(result)
        
        # Update counters
        if classification['class'] in classified_counts:
            classified_counts[classification['class']] += 1
        
        # Track for next iteration
        prev_pnl = pnl
        prev_time = trade_time
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Analysis summary
    print()
    print("=" * 90)
    print("  📊 TRADE CLASSIFICATION SUMMARY")
    print("=" * 90)
    
    for cls, count in sorted(classified_counts.items(), key=lambda x: x[1], reverse=True):
        pct = (count / total) * 100 if total > 0 else 0
        cls_trades = results_df[results_df['Class'] == cls]
        cls_pnl = cls_trades['P&L'].sum()
        cls_wr = (cls_trades['P&L'] > 0).mean() * 100 if len(cls_trades) > 0 else 0
        
        emoji = {
            'EXCELLENT': '🌟', 'ACCEPTABLE': '✅', 'MARGINAL': '⚠️',
            'BAD': '❌', 'REVENGE': '🔥', 'GAMBLE': '🎲', 'NO_DATA': '❓'
        }.get(cls, '•')
        
        print(f"  {emoji} {cls:12} | Count: {count:>4} ({pct:>5.1f}%) | P&L: ${cls_pnl:>12,.2f} | WR: {cls_wr:>5.1f}%")
    
    # Deep dive into problematic trades
    print()
    print("=" * 90)
    print("  🔴 WORST CLASSIFIED TRADES (Your Biggest Mistakes)")
    print("=" * 90)
    
    bad_trades = results_df[(results_df['Class'].isin(['BAD', 'REVENGE', 'GAMBLE'])) & (results_df['P&L'] < 0)]
    bad_trades = bad_trades.nlargest(20, 'P&L', keep='first').iloc[::-1]  # Biggest negative P&L
    
    print(f"\n  Top 20 Bad Trades (with edge violations):\n")
    for _, t in bad_trades.iterrows():
        print(f"  {t['DateTime']} | {t['Symbol']:10} | {t['Side']:4} | Vol: {t['Volume']:>6.2f} | P&L: ${t['P&L']:>12,.2f}")
        print(f"     └─ Class: {t['Class']} | Score: {t['Score']} | {t['Reasons']}")
        print()
    
    # Counter-trend analysis
    print("=" * 90)
    print("  📈 COUNTER-TREND TRADE ANALYSIS")
    print("=" * 90)
    
    ct_trades = results_df[results_df['Alignment'] == 'COUNTER_TREND']
    if len(ct_trades) > 0:
        ct_pnl = ct_trades['P&L'].sum()
        ct_wr = (ct_trades['P&L'] > 0).mean() * 100
        print(f"\n  Counter-Trend Trades: {len(ct_trades)}")
        print(f"  Net P&L: ${ct_pnl:,.2f}")
        print(f"  Win Rate: {ct_wr:.1f}%")
        
        if ct_pnl < 0:
            print(f"\n  🚨 Counter-trend trading is costing you ${abs(ct_pnl):,.2f}!")
            print("     RULE: Only trade WITH the trend!")
    
    # Revenge trading deep dive
    print()
    print("=" * 90)
    print("  🔥 REVENGE TRADING DEEP DIVE")
    print("=" * 90)
    
    revenge_trades = results_df[results_df['Class'] == 'REVENGE']
    if len(revenge_trades) > 0:
        r_pnl = revenge_trades['P&L'].sum()
        r_wr = (revenge_trades['P&L'] > 0).mean() * 100
        avg_time = revenge_trades['TimeSincePrev'].mean()
        print(f"\n  Revenge Trades: {len(revenge_trades)}")
        print(f"  Net P&L: ${r_pnl:,.2f}")
        print(f"  Win Rate: {r_wr:.1f}%")
        print(f"  Avg time after loss: {avg_time:.1f} minutes")
        
        print(f"\n  Worst Revenge Trades:")
        for _, t in revenge_trades.nsmallest(5, 'P&L').iterrows():
            print(f"    {t['DateTime']} | {t['Symbol']} | P&L: ${t['P&L']:,.2f} | {t['TimeSincePrev']:.1f} min after loss")
    
    # RSI extremes
    print()
    print("=" * 90)
    print("  📉 OVERBOUGHT/OVERSOLD ENTRY ANALYSIS")
    print("=" * 90)
    
    buy_overbought = results_df[(results_df['Side'] == 'Buy') & (results_df['RSI'] > 70)]
    sell_oversold = results_df[(results_df['Side'] == 'Sell') & (results_df['RSI'] < 30)]
    
    if len(buy_overbought) > 0:
        ob_pnl = buy_overbought['P&L'].sum()
        print(f"\n  Buying when OVERBOUGHT (RSI > 70): {len(buy_overbought)} trades")
        print(f"  Net P&L: ${ob_pnl:,.2f}")
        
    if len(sell_oversold) > 0:
        os_pnl = sell_oversold['P&L'].sum()
        print(f"\n  Selling when OVERSOLD (RSI < 30): {len(sell_oversold)} trades")
        print(f"  Net P&L: ${os_pnl:,.2f}")
    
    # Excellent trades analysis
    print()
    print("=" * 90)
    print("  🌟 YOUR EXCELLENT TRADES (What You Did RIGHT)")
    print("=" * 90)
    
    excellent = results_df[results_df['Class'] == 'EXCELLENT']
    if len(excellent) > 0:
        exc_pnl = excellent['P&L'].sum()
        exc_wr = (excellent['P&L'] > 0).mean() * 100
        print(f"\n  Excellent Trades: {len(excellent)}")
        print(f"  Net P&L: ${exc_pnl:,.2f}")
        print(f"  Win Rate: {exc_wr:.1f}%")
        
        print(f"\n  Best Excellent Trades:")
        for _, t in excellent.nlargest(5, 'P&L').iterrows():
            print(f"    {t['DateTime']} | {t['Symbol']} | P&L: ${t['P&L']:,.2f}")
            print(f"       └─ {t['Reasons']}")
    
    # Symbol-specific deep dive
    print()
    print("=" * 90)
    print("  📊 SYMBOL-SPECIFIC EDGE ANALYSIS")
    print("=" * 90)
    
    for symbol in ['GOLD', 'BTCUSD', 'SILVER', 'USDJPY']:
        sym_trades = results_df[results_df['Symbol'] == symbol]
        if len(sym_trades) > 0:
            print(f"\n  {symbol}:")
            for cls in ['EXCELLENT', 'ACCEPTABLE', 'BAD', 'REVENGE']:
                cls_trades = sym_trades[sym_trades['Class'] == cls]
                if len(cls_trades) > 0:
                    cls_pnl = cls_trades['P&L'].sum()
                    print(f"    {cls}: {len(cls_trades)} trades, P&L: ${cls_pnl:,.2f}")
    
    # Save detailed results
    output_path = Path(csv_path).parent / 'deep_trade_analysis.csv'
    results_df.to_csv(output_path, index=False)
    print(f"\n💾 Detailed results saved to: {output_path}")
    
    # Final verdict
    print()
    print("=" * 90)
    print("  🎯 FINAL VERDICT: YOUR IMPROVEMENT AREAS")
    print("=" * 90)
    
    total_bad_pnl = results_df[results_df['Class'].isin(['BAD', 'REVENGE', 'GAMBLE'])]['P&L'].sum()
    total_good_pnl = results_df[results_df['Class'].isin(['EXCELLENT', 'ACCEPTABLE'])]['P&L'].sum()
    
    print(f"\n  💚 P&L from GOOD trades (Excellent + Acceptable): ${total_good_pnl:,.2f}")
    print(f"  🔴 P&L from BAD trades (Bad + Revenge + Gamble):   ${total_bad_pnl:,.2f}")
    print(f"  📊 Edge Quality Ratio: {(total_good_pnl / abs(total_bad_pnl)):.2f}x" if total_bad_pnl != 0 else "")
    
    print("\n  🎓 KEY LESSONS FROM YOUR DATA:")
    
    # Generate specific lessons
    lessons = []
    
    if len(revenge_trades) > 0 and revenge_trades['P&L'].sum() < -10000:
        lessons.append("1. STOP trading immediately after a loss - wait at least 5 minutes")
    
    if len(ct_trades) > 0 and ct_trades['P&L'].sum() < -10000:
        lessons.append("2. ONLY trade WITH the trend - counter-trend = gambling")
    
    if len(buy_overbought) > 0 and buy_overbought['P&L'].sum() < -5000:
        lessons.append("3. NEVER buy when RSI > 70 - wait for pullback")
    
    if len(sell_oversold) > 0 and sell_oversold['P&L'].sum() < -5000:
        lessons.append("4. NEVER sell when RSI < 30 - wait for bounce")
    
    bad_high_vol = results_df[(results_df['Class'].isin(['BAD', 'GAMBLE'])) & (results_df['Volume'] > 10)]
    if len(bad_high_vol) > 0 and bad_high_vol['P&L'].sum() < -20000:
        lessons.append("5. REDUCE size when setup quality is low")
    
    for lesson in lessons:
        print(f"  ✅ {lesson}")
    
    print()
    print("=" * 90)
    print("  Analysis Complete! Review deep_trade_analysis.csv for full details.")
    print("=" * 90)
    
    mt5.shutdown()
    return results_df


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "trades_export_20251229.csv"
    if csv_path.exists():
        results = analyze_all_trades_deep(str(csv_path), max_trades=500)  # Last 500 trades
    else:
        print("❌ Trade export file not found!")
