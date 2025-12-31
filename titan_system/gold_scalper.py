"""
GOLD SCALPER BOT
================
Built by reverse-engineering your successful trades.

Strategy:
- Timeframe: M5 (fast)
- Focus: GOLD only
- Size: 5-10 lots (conviction)
- Entry: RSI extremes + Momentum + Range position
- Exit: Quick 20-30 point TP or trail
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger("GoldScalper")


class GoldScalper:
    """
    GOLD-focused scalping bot.
    Derived from user's successful manual trades.
    """
    
    def __init__(self):
        self.symbol = "GOLD"
        self.lot_size = 5.0  # User uses 5-20 lots
        self.max_positions = 2  # Don't over-leverage
        self.scan_interval = 30  # Check every 30 seconds
        self.tp_points = 300  # 30 point TP ($30 per lot)
        self.sl_points = 500  # 50 point SL
        
    def start(self):
        logger.info("="*50)
        logger.info("GOLD SCALPER BOT - ACTIVE")
        logger.info("="*50)
        
        if not mt5.initialize():
            logger.error("MT5 failed")
            return
        
        account = mt5.account_info()
        logger.info(f"Account: {account.login}")
        logger.info(f"Equity: ${account.equity:,.2f}")
        logger.info(f"Lot Size: {self.lot_size} lots")
        
        # Select symbol
        if not mt5.symbol_select(self.symbol, True):
            logger.error(f"Cannot select {self.symbol}")
            return
        
        while True:
            try:
                self.scan_and_trade()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(10)
        
        mt5.shutdown()
    
    def scan_and_trade(self):
        """Scan GOLD for entry"""
        logger.info("-"*40)
        logger.info(f"SCAN: {datetime.now().strftime('%H:%M:%S')}")
        
        # Check current positions
        positions = mt5.positions_get(symbol=self.symbol)
        if positions and len(positions) >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return
        
        # Get M5 data
        rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M5, 0, 100)
        if rates is None:
            return
        
        df = pd.DataFrame(rates)
        signal = self.analyze(df)
        
        if signal:
            self.execute(signal)
    
    def analyze(self, df: pd.DataFrame) -> dict:
        """
        Your derived strategy:
        - SELL when RSI high + near top of range + bearish momentum
        - BUY when RSI low + near bottom of range + bullish momentum
        """
        # Calculate indicators
        df['EMA9'] = df['close'].ewm(span=9).mean()
        df['EMA21'] = df['close'].ewm(span=21).mean()
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['RSI'] = 100 - (100 / (1 + gain/loss))
        
        df['MOM'] = df['close'].pct_change(5) * 100
        
        # Range position
        df['HIGH_20'] = df['high'].rolling(20).max()
        df['LOW_20'] = df['low'].rolling(20).min()
        df['RANGE_POS'] = (df['close'] - df['LOW_20']) / (df['HIGH_20'] - df['LOW_20'])
        
        curr = df.iloc[-1]
        prev = df.iloc[-2]
        
        logger.info(f"Price: {curr['close']:.2f} | RSI: {curr['RSI']:.1f} | MOM: {curr['MOM']:.2f}% | Range: {curr['RANGE_POS']*100:.0f}%")
        
        # SELL SETUP: RSI high + top of range + bearish momentum
        if curr['RSI'] > 60 and curr['RANGE_POS'] > 0.7 and curr['MOM'] < -0.1:
            logger.info("SELL SIGNAL: RSI high + top of range + bearish momentum")
            return {
                'direction': 'SELL',
                'reason': f"RSI {curr['RSI']:.0f} + Range {curr['RANGE_POS']*100:.0f}% + Mom {curr['MOM']:.2f}%"
            }
        
        # BUY SETUP: RSI low + bottom of range + bullish momentum
        if curr['RSI'] < 40 and curr['RANGE_POS'] < 0.3 and curr['MOM'] > 0.1:
            logger.info("BUY SIGNAL: RSI low + bottom of range + bullish momentum")
            return {
                'direction': 'BUY',
                'reason': f"RSI {curr['RSI']:.0f} + Range {curr['RANGE_POS']*100:.0f}% + Mom {curr['MOM']:.2f}%"
            }
        
        # STRONG MOMENTUM ONLY
        if curr['MOM'] > 0.5 and curr['EMA9'] > curr['EMA21']:
            logger.info("BUY SIGNAL: Strong upward momentum")
            return {
                'direction': 'BUY',
                'reason': f"Strong momentum {curr['MOM']:.2f}% + bullish EMA"
            }
        
        if curr['MOM'] < -0.5 and curr['EMA9'] < curr['EMA21']:
            logger.info("SELL SIGNAL: Strong downward momentum")
            return {
                'direction': 'SELL',
                'reason': f"Strong momentum {curr['MOM']:.2f}% + bearish EMA"
            }
        
        return None
    
    def execute(self, signal: dict) -> bool:
        """Execute GOLD trade"""
        logger.info(f"\nEXECUTING: {signal['direction']}")
        logger.info(f"Reason: {signal['reason']}")
        logger.info(f"Size: {self.lot_size} lots")
        
        info = mt5.symbol_info(self.symbol)
        tick = mt5.symbol_info_tick(self.symbol)
        
        if not info or not tick:
            return False
        
        point = info.point
        
        if signal['direction'] == 'BUY':
            price = tick.ask
            sl = price - self.sl_points * point
            tp = price + self.tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + self.sl_points * point
            tp = price - self.tp_points * point
            order_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.lot_size,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 50,
            "magic": 888888,
            "comment": f"GS: {signal['reason'][:20]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"EXECUTED: {self.symbol} {signal['direction']} @ {result.price}")
            logger.info(f"SL: {sl:.2f} | TP: {tp:.2f}")
            return True
        else:
            logger.warning(f"FAILED: {result.comment}")
            return False


if __name__ == "__main__":
    bot = GoldScalper()
    bot.start()
