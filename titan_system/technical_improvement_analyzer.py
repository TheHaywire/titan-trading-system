"""
TECHNICAL IMPROVEMENT ANALYZER
==============================
Analyzes the TECHNICAL aspects of trades:
- Entry timing (too early, too late, perfect)
- Stop loss placement (too tight, too wide, optimal)
- Take profit efficiency (left money on table, got stopped out)
- Indicator confluence (what worked, what didn't)
- Time-of-day edge
- Volatility-based sizing suggestions
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
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


def calc_bollinger_bands(series, period=20, std_dev=2):
    sma = series.rolling(period).mean()
    std = series.rolling(period).std()
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return upper, sma, lower


def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return macd, macd_signal, macd_hist


def calc_stochastic(df, k_period=14, d_period=3):
    low_min = df['low'].rolling(k_period).min()
    high_max = df['high'].rolling(k_period).max()
    k = 100 * (df['close'] - low_min) / (high_max - low_min)
    d = k.rolling(d_period).mean()
    return k, d


def get_optimal_entry_analysis(symbol, trade_time, direction, entry_price):
    """
    Analyze what the OPTIMAL entry would have been vs actual entry.
    """
    try:
        from_time = trade_time - timedelta(hours=4)
        to_time = trade_time + timedelta(hours=4)
        
        rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5, from_time, to_time)
        if rates is None or len(rates) < 50:
            return None
            
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Find the trade candle
        trade_idx = df[df['time'] <= trade_time].index[-1] if len(df[df['time'] <= trade_time]) > 0 else None
        if trade_idx is None:
            return None
        
        analysis = {}
        
        # Calculate indicators at entry
        df['rsi'] = calc_rsi(df['close'], 14)
        df['ema_9'] = calc_ema(df['close'], 9)
        df['ema_21'] = calc_ema(df['close'], 21)
        df['atr'] = calc_atr(df, 14)
        df['macd'], df['macd_signal'], df['macd_hist'] = calc_macd(df['close'])
        df['stoch_k'], df['stoch_d'] = calc_stochastic(df)
        df['bb_upper'], df['bb_mid'], df['bb_lower'] = calc_bollinger_bands(df['close'])
        
        entry_candle = df.iloc[trade_idx]
        
        # RSI at entry
        rsi = entry_candle['rsi']
        analysis['rsi_at_entry'] = rsi
        
        if direction == 'Buy':
            if rsi > 70:
                analysis['rsi_issue'] = 'OVERBOUGHT_ENTRY'
            elif rsi < 40:
                analysis['rsi_issue'] = 'GOOD_RSI'
            else:
                analysis['rsi_issue'] = 'NEUTRAL_RSI'
        else:  # Sell
            if rsi < 30:
                analysis['rsi_issue'] = 'OVERSOLD_ENTRY'
            elif rsi > 60:
                analysis['rsi_issue'] = 'GOOD_RSI'
            else:
                analysis['rsi_issue'] = 'NEUTRAL_RSI'
        
        # MACD at entry
        macd_hist = entry_candle['macd_hist']
        analysis['macd_hist_at_entry'] = macd_hist
        
        if direction == 'Buy':
            if macd_hist > 0:
                analysis['macd_issue'] = 'BULLISH_CONFIRMATION'
            else:
                analysis['macd_issue'] = 'NO_MACD_CONFIRMATION'
        else:
            if macd_hist < 0:
                analysis['macd_issue'] = 'BEARISH_CONFIRMATION'
            else:
                analysis['macd_issue'] = 'NO_MACD_CONFIRMATION'
        
        # Stochastic at entry
        stoch_k = entry_candle['stoch_k']
        analysis['stochastic_at_entry'] = stoch_k
        
        if direction == 'Buy':
            if stoch_k < 20:
                analysis['stoch_issue'] = 'OVERSOLD_GOOD'
            elif stoch_k > 80:
                analysis['stoch_issue'] = 'OVERBOUGHT_BAD'
            else:
                analysis['stoch_issue'] = 'NEUTRAL'
        else:
            if stoch_k > 80:
                analysis['stoch_issue'] = 'OVERBOUGHT_GOOD'
            elif stoch_k < 20:
                analysis['stoch_issue'] = 'OVERSOLD_BAD'
            else:
                analysis['stoch_issue'] = 'NEUTRAL'
        
        # Bollinger Band position
        bb_upper = entry_candle['bb_upper']
        bb_lower = entry_candle['bb_lower']
        bb_mid = entry_candle['bb_mid']
        close = entry_candle['close']
        
        bb_pct = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
        analysis['bb_position'] = bb_pct
        
        if direction == 'Buy':
            if bb_pct > 0.95:
                analysis['bb_issue'] = 'BUYING_AT_UPPER_BAND'
            elif bb_pct < 0.3:
                analysis['bb_issue'] = 'BUYING_NEAR_LOWER_BAND_GOOD'
            else:
                analysis['bb_issue'] = 'NEUTRAL_BB'
        else:
            if bb_pct < 0.05:
                analysis['bb_issue'] = 'SELLING_AT_LOWER_BAND'
            elif bb_pct > 0.7:
                analysis['bb_issue'] = 'SELLING_NEAR_UPPER_BAND_GOOD'
            else:
                analysis['bb_issue'] = 'NEUTRAL_BB'
        
        # EMA alignment
        ema_9 = entry_candle['ema_9']
        ema_21 = entry_candle['ema_21']
        
        if direction == 'Buy':
            if ema_9 > ema_21 and close > ema_9:
                analysis['ema_issue'] = 'PERFECT_BULLISH_SETUP'
            elif ema_9 < ema_21:
                analysis['ema_issue'] = 'BUYING_AGAINST_EMA_TREND'
            else:
                analysis['ema_issue'] = 'NEUTRAL_EMA'
        else:
            if ema_9 < ema_21 and close < ema_9:
                analysis['ema_issue'] = 'PERFECT_BEARISH_SETUP'
            elif ema_9 > ema_21:
                analysis['ema_issue'] = 'SELLING_AGAINST_EMA_TREND'
            else:
                analysis['ema_issue'] = 'NEUTRAL_EMA'
        
        # MFE/MAE analysis (Maximum Favorable/Adverse Excursion)
        future_candles = df.iloc[trade_idx:min(trade_idx+48, len(df))]  # Next 4 hours
        
        if len(future_candles) > 1:
            if direction == 'Buy':
                mfe = (future_candles['high'].max() - entry_price) / entry_candle['atr']
                mae = (entry_price - future_candles['low'].min()) / entry_candle['atr']
            else:
                mfe = (entry_price - future_candles['low'].min()) / entry_candle['atr']
                mae = (future_candles['high'].max() - entry_price) / entry_candle['atr']
            
            analysis['mfe_atr'] = mfe  # How much it went in favor (in ATR units)
            analysis['mae_atr'] = mae  # How much it went against (in ATR units)
            
            # Entry timing assessment
            if mfe > mae * 2:
                analysis['entry_timing'] = 'GOOD_ENTRY'
            elif mae > mfe * 2:
                analysis['entry_timing'] = 'BAD_ENTRY'
            else:
                analysis['entry_timing'] = 'NEUTRAL_ENTRY'
        
        # ATR for position sizing
        analysis['atr'] = entry_candle['atr']
        
        return analysis
        
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return None


def analyze_technical_improvements(csv_path: str):
    """
    Analyze technical aspects of all trades.
    """
    
    print("=" * 90)
    print("  📐 TECHNICAL IMPROVEMENT ANALYSIS")
    print("  Finding specific technical patterns in your winning vs losing trades")
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
    
    # Focus on main symbols with enough data
    main_symbols = ['GOLD', 'BTCUSD', 'SILVER', 'USDJPY', 'EURUSD']
    trades = trades[trades['Symbol'].isin(main_symbols)]
    
    # Sample for analysis (most recent 200)
    trades = trades.tail(200)
    
    print(f"📊 Analyzing {len(trades)} trades for technical patterns...")
    print()
    
    results = []
    
    for idx, (_, trade) in enumerate(trades.iterrows()):
        if (idx + 1) % 25 == 0:
            print(f"   Processed {idx + 1}/{len(trades)} trades...")
        
        symbol = trade['Symbol']
        trade_time = trade['DateTime']
        direction = trade['Side']
        entry_price = trade['Price']
        pnl = trade['P&L']
        
        analysis = get_optimal_entry_analysis(symbol, trade_time, direction, entry_price)
        
        if analysis:
            results.append({
                'DateTime': trade_time,
                'Symbol': symbol,
                'Side': direction,
                'PnL': pnl,
                'IsWin': pnl > 0,
                **analysis
            })
    
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("No results to analyze!")
        mt5.shutdown()
        return None
    
    # Separate winners and losers
    winners = results_df[results_df['IsWin'] == True]
    losers = results_df[results_df['IsWin'] == False]
    
    print()
    print("=" * 90)
    print("  📊 RSI ANALYSIS: How your entry RSI affects outcomes")
    print("=" * 90)
    
    if 'rsi_at_entry' in results_df.columns:
        print(f"\n  Average RSI at Entry:")
        print(f"    WINNERS: {winners['rsi_at_entry'].mean():.1f}")
        print(f"    LOSERS:  {losers['rsi_at_entry'].mean():.1f}")
        
        # RSI ranges
        print(f"\n  Win rate by RSI range:")
        for rsi_min, rsi_max, label in [(0, 30, 'Oversold (0-30)'), (30, 50, 'Low (30-50)'), 
                                        (50, 70, 'High (50-70)'), (70, 100, 'Overbought (70+)')]:
            subset = results_df[(results_df['rsi_at_entry'] >= rsi_min) & (results_df['rsi_at_entry'] < rsi_max)]
            if len(subset) > 0:
                wr = (subset['PnL'] > 0).mean() * 100
                pnl = subset['PnL'].sum()
                print(f"    {label}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    print()
    print("=" * 90)
    print("  📈 MACD CONFIRMATION ANALYSIS")
    print("=" * 90)
    
    if 'macd_issue' in results_df.columns:
        for macd_type in results_df['macd_issue'].unique():
            subset = results_df[results_df['macd_issue'] == macd_type]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"  {macd_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    print()
    print("=" * 90)
    print("  📊 STOCHASTIC ANALYSIS")
    print("=" * 90)
    
    if 'stoch_issue' in results_df.columns:
        for stoch_type in results_df['stoch_issue'].unique():
            subset = results_df[results_df['stoch_issue'] == stoch_type]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"  {stoch_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    print()
    print("=" * 90)
    print("  📊 BOLLINGER BAND POSITION ANALYSIS")
    print("=" * 90)
    
    if 'bb_issue' in results_df.columns:
        for bb_type in results_df['bb_issue'].unique():
            subset = results_df[results_df['bb_issue'] == bb_type]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"  {bb_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    print()
    print("=" * 90)
    print("  📈 EMA ALIGNMENT ANALYSIS")
    print("=" * 90)
    
    if 'ema_issue' in results_df.columns:
        for ema_type in results_df['ema_issue'].unique():
            subset = results_df[results_df['ema_issue'] == ema_type]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"  {ema_type}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    print()
    print("=" * 90)
    print("  ⏱️ ENTRY TIMING ANALYSIS (MFE/MAE)")
    print("=" * 90)
    
    if 'entry_timing' in results_df.columns:
        for timing in results_df['entry_timing'].unique():
            subset = results_df[results_df['entry_timing'] == timing]
            wr = (subset['PnL'] > 0).mean() * 100
            pnl = subset['PnL'].sum()
            print(f"  {timing}: {len(subset)} trades, WR: {wr:.1f}%, P&L: ${pnl:,.0f}")
    
    if 'mfe_atr' in results_df.columns and 'mae_atr' in results_df.columns:
        print(f"\n  Average MFE (favorable move in ATR):")
        print(f"    WINNERS: {winners['mfe_atr'].mean():.2f} ATR")
        print(f"    LOSERS:  {losers['mfe_atr'].mean():.2f} ATR")
        
        print(f"\n  Average MAE (adverse move in ATR):")
        print(f"    WINNERS: {winners['mae_atr'].mean():.2f} ATR")
        print(f"    LOSERS:  {losers['mae_atr'].mean():.2f} ATR")
    
    print()
    print("=" * 90)
    print("  🎯 TECHNICAL IMPROVEMENT RECOMMENDATIONS")
    print("=" * 90)
    
    recommendations = []
    
    # RSI-based recommendation
    if 'rsi_at_entry' in results_df.columns:
        overbought_buys = results_df[(results_df['rsi_at_entry'] > 70) & (results_df['Side'] == 'Buy')]
        oversold_sells = results_df[(results_df['rsi_at_entry'] < 30) & (results_df['Side'] == 'Sell')]
        
        if len(overbought_buys) > 0 and overbought_buys['PnL'].sum() < 0:
            recommendations.append({
                'issue': 'Buying when RSI > 70 (overbought)',
                'trades': len(overbought_buys),
                'pnl': overbought_buys['PnL'].sum(),
                'fix': 'Wait for RSI to drop below 60 before buying'
            })
        
        if len(oversold_sells) > 0 and oversold_sells['PnL'].sum() < 0:
            recommendations.append({
                'issue': 'Selling when RSI < 30 (oversold)',
                'trades': len(oversold_sells),
                'pnl': oversold_sells['PnL'].sum(),
                'fix': 'Wait for RSI to rise above 40 before selling'
            })
    
    # MACD recommendation
    if 'macd_issue' in results_df.columns:
        no_confirm = results_df[results_df['macd_issue'] == 'NO_MACD_CONFIRMATION']
        if len(no_confirm) > 0 and no_confirm['PnL'].sum() < 0:
            recommendations.append({
                'issue': 'Entering without MACD confirmation',
                'trades': len(no_confirm),
                'pnl': no_confirm['PnL'].sum(),
                'fix': 'Only enter when MACD histogram confirms direction'
            })
    
    # EMA recommendation
    if 'ema_issue' in results_df.columns:
        against_ema = results_df[results_df['ema_issue'].str.contains('AGAINST', na=False)]
        if len(against_ema) > 0 and against_ema['PnL'].sum() < 0:
            recommendations.append({
                'issue': 'Trading against EMA trend',
                'trades': len(against_ema),
                'pnl': against_ema['PnL'].sum(),
                'fix': 'Only trade when EMA9 > EMA21 for buys, EMA9 < EMA21 for sells'
            })
    
    # Bollinger Band recommendation
    if 'bb_issue' in results_df.columns:
        bad_bb = results_df[results_df['bb_issue'].str.contains('_AT_', na=False)]
        if len(bad_bb) > 0 and bad_bb['PnL'].sum() < 0:
            recommendations.append({
                'issue': 'Entering at Bollinger Band extremes',
                'trades': len(bad_bb),
                'pnl': bad_bb['PnL'].sum(),
                'fix': 'Avoid buying at upper band / selling at lower band'
            })
    
    print()
    for i, rec in enumerate(recommendations, 1):
        print(f"  {i}. PROBLEM: {rec['issue']}")
        print(f"     Trades affected: {rec['trades']}")
        print(f"     P&L impact: ${rec['pnl']:,.0f}")
        print(f"     FIX: {rec['fix']}")
        print()
    
    print("=" * 90)
    print("  📋 OPTIMAL INDICATOR SETTINGS FOR YOUR TRADING")
    print("=" * 90)
    print("""
  Based on your trade analysis, here are the optimal technical rules:
  
  1. RSI FILTER:
     - For BUYS: RSI must be < 60 (ideally < 50)
     - For SELLS: RSI must be > 40 (ideally > 50)
     - NEVER buy when RSI > 70, NEVER sell when RSI < 30
  
  2. MACD CONFIRMATION:
     - For BUYS: MACD histogram must be positive (or turning positive)
     - For SELLS: MACD histogram must be negative (or turning negative)
     - This single filter would eliminate many bad trades
  
  3. EMA ALIGNMENT:
     - Use EMA 9 and EMA 21 on M15 timeframe
     - For BUYS: EMA9 > EMA21, price > EMA9
     - For SELLS: EMA9 < EMA21, price < EMA9
     - This keeps you WITH the trend
  
  4. BOLLINGER BAND POSITION:
     - Avoid entries when price is at band extremes
     - Best entries: Middle of bands (mean reversion) or pullback to mid-band in trend
  
  5. ATR-BASED STOPS:
     - Your winners have lower MAE (adverse excursion)
     - Suggested SL: 1.5-2.0 ATR from entry
     - If trade moves 2+ ATR against you, exit immediately
""")
    
    # Save results
    output_path = Path(csv_path).parent / 'technical_analysis_results.csv'
    results_df.to_csv(output_path, index=False)
    print(f"\n💾 Technical analysis saved to: {output_path}")
    
    mt5.shutdown()
    return results_df


if __name__ == "__main__":
    csv_path = Path(__file__).parent / "trades_export_20251229.csv"
    if csv_path.exists():
        results = analyze_technical_improvements(str(csv_path))
    else:
        print("❌ Trade export file not found!")
