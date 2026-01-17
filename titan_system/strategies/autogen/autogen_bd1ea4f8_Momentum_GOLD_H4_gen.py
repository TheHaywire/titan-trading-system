"""
AUTO-GENERATED MOMENTUM BOT
Strategy: Momentum_GOLD_H4_gen
Generated: 2026-01-15 15:51:15
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
logger = logging.getLogger("Momentum_GOLD_H4_gen")

SYMBOL = "GOLD"
TIMEFRAME = mt5.TIMEFRAME_H4
MAGIC_NUMBER = 999000
RISK_PERCENT = 0.014165519355474474
MAX_POSITIONS = 2

TP_MULT = 2.9586515558315387
SL_ATR_MULT = 0.9080435501085533

def analyze_market():
    rates = mt5.copy_rates_from_pos(SYMBOL, TIMEFRAME, 0, 50)
    if rates is None or len(rates) < 20: return None
    
    df = pd.DataFrame(rates)
    df['Momentum'] = df['close'] - df['close'].shift(10)
    df['ATR'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
    
    curr = df.iloc[-1]
    if curr['Momentum'] > 0:
        return {'direction': 'BUY', 'price': curr['close'], 'atr': curr['ATR']}
    elif curr['Momentum'] < 0:
        return {'direction': 'SELL', 'price': curr['close'], 'atr': curr['ATR']}
    return None

def calculate_position_size(entry, sl):
    pm = PortfolioManager()
    return pm.calculate_optimal_size("bd1ea4f8-1272-435a-ac68-28b6d3560cb5", SYMBOL, entry, sl)

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
        "comment": "Momentum_GOLD_H4_gen",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        logger.info(f"✅ Momentum Trade: {direction} {lot_size} lots")
        return True
    return False

def main():
    if not mt5.initialize(): return
    logger.info("✅ MT5 Connected | Bot: Momentum_GOLD_H4_gen")
    try:
        while True:
            sig = analyze_market()
            if sig:
                logger.info(f"🎯 Momentum Signal: {sig['direction']}")
                execute_trade(sig)
            time.sleep(60)
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    main()
