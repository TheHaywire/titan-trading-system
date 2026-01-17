import sys
import os
import json
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_trend_alignment(symbol):
    """Calculates trend alignment across major timeframes"""
    tfs = {
        '1D': mt5.TIMEFRAME_D1,
        '4H': mt5.TIMEFRAME_H4,
        '1H': mt5.TIMEFRAME_H1
    }
    alignment = {}
    for tf_name, tf in tfs.items():
        rates = mt5.copy_rates_from_pos(symbol, tf, 0, 50)
        if rates is None: continue
        df = pd.DataFrame(rates)
        sma50 = df['close'].rolling(50).mean().iloc[-1]
        close = df['close'].iloc[-1]
        alignment[tf_name] = "BULLISH" if close > sma50 else "BEARISH"
    return alignment

def get_rsi(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
    if rates is None: return 50
    df = pd.DataFrame(rates)
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]

def coach_trades():
    if not mt5.initialize():
        print("MT5 Initialization failed")
        return

    positions = mt5.positions_get()
    if not positions:
        print("No active positions found.")
        mt5.shutdown()
        return

    print("="*70)
    print(f"🏛️ TITAN INSTITUTIONAL TRADE COACH | {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)

    for pos in positions:
        # We focus on Manual Trades (Magic 0) or specific bot magics if needed
        is_manual = (pos.magic == 0)
        tag = "[MANUAL]" if is_manual else f"[BOT:{pos.magic}]"
        
        print(f"\n{tag} {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} | Ticket: {pos.ticket}")
        print(f"Profit: ${pos.profit:,.2f} | Volume: {pos.volume}")

        # 1. Trend Alignment
        alignment = get_trend_alignment(pos.symbol)
        alignment_str = " | ".join([f"{k}: {v}" for k,v in alignment.items()])
        print(f"Trend Alignment: {alignment_str}")

        # 2. RSI Check
        rsi = get_rsi(pos.symbol)
        print(f"1H RSI: {rsi:.1f}")

        # 3. Grading Logic
        grade = "B" # Default
        learning_point = ""
        
        direction = "BULLISH" if pos.type == 0 else "BEARISH"
        matches_1d = (direction == alignment.get('1D'))
        matches_4h = (direction == alignment.get('4H'))
        
        if matches_1d and matches_4h:
            grade = "A"
            learning_point = "Excellent! You are trading with the primary institutional flow. High probability."
        elif not matches_1d and not matches_4h:
            grade = "D"
            learning_point = "Trading against the main flow. This is high risk 'Mean Reversion'. Is there a liquidity reason?"
        elif rsi > 80 and direction == "BULLISH":
            grade = "C"
            learning_point = "Buying the peak. 1H RSI is extreme. Watch for a 'Liquidity Flush' pullback."
        elif rsi < 20 and direction == "BEARISH":
            grade = "C"
            learning_point = "Selling the bottom. 1H RSI is extreme. Exhaustion likely."
        
        # SL/TP check
        if pos.sl == 0:
            grade = "F"
            learning_point = "CRITICAL: No Stop Loss. You are exposed to infinite 'Black Swan' risk. Fix immediately."

        print(f"--- GRADE: {grade} ---")
        print(f"💡 LEARNING POINT: {learning_point}")
        print("-" * 50)

    mt5.shutdown()

if __name__ == "__main__":
    coach_trades()
