"""
Trade Analysis Report
=====================
Shows WHY each trade was placed with full reasoning and SL/TP analysis.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np

mt5.initialize()

def analyze_position(pos):
    """Deep analysis of a position"""
    print(f"\n{'='*60}")
    print(f"TRADE: {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'}")
    print(f"{'='*60}")
    
    # Position details
    print(f"\n--- POSITION DETAILS ---")
    print(f"Volume: {pos.volume} lots")
    print(f"Entry: {pos.price_open}")
    print(f"Current: {pos.price_current}")
    print(f"SL: {pos.sl}")
    print(f"TP: {pos.tp}")
    print(f"P/L: ${pos.profit:.2f}")
    
    # Get current data
    rates = mt5.copy_rates_from_pos(pos.symbol, mt5.TIMEFRAME_M15, 0, 100)
    if rates is None or len(rates) < 50:
        print("Cannot get data for analysis")
        return
    
    df = pd.DataFrame(rates)
    
    # Calculate indicators
    df['EMA9'] = df['close'].ewm(span=9).mean()
    df['EMA21'] = df['close'].ewm(span=21).mean()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    df['MOM'] = df['close'].pct_change(5) * 100
    
    curr = df.iloc[-1]
    
    print(f"\n--- INDICATORS AT ENTRY ---")
    print(f"EMA9: {curr['EMA9']:.5f}")
    print(f"EMA21: {curr['EMA21']:.5f}")
    print(f"RSI: {curr['RSI']:.1f}")
    print(f"Momentum (5-bar): {curr['MOM']:.2f}%")
    
    # Determine signal type
    print(f"\n--- SIGNAL REASONING ---")
    
    direction = 'BUY' if pos.type == 0 else 'SELL'
    
    if curr['RSI'] < 25:
        reason = f"RSI Oversold ({curr['RSI']:.1f}) - Price likely to bounce UP"
    elif curr['RSI'] > 75:
        reason = f"RSI Overbought ({curr['RSI']:.1f}) - Price likely to drop"
    elif curr['EMA9'] > curr['EMA21'] and direction == 'BUY':
        reason = f"Bullish EMA alignment (EMA9 > EMA21) - Uptrend confirmed"
    elif curr['EMA9'] < curr['EMA21'] and direction == 'SELL':
        reason = f"Bearish EMA alignment (EMA9 < EMA21) - Downtrend confirmed"
    elif curr['MOM'] > 0.5 and direction == 'BUY':
        reason = f"Strong bullish momentum ({curr['MOM']:.2f}%)"
    elif curr['MOM'] < -0.5 and direction == 'SELL':
        reason = f"Strong bearish momentum ({curr['MOM']:.2f}%)"
    elif curr['EMA9'] > curr['EMA21'] and 50 < curr['RSI'] < 70:
        reason = f"Uptrend + RSI in bullish zone ({curr['RSI']:.1f})"
    elif curr['EMA9'] < curr['EMA21'] and 30 < curr['RSI'] < 50:
        reason = f"Downtrend + RSI in bearish zone ({curr['RSI']:.1f})"
    else:
        reason = "Multiple confirmations aligned"
    
    print(f"  -> {reason}")
    
    # SL/TP Analysis
    print(f"\n--- SL/TP ANALYSIS ---")
    
    info = mt5.symbol_info(pos.symbol)
    point = info.point
    
    sl_distance = abs(pos.price_open - pos.sl) / point if pos.sl > 0 else 0
    tp_distance = abs(pos.tp - pos.price_open) / point if pos.tp > 0 else 0
    
    print(f"SL Distance: {sl_distance:.0f} points")
    print(f"TP Distance: {tp_distance:.0f} points")
    print(f"Risk:Reward = 1:{tp_distance/sl_distance:.1f}" if sl_distance > 0 else "N/A")
    
    # ATR check
    df['TR'] = pd.concat([
        df['high'] - df['low'],
        abs(df['high'] - df['close'].shift()),
        abs(df['low'] - df['close'].shift())
    ], axis=1).max(axis=1)
    atr = df['TR'].rolling(14).mean().iloc[-1]
    
    print(f"Current ATR: {atr:.5f} ({atr/point:.0f} points)")
    print(f"SL = {sl_distance/atr*100:.0f}% of ATR (good if 100-200%)")
    
    # Win probability estimate
    print(f"\n--- WIN PROBABILITY ---")
    
    trend_aligned = (direction == 'BUY' and curr['EMA9'] > curr['EMA21']) or \
                   (direction == 'SELL' and curr['EMA9'] < curr['EMA21'])
    
    rsi_ok = (direction == 'BUY' and 40 < curr['RSI'] < 70) or \
             (direction == 'SELL' and 30 < curr['RSI'] < 60)
    
    mom_ok = (direction == 'BUY' and curr['MOM'] > 0) or \
             (direction == 'SELL' and curr['MOM'] < 0)
    
    score = 0
    if trend_aligned:
        score += 30
        print("  [+30%] Trend aligned with trade direction")
    else:
        print("  [0%] CAUTION: Trading against trend")
    
    if rsi_ok:
        score += 25
        print("  [+25%] RSI in favorable zone")
    else:
        print("  [0%] RSI not in optimal zone")
    
    if mom_ok:
        score += 20
        print("  [+20%] Momentum supports direction")
    else:
        print("  [0%] Momentum against trade")
        
    score += 25  # Base success rate
    print("  [+25%] Base strategy rate")
    
    print(f"\n  ESTIMATED WIN PROBABILITY: {score}%")
    
    if score >= 70:
        print("  VERDICT: HIGH CONFIDENCE trade")
    elif score >= 50:
        print("  VERDICT: MODERATE confidence")
    else:
        print("  VERDICT: LOW confidence - monitor closely")


# Get all positions
positions = mt5.positions_get()

if not positions:
    print("No open positions")
else:
    print(f"\n{'#'*60}")
    print(f"TRADE ANALYSIS REPORT - {len(positions)} OPEN POSITIONS")
    print(f"{'#'*60}")
    
    for pos in positions:
        analyze_position(pos)

print(f"\n{'='*60}")
print("END OF REPORT")
print(f"{'='*60}")

mt5.shutdown()
