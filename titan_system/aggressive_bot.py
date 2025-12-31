"""
AGGRESSIVE TRADING BOT
======================
Trades on EVERY opportunity - RSI, EMA, Momentum

NO WAITING - TRADES NOW!
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger("AggressiveBot")


class AggressiveBot:
    """
    Trades aggressively on multiple indicators.
    Places trades when ANY condition is met.
    Uses dynamic position sizing based on risk.
    """
    
    UNIVERSE = [
        "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
        "GOLD", "BTCUSD", "US500", "USTEC"
    ]
    
    def __init__(self):
        self.risk_percent = 1.0  # Risk 1% per trade
        self.max_positions = 10
        self.scan_interval = 60  # seconds
        
    def calculate_lot_size(self, symbol: str, sl_points: int) -> float:
        """
        Calculate position size based on:
        - Account equity
        - Risk percentage (1%)
        - Stop loss distance
        """
        account = mt5.account_info()
        equity = account.equity
        
        risk_amount = equity * (self.risk_percent / 100)
        
        info = mt5.symbol_info(symbol)
        tick = mt5.symbol_info_tick(symbol)
        
        if not info or not tick:
            return 0.01
        
        point = info.point
        tick_value = info.trade_tick_value
        
        if tick_value == 0:
            tick_value = 1.0  # Fallback
        
        # Lot size = Risk / (SL in points * tick value)
        lot = risk_amount / (sl_points * tick_value)
        
        # Apply limits
        lot = max(info.volume_min, lot)
        lot = min(info.volume_max, lot)
        lot = round(lot, 2)
        
        return lot
        
    def start(self):
        logger.info("="*50)
        logger.info("AGGRESSIVE TRADING BOT - ACTIVE")
        logger.info("="*50)
        
        if not mt5.initialize():
            logger.error("MT5 failed")
            return
        
        account = mt5.account_info()
        logger.info(f"Account: {account.login}")
        logger.info(f"Balance: ${account.balance:,.2f}")
        
        while True:
            try:
                self.scan_all()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(10)
        
        mt5.shutdown()
    
    def scan_all(self):
        """Scan all symbols and trade"""
        logger.info("-"*40)
        logger.info(f"SCAN: {datetime.now().strftime('%H:%M:%S')}")
        
        # Check current positions
        positions = mt5.positions_get()
        current_count = len(positions) if positions else 0
        
        if current_count >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return
        
        for symbol in self.UNIVERSE:
            if current_count >= self.max_positions:
                break
            
            signal = self.analyze(symbol)
            if signal:
                if self.execute(symbol, signal['direction'], signal['reason']):
                    current_count += 1
    
    def analyze(self, symbol: str) -> dict:
        """
        AGGRESSIVE analysis - trade on ANY of these:
        1. RSI oversold/overbought
        2. EMA crossover
        3. Strong momentum
        4. Price at support/resistance
        """
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
        if rates is None or len(rates) < 50:
            return None
        
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
        prev = df.iloc[-2]
        
        # CHECK 1: RSI Extremes
        if curr['RSI'] < 25:
            return {'direction': 'BUY', 'reason': f'RSI Oversold: {curr["RSI"]:.1f}'}
        if curr['RSI'] > 75:
            return {'direction': 'SELL', 'reason': f'RSI Overbought: {curr["RSI"]:.1f}'}
        
        # CHECK 2: EMA Crossover
        if prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']:
            return {'direction': 'BUY', 'reason': 'EMA9 crossed above EMA21'}
        if prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']:
            return {'direction': 'SELL', 'reason': 'EMA9 crossed below EMA21'}
        
        # CHECK 3: Strong Momentum
        if curr['MOM'] > 0.5:
            return {'direction': 'BUY', 'reason': f'Strong upward momentum: {curr["MOM"]:.2f}%'}
        if curr['MOM'] < -0.5:
            return {'direction': 'SELL', 'reason': f'Strong downward momentum: {curr["MOM"]:.2f}%'}
        
        # CHECK 4: Trend continuation
        if curr['EMA9'] > curr['EMA21'] and curr['RSI'] > 50 and curr['RSI'] < 70:
            return {'direction': 'BUY', 'reason': 'Uptrend + RSI supportive'}
        if curr['EMA9'] < curr['EMA21'] and curr['RSI'] < 50 and curr['RSI'] > 30:
            return {'direction': 'SELL', 'reason': 'Downtrend + RSI supportive'}
        
        return None
    
    def execute(self, symbol: str, direction: str, reason: str) -> bool:
        """Execute trade with dynamic position sizing"""
        logger.info(f"SIGNAL: {symbol} {direction} - {reason}")
        
        info = mt5.symbol_info(symbol)
        if not info:
            return False
        
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            return False
        
        point = info.point
        
        # Symbol-specific stop levels
        if "BTC" in symbol or "ETH" in symbol:
            sl_points = 50000  # Crypto needs wider stops
            tp_points = 100000
        elif "XAU" in symbol or "GOLD" in symbol:
            sl_points = 5000  # Gold
            tp_points = 10000
        elif "US5" in symbol or "US3" in symbol or "USTEC" in symbol:
            sl_points = 5000  # Indices
            tp_points = 10000
        else:
            sl_points = 500  # Forex
            tp_points = 1000
        
        if direction == 'BUY':
            price = tick.ask
            sl = price - sl_points * point
            tp = price + tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_points * point
            tp = price - tp_points * point
            order_type = mt5.ORDER_TYPE_SELL
        # Calculate dynamic lot size based on risk
        lot = self.calculate_lot_size(symbol, sl_points)
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 999999,
            "comment": f"AGG: {reason[:20]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"EXECUTED: {symbol} {direction} @ {result.price}")
            return True
        else:
            logger.warning(f"FAILED: {result.comment}")
            return False


if __name__ == "__main__":
    bot = AggressiveBot()
    bot.start()
