"""
AUTO-GENERATED SCALPING BOT
Strategy: Expert_Scalping_GBPUSD_M5_112
Generated: 2026-01-15 15:51:15
"""

import MetaTrader5 as mt5
import pandas as pd
import talib
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Expert_Scalping_GBPUSD_M5_112")

SYMBOL = "GBPUSD"
TIMEFRAME = mt5.TIMEFRAME_M5
MAGIC_NUMBER = 999002
RISK_PERCENT = 0.008830616820715318

# Indicators
RSI_PERIOD = 7
TP_MULT = 4.065490604483652
SL_ATR = 2.6769410482058236

def analyze_market():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    if rates is None or len(rates) < 50: return None
    
    df = pd.DataFrame(rates)
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    df['RSI'] = talib.RSI(close, timeperiod=RSI_PERIOD)
    macd, macdsignal, macdhist = talib.MACD(close)
    df['MACD_hist'] = macdhist
    df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Scalp Logic: RSI extreme + Momentum shift
    if curr['RSI'] < 25 and curr['MACD_hist'] > prev['MACD_hist']:
        return {'direction': 'BUY', 'price': curr['close'], 'atr': curr['ATR']}
    elif curr['RSI'] > 75 and curr['MACD_hist'] < prev['MACD_hist']:
        return {'direction': 'SELL', 'price': curr['close'], 'atr': curr['ATR']}
    
    return None

def execute_trade(signal):
    # Safety: Check if already in position
    pos = mt5.positions_get(symbol=SYMBOL, magic=MAGIC_NUMBER)
    if pos: return # One at a time for scalper safety
    
    # Calculate SL/TP
    price = signal['price']
    atr = signal['atr']
    sl_dist = atr * SL_ATR
    
    if signal['direction'] == 'BUY':
        sl = price - sl_dist
        tp = price + (sl_dist * TP_MULT)
        order_type = mt5.ORDER_TYPE_BUY
    else:
        sl = price + sl_dist
        tp = price - (sl_dist * TP_MULT)
        order_type = mt5.ORDER_TYPE_SELL
        
    # Fixed risk sizing (No Martingale)
    acc = mt5.account_info()
    lot = (acc.equity * RISK_PERCENT) / (sl_dist * 100000) # Simple lot calc
    lot = max(0.01, round(lot, 2))
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": MAGIC_NUMBER,
        "comment": "ExpertScalp",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    mt5.order_send(request)

def main():
    if not mt5.initialize(): return
    while True:
        sig = analyze_market()
        if sig: execute_trade(sig)
        time.sleep(30) # Fast check for M5/M1

if __name__ == "__main__":
    main()
