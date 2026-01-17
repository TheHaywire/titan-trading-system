"""
TITAN OS :: BREAKOUT BOT :: Breakout_GOLD_H4_gen_v1
Generated: 2026-01-15 16:34:18
Strategy ID: 55571543-9ebe-40ec-a415-9a59028b98e6
Magic Number: 999007
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import talib
from datetime import datetime

# --- CONFIG ---
SYMBOL = "GOLD"
TIMEFRAME = mt5.TIMEFRAME_H4 if hasattr(mt5, "TIMEFRAME_H4") else mt5.TIMEFRAME_H1
MAGIC = 999007
LOT_SIZE = 0.1
SL_ATR = 0.9925000776211605
TP_MULT = 4.253795364193607

# --- INDICATOR PARAMS ---
BB_period = 11\nBB_std = 1.863557677265831\nATR_period = 8\nATR_multiplier = 1.2334644577614648\n

def get_data(symbol, timeframe, n=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None: return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def calculate_vlatility(df):
    return talib.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]

def get_signal(df):
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    # Breakout Logic: BB or Keltner or High/Low
    upper, middle, lower = talib.BBANDS(close, timeperiod=20, nbdevup=2.0, nbdevdn=2.0)
    
    if close[-1] > upper[-1] and close[-2] <= upper[-2]:
        return 1 # BULLISH BREAKOUT
    if close[-1] < lower[-1] and close[-2] >= lower[-2]:
        return -1 # BEARISH BREAKOUT
        
    return 0

def execute_trade(direction, sl_pips, tp_pips):
    price = mt5.symbol_info_tick(SYMBOL).ask if direction == 1 else mt5.symbol_info_tick(SYMBOL).bid
    point = mt5.symbol_info(SYMBOL).point
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": LOT_SIZE,
        "type": mt5.ORDER_TYPE_BUY if direction == 1 else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": price - (sl_pips * point) if direction == 1 else price + (sl_pips * point),
        "tp": price + (tp_pips * point) if direction == 1 else price - (tp_pips * point),
        "magic": MAGIC,
        "comment": "Titan OS Breakout",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    return mt5.order_send(request)

def main():
    if not mt5.initialize(): return
    print(f"🚀 Breakout Bot {MAGIC} Active on {SYMBOL}")
    
    while True:
        try:
            df = get_data(SYMBOL, TIMEFRAME)
            if df is not None:
                # Check for existing positions
                pos = mt5.positions_get(symbol=SYMBOL, magic=MAGIC)
                if not pos:
                    signal = get_signal(df)
                    if signal != 0:
                        atr = calculate_vlatility(df)
                        sl_pips = (atr * SL_ATR) / mt5.symbol_info(SYMBOL).point
                        tp_pips = sl_pips * TP_MULT
                        res = execute_trade(signal, sl_pips, tp_pips)
                        print(f"Trade Result: {res.comment}")
            time.sleep(60)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
