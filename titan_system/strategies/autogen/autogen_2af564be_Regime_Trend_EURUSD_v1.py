"""
AUTO-GENERATED TREND FOLLOWING BOT
Generated: 2026-01-15 16:34:18
Strategy: Regime_Trend_EURUSD_v1
"""

import MetaTrader5 as mt5
import pandas as pd
import talib
import time
import logging
import sys, os

# Allow import from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from titan_system.factory.portfolio.portfolio_manager import PortfolioManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s [BOT] %(message)s')
logger = logging.getLogger("Regime_Trend_EURUSD_v1")

SYMBOL = "SILVER"
TIMEFRAME = mt5.TIMEFRAME_M5
MAGIC_NUMBER = 999004
RISK_PERCENT = 0.01
MAX_POSITIONS = 1

EMA_FAST = 17
EMA_SLOW = 98
TP_MULT = 9.490732371378138
SL_ATR_MULT = 6.445483795077223

def analyze_market():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 100)
    if rates is None: return None
    
    df = pd.DataFrame(rates)
    close = df['close'].values
    high = df['high'].values
    low = df['low'].values
    
    df['EMA_fast'] = talib.EMA(close, timeperiod=EMA_FAST)
    df['EMA_slow'] = talib.EMA(close, timeperiod=EMA_SLOW)
    df['ATR'] = talib.ATR(high, low, close, timeperiod=14)
    
    curr = df.iloc[-1]
    prev = df.iloc[-2]
    
    if prev['EMA_fast'] <= prev['EMA_slow'] and curr['EMA_fast'] > curr['EMA_slow']:
        return {'direction': 'BUY', 'score': 85, 'price': curr['close'], 'atr': curr['ATR']}
    elif prev['EMA_fast'] >= prev['EMA_slow'] and curr['EMA_fast'] < curr['EMA_slow']:
        return {'direction': 'SELL', 'score': 85, 'price': curr['close'], 'atr': curr['ATR']}
    
    return None

def calculate_position_size(entry, sl):
    pm = PortfolioManager()
    return pm.calculate_optimal_size("2af564be-f61c-4d3b-974a-371485bc18ab", SYMBOL, entry, sl)

def execute_trade(signal):
    positions = mt5.positions_get(symbol=SYMBOL, magic=MAGIC_NUMBER)
    if positions and len(positions) >= MAX_POSITIONS: return False
    
    direction = signal['direction']
    price = signal['price']
    atr = signal['atr']
    
    if direction == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        sl = price - (atr * SL_ATR_MULT)
        tp = price + (atr * SL_ATR_MULT * TP_MULT)
    else:
        order_type = mt5.ORDER_TYPE_SELL
        sl = price + (atr * SL_ATR_MULT)
        tp = price - (atr * SL_ATR_MULT * TP_MULT)
    
    lot_size = calculate_position_size(price, sl)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": SYMBOL,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "magic": MAGIC_NUMBER,
        "comment": "Regime_Trend_EURUSD_",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info(f"✅ Trade executed: {direction} {lot_size} lots @ {price:.5f}")
        return True
    return False

def main():
    if not mt5.initialize(): return
    logger.info("✅ MT5 connected | Bot: Regime_Trend_EURUSD_v1")
    try:
        while True:
            signal = analyze_market()
            if signal:
                logger.info(f"🎯 Signal: {signal['direction']}")
                execute_trade(signal)
            time.sleep(60)
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
