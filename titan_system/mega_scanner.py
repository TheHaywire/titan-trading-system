"""
MEGA SCANNER BOT
================
Scans ALL 1500+ MT5 symbols and trades the best opportunities.
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
logger = logging.getLogger("MegaScanner")


class MegaScanner:
    """
    Scans ALL available symbols and trades the best opportunities.
    """
    
    def __init__(self):
        self.risk_percent = 0.5  # 0.5% per trade (conservative with many symbols)
        self.max_positions = 15
        self.scan_interval = 120  # 2 minutes
        self.min_score = 80  # Only trade high-score signals
        self.symbols_per_scan = 200  # Scan 200 at a time
        
    def start(self):
        logger.info("="*60)
        logger.info("MEGA SCANNER BOT - ALL SYMBOLS")
        logger.info("="*60)
        
        if not mt5.initialize():
            logger.error("MT5 failed")
            return
        
        account = mt5.account_info()
        logger.info(f"Account: {account.login}")
        logger.info(f"Equity: ${account.equity:,.2f}")
        
        # Get all tradeable symbols
        all_symbols = mt5.symbols_get()
        self.symbols = [s.name for s in all_symbols if s.visible and s.trade_mode != 0]
        logger.info(f"Total tradeable symbols: {len(self.symbols)}")
        
        self.scan_offset = 0
        
        while True:
            try:
                self.scan_and_trade()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(30)
        
        mt5.shutdown()
    
    def scan_and_trade(self):
        """Scan batch of symbols and trade best opportunities"""
        logger.info("-"*50)
        logger.info(f"SCAN: {datetime.now().strftime('%H:%M:%S')}")
        
        # Check positions
        positions = mt5.positions_get()
        current_count = len(positions) if positions else 0
        
        if current_count >= self.max_positions:
            logger.info(f"Max positions ({self.max_positions}) reached")
            return
        
        # Get batch of symbols to scan
        batch_start = self.scan_offset
        batch_end = min(batch_start + self.symbols_per_scan, len(self.symbols))
        batch = self.symbols[batch_start:batch_end]
        
        logger.info(f"Scanning symbols {batch_start+1} to {batch_end} of {len(self.symbols)}")
        
        # Move offset for next scan
        self.scan_offset = batch_end if batch_end < len(self.symbols) else 0
        
        # Scan and collect opportunities
        opportunities = []
        
        for sym in batch:
            opp = self.analyze(sym)
            if opp and opp['score'] >= self.min_score:
                opportunities.append(opp)
        
        if not opportunities:
            logger.info("No high-score opportunities found")
            return
        
        # Sort by score
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        logger.info(f"Found {len(opportunities)} opportunities")
        
        # Trade top opportunities
        for opp in opportunities[:3]:  # Max 3 trades per scan
            if current_count >= self.max_positions:
                break
            
            # Check if already have position on this symbol
            sym_positions = mt5.positions_get(symbol=opp['symbol'])
            if sym_positions and len(sym_positions) > 0:
                continue
            
            if self.execute(opp):
                current_count += 1
    
    def analyze(self, symbol: str) -> dict:
        """Analyze single symbol for opportunity"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 50)
            if rates is None or len(rates) < 30:
                return None
            
            df = pd.DataFrame(rates)
            
            # Indicators
            df['EMA9'] = df['close'].ewm(span=9).mean()
            df['EMA21'] = df['close'].ewm(span=21).mean()
            
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            df['RSI'] = 100 - (100 / (1 + gain/loss))
            
            df['MOM'] = df['close'].pct_change(5) * 100
            
            curr = df.iloc[-1]
            prev = df.iloc[-2]
            
            # Check signals
            if curr['RSI'] < 20:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 95, 'reason': f"RSI Extreme Oversold ({curr['RSI']:.0f})"}
            if curr['RSI'] > 80:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 95, 'reason': f"RSI Extreme Overbought ({curr['RSI']:.0f})"}
            if curr['RSI'] < 25:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 90, 'reason': f"RSI Oversold ({curr['RSI']:.0f})"}
            if curr['RSI'] > 75:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 90, 'reason': f"RSI Overbought ({curr['RSI']:.0f})"}
            if prev['EMA9'] <= prev['EMA21'] and curr['EMA9'] > curr['EMA21']:
                return {'symbol': symbol, 'direction': 'BUY', 'score': 85, 'reason': "EMA Bullish Cross"}
            if prev['EMA9'] >= prev['EMA21'] and curr['EMA9'] < curr['EMA21']:
                return {'symbol': symbol, 'direction': 'SELL', 'score': 85, 'reason': "EMA Bearish Cross"}
            
            return None
            
        except Exception:
            return None
    
    def execute(self, opp: dict) -> bool:
        """Execute trade"""
        logger.info(f"TRADING: {opp['symbol']} {opp['direction']} | {opp['reason']}")
        
        info = mt5.symbol_info(opp['symbol'])
        tick = mt5.symbol_info_tick(opp['symbol'])
        
        if not info or not tick:
            return False
        
        # Calculate lot size
        account = mt5.account_info()
        risk_amount = account.equity * (self.risk_percent / 100)
        
        point = info.point
        tick_value = info.trade_tick_value if info.trade_tick_value > 0 else 1.0
        
        # SL based on symbol type
        if any(x in opp['symbol'] for x in ["BTC", "ETH", "XRP"]):
            sl_points = 50000
        elif any(x in opp['symbol'] for x in ["GOLD", "XAU"]):
            sl_points = 5000
        elif any(x in opp['symbol'] for x in ["US5", "US3", "USTEC", "GER"]):
            sl_points = 5000
        else:
            sl_points = 500
        
        lot = risk_amount / (sl_points * tick_value)
        lot = max(info.volume_min, min(info.volume_max, round(lot, 2)))
        
        tp_points = sl_points * 2  # 1:2 RR
        
        if opp['direction'] == 'BUY':
            price = tick.ask
            sl = price - sl_points * point
            tp = price + tp_points * point
            order_type = mt5.ORDER_TYPE_BUY
        else:
            price = tick.bid
            sl = price + sl_points * point
            tp = price - tp_points * point
            order_type = mt5.ORDER_TYPE_SELL
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": opp['symbol'],
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 50,
            "magic": 777777,
            "comment": f"MEGA: {opp['reason'][:15]}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            logger.info(f"EXECUTED: {opp['symbol']} {opp['direction']} {lot} lots @ {result.price}")
            return True
        else:
            logger.warning(f"FAILED: {result.comment}")
            return False


if __name__ == "__main__":
    bot = MegaScanner()
    bot.start()
